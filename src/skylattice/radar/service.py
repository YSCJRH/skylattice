"""Technology radar service for discovery, experimentation, and bounded promotion."""

from __future__ import annotations

import base64
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
import uuid

import yaml

from skylattice.actions import GitAdapter, GitHubAdapter, RepoWorkspaceAdapter
from skylattice.governance import GovernanceDecision, GovernanceGate, GovernanceRequest, PermissionTier
from skylattice.ledger import EventKind, LedgerStore
from skylattice.memory import MemoryLayer, SQLiteMemoryRepository
from skylattice.runtime.models import RunStatus
from skylattice.runtime.repositories import RunRepository

from .config import RadarConfig, load_adoption_records, load_radar_config
from .models import (
    RadarCandidate,
    RadarCandidateStatus,
    RadarDecision,
    RadarEvidence,
    RadarExperiment,
    RadarExperimentStatus,
    RadarPromotion,
    RadarPromotionStatus,
    RadarRun,
    RadarRunStatus,
    RadarState,
    RadarWindow,
)
from .repositories import RadarRepository
from .scoring import RadarScorer
from .source import RadarDiscoverySource, resolve_radar_source


class RadarService:
    def __init__(
        self,
        *,
        repo_root: Path,
        radar_repository: RadarRepository,
        run_repository: RunRepository,
        ledger: LedgerStore,
        memory: SQLiteMemoryRepository,
        governance: GovernanceGate,
        workspace: RepoWorkspaceAdapter,
        git: GitAdapter,
        github: GitHubAdapter | None,
        source: RadarDiscoverySource | None,
        config: RadarConfig,
    ) -> None:
        self.repo_root = repo_root.resolve()
        self.radar_repository = radar_repository
        self.run_repository = run_repository
        self.ledger = ledger
        self.memory = memory
        self.governance = governance
        self.workspace = workspace
        self.git = git
        self.github = github
        self.source = source
        self.config = config

    @classmethod
    def from_repo(
        cls,
        *,
        repo_root: Path,
        radar_repository: RadarRepository,
        run_repository: RunRepository,
        ledger: LedgerStore,
        memory: SQLiteMemoryRepository,
        governance: GovernanceGate,
        workspace: RepoWorkspaceAdapter,
        git: GitAdapter,
        github: GitHubAdapter | None,
        source: RadarDiscoverySource | None = None,
    ) -> "RadarService":
        config = load_radar_config(repo_root)
        actual_source = resolve_radar_source(providers=config.providers, github=github, override=source)
        return cls(
            repo_root=repo_root,
            radar_repository=radar_repository,
            run_repository=run_repository,
            ledger=ledger,
            memory=memory,
            governance=governance,
            workspace=workspace,
            git=git,
            github=github,
            source=actual_source,
            config=config,
        )

    def state_snapshot(self) -> dict[str, object]:
        state = self.radar_repository.get_state()
        latest = self.radar_repository.latest_run()
        return {
            "source_available": self.source is not None,
            "source_provider": self.source.provider if self.source is not None else None,
            "default_provider": self.config.providers.default_provider,
            "enabled_providers": list(self.config.providers.enabled_provider_ids()),
            "freeze_mode": state.freeze_mode,
            "consecutive_failures": state.consecutive_failures,
            "latest_run_id": latest.run_id if latest is not None else None,
            "default_schedule": self.config.schedule.default_schedule,
        }

    def show_schedule(self, schedule_id: str | None = None) -> dict[str, object]:
        selected = self.config.schedule.get(schedule_id)
        return {
            "default_schedule": self.config.schedule.default_schedule,
            "selected_schedule": selected.schedule_id,
            "schedules": {
                key: self._serialize_schedule(item)
                for key, item in sorted(self.config.schedule.schedules.items())
            },
        }

    def render_schedule(self, *, target: str, schedule_id: str | None = None) -> dict[str, object]:
        if target != "windows-task":
            raise RuntimeError(f"Unsupported radar schedule render target: {target}")
        schedule = self.config.schedule.get(schedule_id)
        repo_root = str(self.repo_root)
        escaped_repo_root = repo_root.replace("'", "''")
        action_script = f"Set-Location -LiteralPath '{escaped_repo_root}'; {schedule.target_command}"
        encoded_command = base64.b64encode(action_script.encode("utf-16le")).decode("ascii")
        action_execute = "powershell.exe"
        action_arguments = f"-NoProfile -ExecutionPolicy Bypass -EncodedCommand {encoded_command}"
        trigger_command = schedule.windows_task.trigger_command
        register_command = (
            "Register-ScheduledTask "
            f"-TaskName \"Skylattice Radar {schedule.schedule_id}\" "
            f"-TaskPath \"{schedule.windows_task.folder}\" "
            "-Action (New-ScheduledTaskAction "
            f"-Execute \"{action_execute}\" -Argument \"{action_arguments}\") "
        )
        if trigger_command:
            register_command += f"-Trigger ({trigger_command}) "
        register_command += f"-Description \"{schedule.windows_task.description}\""
        return {
            "target": target,
            "schedule": self._serialize_schedule(schedule),
            "working_directory": repo_root,
            "command": schedule.target_command,
            "windows_task": {
                "task_name": f"Skylattice Radar {schedule.schedule_id}",
                "folder": schedule.windows_task.folder,
                "description": schedule.windows_task.description,
                "schedule_expression": schedule.windows_task.schedule_expression,
                "trigger_command": trigger_command,
                "registration_mode": "scheduled" if trigger_command else "on-demand",
                "action": {
                    "execute": action_execute,
                    "arguments": action_arguments,
                    "script": action_script,
                    "working_directory": repo_root,
                },
                "register_command": register_command,
                "inspect_command": (
                    "Get-ScheduledTask "
                    f"-TaskName \"Skylattice Radar {schedule.schedule_id}\" "
                    f"-TaskPath \"{schedule.windows_task.folder}\""
                ),
                "run_now_command": (
                    "Start-ScheduledTask "
                    f"-TaskName \"Skylattice Radar {schedule.schedule_id}\" "
                    f"-TaskPath \"{schedule.windows_task.folder}\""
                ),
                "unregister_command": (
                    "Unregister-ScheduledTask "
                    f"-TaskName \"Skylattice Radar {schedule.schedule_id}\" "
                    f"-TaskPath \"{schedule.windows_task.folder}\" "
                    "-Confirm:$false"
                ),
            },
        }

    def run_schedule(self, schedule_id: str | None = None) -> RadarRun:
        schedule = self.config.schedule.get(schedule_id)
        if not schedule.enabled:
            raise RuntimeError(f"Radar schedule {schedule.schedule_id} is disabled.")
        return self.scan(window=schedule.window, limit=schedule.limit)

    def scan(self, *, window: str = "manual", limit: int | None = None) -> RadarRun:
        if self.source is None:
            raise RuntimeError("Radar discovery is not configured. Set GITHUB_TOKEN to enable GitHub search.")
        state = self.radar_repository.get_state()
        if state.freeze_mode or self.governance.freeze_mode_enabled:
            raise RuntimeError("Technology radar is frozen. Resolve failures or disable freeze mode before scanning.")
        read_check = self.governance.evaluate(
            GovernanceRequest(tier=PermissionTier.EXTERNAL_READ, summary="Scan GitHub repositories for technology radar")
        )
        if read_check.decision is GovernanceDecision.DENIED:
            raise RuntimeError(read_check.reason)
        self._ensure_clean_base_branch()

        radar_window = RadarWindow(window)
        window_config = self.config.sources.weekly if radar_window is RadarWindow.WEEKLY else self.config.sources.manual
        effective_limit = min(limit or window_config.candidate_limit, window_config.candidate_limit)
        run_id = f"radar-{uuid.uuid4().hex}"
        generic_goal = f"Technology radar {radar_window.value} scan"
        self._create_shadow_run(run_id=run_id, goal=generic_goal)
        self.radar_repository.create_run(
            RadarRun(run_id=run_id, window=radar_window, status=RadarRunStatus.CREATED, limit=effective_limit)
        )
        self.ledger.append(
            run_id=run_id,
            kind=EventKind.RUN,
            summary="Radar run created",
            actor="radar",
            payload={"window": radar_window.value, "limit": effective_limit},
        )
        self.memory.create(
            layer=MemoryLayer.WORKING,
            summary=f"Radar scan in progress: {radar_window.value}",
            run_id=run_id,
            source_refs=[radar_window.value],
            metadata={"origin": "radar", "phase": "active"},
        )

        self._update_run_status(run_id, RadarRunStatus.SCANNING, summary="Scanning GitHub for fresh candidates")
        candidates, evidence = self.source.discover(
            run_id=run_id,
            topics=self.config.sources.topics,
            created_days=window_config.created_days,
            active_days=window_config.active_days,
            limit=effective_limit,
        )
        self.radar_repository.create_candidates(candidates)
        self.radar_repository.add_evidence(evidence)
        self.ledger.append(
            run_id=run_id,
            kind=EventKind.ACTION,
            summary="GitHub discovery completed",
            actor="radar",
            payload={"candidate_count": len(candidates)},
        )

        self._update_run_status(run_id, RadarRunStatus.ANALYZING, summary="Scoring and enriching shortlisted candidates")
        scored = self._score_candidates(
            run_id=run_id,
            candidates=self.radar_repository.list_candidates(run_id),
            active_days=window_config.active_days,
            created_days=window_config.created_days,
        )
        shortlist = scored[: self.config.sources.deep_analysis_limit]
        experiments = shortlist[: self.config.sources.experiment_limit]
        promotions: list[RadarPromotion] = []

        for candidate in shortlist:
            self._record_candidate_memories(run_id, candidate)

        self._update_run_status(run_id, RadarRunStatus.EXPERIMENTING, summary="Running repo-contained radar experiments")
        for candidate in experiments:
            experiment = self._run_experiment(candidate)
            if experiment.status is not RadarExperimentStatus.VERIFIED:
                continue
            if len(promotions) >= self.config.sources.promotion_limit:
                continue
            if candidate.decision is RadarDecision.REJECT:
                continue
            promotion = self._maybe_promote(candidate, experiment)
            if promotion is not None:
                promotions.append(promotion)
                break

        self._finalize_run(run_id=run_id, candidates=scored, promotions=promotions)
        return self.radar_repository.get_run(run_id)

    def get_run(self, run_id: str) -> RadarRun:
        return self.radar_repository.get_run(run_id)

    def inspect_run(self, run_id: str) -> dict[str, object]:
        run = self.radar_repository.get_run(run_id)
        return {
            "run": self._serialize_run(run),
            "candidates": [self._serialize_candidate(item) for item in self.radar_repository.list_candidates(run_id)],
            "experiments": [self._serialize_experiment(item) for item in self.radar_repository.list_experiments(run_id)],
            "promotions": [self._serialize_promotion(item) for item in self.radar_repository.list_promotions(run_id)],
            "events": [self._serialize_event(item) for item in self.ledger.list_for_run(run_id)],
            "memory": [self._serialize_memory(item) for item in self.memory.list_for_run(run_id)],
            "evidence": [self._serialize_evidence(item) for item in self.radar_repository.list_evidence(run_id=run_id)],
        }

    def inspect_target(self, identifier: str) -> dict[str, object]:
        try:
            return self.inspect_run(identifier)
        except KeyError:
            candidate = self.radar_repository.get_candidate(identifier)
            experiments = [
                item for item in self.radar_repository.list_experiments(candidate.run_id) if item.candidate_id == candidate.candidate_id
            ]
            promotions = [
                item for item in self.radar_repository.list_promotions(candidate.run_id) if item.candidate_id == candidate.candidate_id
            ]
            return {
                "candidate": self._serialize_candidate(candidate),
                "run": self._serialize_run(self.radar_repository.get_run(candidate.run_id)),
                "experiments": [self._serialize_experiment(item) for item in experiments],
                "promotions": [self._serialize_promotion(item) for item in promotions],
                "evidence": [self._serialize_evidence(item) for item in self.radar_repository.list_evidence(candidate_id=candidate.candidate_id)],
            }

    def replay_candidate(self, candidate_id: str) -> RadarRun:
        original = self.radar_repository.get_candidate(candidate_id)
        self._ensure_clean_base_branch()
        run_id = f"radar-{uuid.uuid4().hex}"
        self._create_shadow_run(run_id=run_id, goal=f"Replay radar candidate {original.identity_handle}")
        self.radar_repository.create_run(
            RadarRun(
                run_id=run_id,
                window=RadarWindow.MANUAL,
                status=RadarRunStatus.CREATED,
                limit=1,
                summary=f"Replay {original.identity_handle}",
            )
        )
        replayed = replace(
            original,
            candidate_id=f"cand-{uuid.uuid4().hex}",
            run_id=run_id,
            status=RadarCandidateStatus.REPLAYED,
            reason=f"replayed from {original.candidate_id}",
            metadata={**original.metadata, "replay_of": original.candidate_id},
        )
        self.radar_repository.create_candidates([replayed])
        self.ledger.append(
            run_id=run_id,
            kind=EventKind.RUN,
            summary="Radar candidate replay created",
            actor="radar",
            payload={
                "source_candidate": original.candidate_id,
                "repo_slug": original.repo_slug,
                "source_handle": original.identity_handle,
            },
        )
        self._record_candidate_memories(run_id, replayed)
        self._update_run_status(run_id, RadarRunStatus.EXPERIMENTING, summary=f"Replaying candidate {original.identity_handle}")
        experiment = self._run_experiment(replayed)
        promotions: list[RadarPromotion] = []
        if experiment.status is RadarExperimentStatus.VERIFIED:
            promotion = self._maybe_promote(replayed, experiment)
            if promotion is not None:
                promotions.append(promotion)
        self._finalize_run(
            run_id=run_id,
            candidates=[self.radar_repository.get_candidate(replayed.candidate_id)],
            promotions=promotions,
        )
        return self.radar_repository.get_run(run_id)

    def rollback_promotion(self, promotion_id: str) -> RadarPromotion:
        promotion = self.radar_repository.get_promotion(promotion_id)
        if not promotion.main_commit:
            raise RuntimeError("Promotion does not have a main commit to roll back")
        self._ensure_clean_base_branch()
        self.git.checkout(self.config.promotion.base_branch)
        self.git.revert(promotion.main_commit)
        experiment_main_commit = str(promotion.metadata.get("experiment_main_commit", ""))
        if experiment_main_commit:
            self.git.revert(experiment_main_commit)
        self.git.push(self.config.promotion.base_branch)
        updated = self.radar_repository.update_promotion(
            replace(
                promotion,
                status=RadarPromotionStatus.ROLLED_BACK,
                metadata={**promotion.metadata, "rolled_back_at": datetime.now(UTC).isoformat()},
            )
        )
        self.ledger.append(
            run_id=promotion.run_id,
            kind=EventKind.EVOLUTION,
            summary="Radar promotion rolled back",
            actor="radar",
            payload={
                "promotion_id": promotion_id,
                "main_commit": promotion.main_commit,
                "experiment_main_commit": experiment_main_commit,
            },
        )
        refs = [promotion.main_commit]
        if experiment_main_commit:
            refs.append(experiment_main_commit)
        self.memory.create(
            layer=MemoryLayer.EPISODIC,
            summary=f"Rolled back radar promotion {promotion_id}",
            run_id=promotion.run_id,
            source_refs=refs,
            metadata={"origin": "radar", "promotion_id": promotion_id},
        )
        return updated

    def latest_digest(self) -> dict[str, object]:
        return self.radar_repository.latest_digest()

    def _score_candidates(
        self,
        *,
        run_id: str,
        candidates: list[RadarCandidate],
        active_days: int,
        created_days: int,
    ) -> list[RadarCandidate]:
        scorer = RadarScorer(self.config.scoring, adoption_records=load_adoption_records(self.repo_root))
        scored: list[RadarCandidate] = []
        for candidate in candidates:
            enriched, evidence = self.source.enrich_candidate(candidate) if self.source is not None else (candidate, [])
            self.radar_repository.add_evidence(evidence)
            score = scorer.score(enriched, active_days=active_days, created_days=created_days)
            status = RadarCandidateStatus.SHORTLISTED if score.decision is not RadarDecision.REJECT else RadarCandidateStatus.REJECTED
            updated = replace(
                enriched,
                score=score.total,
                score_breakdown=score.breakdown,
                decision=score.decision,
                status=status,
                reason=score.reason,
            )
            self.radar_repository.update_candidate(updated)
            self.ledger.append(
                run_id=run_id,
                kind=EventKind.EVALUATION,
                summary=f"Scored radar candidate {updated.identity_handle}",
                actor="radar",
                payload={"score": updated.score, "decision": updated.decision.value},
            )
            scored.append(updated)
        return sorted(scored, key=lambda item: item.score, reverse=True)

    def _run_experiment(self, candidate: RadarCandidate) -> RadarExperiment:
        allowed = self._check_paths(
            tier=PermissionTier.RADAR_EXPERIMENT_WRITE,
            paths=(self._experiment_path(candidate),),
            summary=f"Run radar experiment for {candidate.identity_handle}",
        )
        if allowed.decision is GovernanceDecision.DENIED:
            raise RuntimeError(allowed.reason)

        branch_name = self._experiment_branch(candidate)
        validation_command = self.config.promotion.validation_commands[0]
        source_commit = self.git.current_commit()
        experiment = self.radar_repository.create_experiment(
            RadarExperiment(
                experiment_id=f"exp-{uuid.uuid4().hex}",
                run_id=candidate.run_id,
                candidate_id=candidate.candidate_id,
                branch_name=branch_name,
                hypothesis=self._build_hypothesis(candidate),
                artifact_path=self._experiment_path(candidate),
                validation_command=validation_command,
                status=RadarExperimentStatus.RUNNING,
                source_commit=source_commit,
                notes={"repo_slug": candidate.repo_slug, "source_handle": candidate.identity_handle},
            )
        )
        self.git.checkout(self.config.promotion.base_branch)
        self.git.create_branch(branch_name)
        validation = self.workspace.run_check(validation_command)
        passed = int(validation.get("returncode", 1)) == 0
        recommended = passed and candidate.decision in {RadarDecision.EXPERIMENT, RadarDecision.PROMOTE}
        content = self._render_experiment_artifact(candidate, experiment, validation, recommended)
        self.workspace.write_text(experiment.artifact_path, content, create_if_missing=True)
        self.git.add_all()
        self.git.commit(f"radar: experiment {candidate.identity_handle}")
        experiment_commit = self.git.current_commit()
        self.git.checkout(self.config.promotion.base_branch)
        updated = self.radar_repository.update_experiment(
            replace(
                experiment,
                status=RadarExperimentStatus.VERIFIED if passed else RadarExperimentStatus.FAILED,
                recommended=recommended,
                experiment_commit=experiment_commit,
                notes={**experiment.notes, "validation": validation, "recommended": recommended},
            )
        )
        candidate_status = RadarCandidateStatus.EXPERIMENTED if passed else RadarCandidateStatus.REJECTED
        self.radar_repository.update_candidate(replace(candidate, status=candidate_status))
        self.ledger.append(
            run_id=candidate.run_id,
            kind=EventKind.ACTION,
            summary=f"Radar experiment executed for {candidate.identity_handle}",
            actor="radar",
            payload={"branch_name": branch_name, "validation_passed": passed},
            artifact_refs=[experiment.artifact_path],
        )
        return updated

    def _maybe_promote(self, candidate: RadarCandidate, experiment: RadarExperiment) -> RadarPromotion | None:
        if experiment.experiment_commit is None:
            return None
        state = self.radar_repository.get_state()
        if state.freeze_mode:
            self._update_run_status(candidate.run_id, RadarRunStatus.FROZEN, summary="Radar froze before promotion")
            return None

        cutoff = (datetime.now(UTC) - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        promotions_this_week = self.radar_repository.count_promotions_since(cutoff)
        if promotions_this_week >= min(self.config.sources.promotion_limit, self.config.promotion.weekly_promotion_cap):
            return None
        if candidate.score < self.config.scoring.thresholds.get("promote", 0.72):
            return None

        promotion_paths = (
            experiment.artifact_path,
            self.config.promotion.adoption_registry,
            self._promotion_log_path(candidate),
        )
        allowed = self._check_paths(
            tier=PermissionTier.RADAR_PROMOTE_MAIN,
            paths=promotion_paths,
            summary=f"Promote radar candidate {candidate.identity_handle} to main",
        )
        if allowed.decision is GovernanceDecision.DENIED:
            raise RuntimeError(allowed.reason)

        self._update_run_status(candidate.run_id, RadarRunStatus.PROMOTING, summary=f"Promoting {candidate.identity_handle} to main")
        promotion = self.radar_repository.create_promotion(
            RadarPromotion(
                promotion_id=f"promo-{uuid.uuid4().hex}",
                run_id=candidate.run_id,
                candidate_id=candidate.candidate_id,
                experiment_id=experiment.experiment_id,
                status=RadarPromotionStatus.PENDING,
                source_branch=experiment.branch_name,
                base_commit=experiment.source_commit or "",
                experiment_commit=experiment.experiment_commit,
                rollback_target=experiment.source_commit,
                metadata={"candidate_score": candidate.score},
            )
        )
        try:
            self.git.checkout(self.config.promotion.base_branch)
            self.git.cherry_pick(experiment.experiment_commit)
            experiment_main_commit = self.git.current_commit()
            self._update_adoption_registry(candidate, promotion)
            self.workspace.write_text(
                self._promotion_log_path(candidate),
                self._render_promotion_log(candidate, experiment, promotion),
                create_if_missing=True,
            )
            validation_command = self.config.promotion.validation_commands[0]
            validation = self.workspace.run_check(validation_command)
            if int(validation.get("returncode", 1)) != 0:
                raise RuntimeError(f"Promotion validation failed: {validation_command}")
            self.git.add_all()
            self.git.commit(f"radar: promote {candidate.identity_handle}")
            main_commit = self.git.current_commit()
            self.git.push(self.config.promotion.base_branch)
        except Exception as exc:  # noqa: BLE001
            self._record_promotion_failure(candidate.run_id)
            self.radar_repository.update_promotion(
                replace(
                    promotion,
                    status=RadarPromotionStatus.FAILED,
                    metadata={**promotion.metadata, "error": str(exc)},
                )
            )
            self.ledger.append(
                run_id=candidate.run_id,
                kind=EventKind.EVOLUTION,
                summary=f"Radar promotion failed for {candidate.identity_handle}",
                actor="radar",
                payload={"error": str(exc), "promotion_id": promotion.promotion_id},
                reversible=False,
            )
            raise RuntimeError(str(exc)) from exc

        self._reset_failure_state()
        promoted = self.radar_repository.update_promotion(
            replace(
                promotion,
                status=RadarPromotionStatus.PROMOTED,
                main_commit=main_commit,
                pushed=True,
                metadata={
                    **promotion.metadata,
                    "promoted_at": datetime.now(UTC).isoformat(),
                    "experiment_main_commit": experiment_main_commit,
                },
            )
        )
        self.radar_repository.update_candidate(replace(candidate, status=RadarCandidateStatus.PROMOTED))
        self.memory.create(
            layer=MemoryLayer.PROCEDURAL,
            summary=f"Adopted radar pattern from {candidate.identity_handle} into tracked behavior registry.",
            run_id=candidate.run_id,
            source_refs=[promoted.promotion_id, self.config.promotion.adoption_registry],
            metadata={
                "workflow": "radar-adoption-registry",
                "canonical": False,
                "origin": "radar",
                "repo_slug": candidate.repo_slug,
                "source_handle": candidate.identity_handle,
                "source_url": candidate.identity_url,
                "topic_tags": list(candidate.topics),
                "confidence": candidate.score,
                "evidence_refs": [candidate.identity_url],
            },
            confidence=max(candidate.score, 0.5),
        )
        self.ledger.append(
            run_id=candidate.run_id,
            kind=EventKind.EVOLUTION,
            summary=f"Radar candidate promoted: {candidate.identity_handle}",
            actor="radar",
            payload={
                "promotion_id": promoted.promotion_id,
                "main_commit": promoted.main_commit,
                "rollback_target": promoted.rollback_target,
            },
            artifact_refs=[self._promotion_log_path(candidate), self.config.promotion.adoption_registry],
        )
        return promoted

    def _finalize_run(self, *, run_id: str, candidates: list[RadarCandidate], promotions: list[RadarPromotion]) -> None:
        for record in self.memory.list_for_run(run_id):
            if record.layer is MemoryLayer.WORKING and record.status.value == "active":
                self.memory.rollback(record.record_id)
        digest = {
            "run_id": run_id,
            "candidate_count": len(candidates),
            "top_candidates": [
                {
                    "candidate_id": candidate.candidate_id,
                    "repo_slug": candidate.repo_slug,
                    "source_handle": candidate.identity_handle,
                    "score": candidate.score,
                    "decision": candidate.decision.value,
                }
                for candidate in candidates[:5]
            ],
            "promotions": [promotion.promotion_id for promotion in promotions],
        }
        self.radar_repository.update_run(
            run_id,
            status=RadarRunStatus.COMPLETED,
            summary="Radar run completed",
            digest=digest,
            result={"promoted": len(promotions), "candidate_count": len(candidates)},
        )
        self.run_repository.set_result(run_id, {"radar_digest": digest})
        self.run_repository.update_status(run_id, RunStatus.COMPLETED)
        self.memory.create(
            layer=MemoryLayer.EPISODIC,
            summary=f"Radar run completed with {len(candidates)} candidates and {len(promotions)} promotions.",
            run_id=run_id,
            source_refs=[item.identity_handle for item in candidates[:3]],
            metadata={"origin": "radar", "promoted": [item.promotion_id for item in promotions]},
        )
        self.ledger.append(
            run_id=run_id,
            kind=EventKind.MEMORY,
            summary="Radar episodic memory recorded",
            actor="radar",
            payload={"run_id": run_id},
        )

    def _record_candidate_memories(self, run_id: str, candidate: RadarCandidate) -> None:
        self.memory.create(
            layer=MemoryLayer.SEMANTIC,
            summary=f"Radar candidate {candidate.identity_handle} suggests reusable patterns in {', '.join(candidate.topics[:4]) or 'general agent tooling'}.",
            run_id=run_id,
            source_refs=[candidate.identity_url],
            metadata={
                "origin": "radar",
                "repo_slug": candidate.repo_slug,
                "source_provider": candidate.source_provider,
                "source_kind": candidate.source_kind,
                "source_handle": candidate.identity_handle,
                "source_url": candidate.identity_url,
                "topic_tags": list(candidate.topics),
                "confidence": candidate.score,
                "evidence_refs": [candidate.identity_url],
            },
            confidence=max(candidate.score, 0.35),
        )

    def _create_shadow_run(self, *, run_id: str, goal: str) -> None:
        self.run_repository.create_run(
            run_id=run_id,
            goal=goal,
            goal_source="radar",
            runtime_snapshot={"service": "radar", "repo_root": str(self.repo_root)},
            status=RunStatus.CREATED,
        )

    def _update_run_status(self, run_id: str, status: RadarRunStatus, *, summary: str | None = None) -> None:
        self.radar_repository.update_run(run_id, status=status, summary=summary)
        self.run_repository.update_status(run_id, self._shadow_status(status))

    @staticmethod
    def _shadow_status(status: RadarRunStatus) -> RunStatus:
        if status in {RadarRunStatus.CREATED}:
            return RunStatus.CREATED
        if status in {RadarRunStatus.SCANNING, RadarRunStatus.ANALYZING, RadarRunStatus.EXPERIMENTING, RadarRunStatus.PROMOTING}:
            return RunStatus.RUNNING
        if status is RadarRunStatus.COMPLETED:
            return RunStatus.COMPLETED
        if status is RadarRunStatus.FAILED:
            return RunStatus.FAILED
        return RunStatus.HALTED

    def _check_paths(self, *, tier: PermissionTier, paths: tuple[str, ...], summary: str):
        outcome = self.governance.evaluate(
            GovernanceRequest(tier=tier, summary=summary, target_path=paths[0] if paths else None)
        )
        if outcome.decision is GovernanceDecision.DENIED:
            return outcome
        if not self.governance.paths_within_roots(paths, self.config.promotion.allowed_paths):
            from skylattice.governance import GovernanceOutcome

            return GovernanceOutcome(GovernanceDecision.DENIED, "radar writes are outside the promotion allowlist")
        return outcome

    def _ensure_clean_base_branch(self) -> None:
        current_branch = self.git.current_branch()
        if current_branch != self.config.promotion.base_branch:
            raise RuntimeError(
                f"Technology radar must start from {self.config.promotion.base_branch}, current branch is {current_branch}"
            )
        if self.git.status_porcelain().strip():
            raise RuntimeError("Technology radar requires a clean worktree before scanning or promotion")

    def _record_promotion_failure(self, run_id: str) -> RadarState:
        state = self.radar_repository.get_state()
        failures = state.consecutive_failures + 1
        freeze = failures >= self.config.promotion.freeze_after_failures
        updated = self.radar_repository.set_state(
            freeze_mode=freeze,
            consecutive_failures=failures,
            last_failure_at=datetime.now(UTC).isoformat(),
        )
        self.radar_repository.update_run(
            run_id,
            status=RadarRunStatus.FROZEN if freeze else RadarRunStatus.FAILED,
            summary="Radar promotion failure recorded",
        )
        self.run_repository.update_status(run_id, RunStatus.HALTED if freeze else RunStatus.FAILED)
        return updated

    def _reset_failure_state(self) -> None:
        self.radar_repository.set_state(freeze_mode=False, consecutive_failures=0, last_failure_at="")

    def _experiment_branch(self, candidate: RadarCandidate) -> str:
        slug = candidate.repo_name.lower().replace("_", "-")
        slug = "-".join(part for part in slug.split("-") if part) or "candidate"
        return f"codex/radar-{slug[:24]}-{candidate.run_id[-6:]}"

    def _experiment_path(self, candidate: RadarCandidate) -> str:
        return f"{self.config.promotion.experiment_dir}/{candidate.repo_name.lower()}-{candidate.run_id[-6:]}.md"

    def _promotion_log_path(self, candidate: RadarCandidate) -> str:
        return f"{self.config.promotion.promotion_log_dir}/{candidate.repo_name.lower()}-{candidate.run_id[-6:]}.md"

    def _build_hypothesis(self, candidate: RadarCandidate) -> str:
        topics = ", ".join(candidate.topics[:4]) or "general agent systems"
        return f"Adopting patterns from {candidate.identity_handle} may strengthen Skylattice around {topics}."

    def _render_experiment_artifact(
        self,
        candidate: RadarCandidate,
        experiment: RadarExperiment,
        validation: dict[str, object],
        recommended: bool,
    ) -> str:
        stdout = str(validation.get("stdout", "")).strip()
        stderr = str(validation.get("stderr", "")).strip()
        return "\n".join(
            [
                f"# Radar Experiment: {candidate.identity_handle}",
                "",
                f"- Run ID: `{candidate.run_id}`",
                f"- Candidate ID: `{candidate.candidate_id}`",
                f"- Branch: `{experiment.branch_name}`",
                f"- Score: `{candidate.score:.4f}`",
                f"- Source: {candidate.identity_url}",
                "",
                "## Hypothesis",
                experiment.hypothesis,
                "",
                "## Minimal Implementation",
                "- Capture semantic memory for the candidate",
                "- Register the candidate as a bounded experiment in the repo",
                "- Validate the current repo after the spike",
                "",
                "## Validation Result",
                f"- Command: `{experiment.validation_command}`",
                f"- Return code: `{validation.get('returncode', 1)}`",
                f"- Recommended for promotion: `{str(recommended).lower()}`",
                "",
                "## Validation Output",
                "```text",
                stdout or stderr or "(no output)",
                "```",
                "",
                "## Recommendation",
                "Promote to main" if recommended else "Keep as observed experiment only",
                "",
                "## Evidence",
                f"- Topics: {', '.join(candidate.topics) or 'n/a'}",
                f"- Stars: {candidate.stars}",
                f"- Last push: {candidate.pushed_at_remote or 'unknown'}",
                f"- Latest release: {candidate.latest_release_at or 'unknown'}",
                "",
            ]
        )

    def _update_adoption_registry(self, candidate: RadarCandidate, promotion: RadarPromotion) -> None:
        registry_path = self.repo_root / self.config.promotion.adoption_registry
        data = yaml.safe_load(registry_path.read_text(encoding="utf-8")) if registry_path.exists() else {}
        if not isinstance(data, dict):
            data = {}
        patterns = data.setdefault("adopted_patterns", [])
        if not isinstance(patterns, list):
            patterns = []
            data["adopted_patterns"] = patterns
        patterns.append(
            {
                "repo_slug": candidate.repo_slug,
                "source_handle": candidate.identity_handle,
                "candidate_id": candidate.candidate_id,
                "promotion_id": promotion.promotion_id,
                "score": round(candidate.score, 4),
                "tags": list(candidate.topics),
                "preference_boost": round(min(max(candidate.score / 4, 0.03), 0.12), 4),
                "rationale": candidate.reason,
                "promoted_at": datetime.now(UTC).isoformat(),
            }
        )
        content = yaml.safe_dump(data, sort_keys=False, allow_unicode=False)
        self.workspace.write_text(self.config.promotion.adoption_registry, content, create_if_missing=True)

    def _render_promotion_log(self, candidate: RadarCandidate, experiment: RadarExperiment, promotion: RadarPromotion) -> str:
        return "\n".join(
            [
                f"# Radar Promotion: {candidate.identity_handle}",
                "",
                f"- Promotion ID: `{promotion.promotion_id}`",
                f"- Run ID: `{candidate.run_id}`",
                f"- Source branch: `{experiment.branch_name}`",
                f"- Base commit: `{promotion.base_commit}`",
                f"- Experiment commit: `{promotion.experiment_commit}`",
                f"- Rollback target: `{promotion.rollback_target or ''}`",
                f"- Adoption registry: `{self.config.promotion.adoption_registry}`",
                "",
                "## Why This Changed Skylattice",
                candidate.reason,
                "",
                "## Behavior Change",
                "Future radar scans will boost repositories that match the adopted topic tags in the registry.",
                "",
                "## Evidence",
                f"- Source: {candidate.identity_url}",
                f"- Topics: {', '.join(candidate.topics) or 'n/a'}",
                f"- Score: {candidate.score:.4f}",
                "",
            ]
        )

    @staticmethod
    def _serialize_run(run: RadarRun) -> dict[str, object]:
        return {
            "run_id": run.run_id,
            "window": run.window.value,
            "status": run.status.value,
            "limit": run.limit,
            "summary": run.summary,
            "digest": run.digest,
            "result": run.result,
            "error": run.error,
            "created_at": run.created_at,
            "updated_at": run.updated_at,
        }

    @staticmethod
    def _serialize_candidate(candidate: RadarCandidate) -> dict[str, object]:
        return {
            "candidate_id": candidate.candidate_id,
            "run_id": candidate.run_id,
            "repo_slug": candidate.repo_slug,
            "repo_name": candidate.repo_name,
            "html_url": candidate.html_url,
            "source_provider": candidate.source_provider,
            "source_kind": candidate.source_kind,
            "source_handle": candidate.identity_handle,
            "source_url": candidate.identity_url,
            "display_name": candidate.identity_name,
            "identity": {
                "provider": candidate.source_provider,
                "kind": candidate.source_kind,
                "handle": candidate.identity_handle,
                "url": candidate.identity_url,
                "display_name": candidate.identity_name,
            },
            "description": candidate.description,
            "topics": list(candidate.topics),
            "stars": candidate.stars,
            "forks": candidate.forks,
            "watchers": candidate.watchers,
            "created_at_remote": candidate.created_at_remote,
            "pushed_at_remote": candidate.pushed_at_remote,
            "latest_release_at": candidate.latest_release_at,
            "score": candidate.score,
            "score_breakdown": candidate.score_breakdown,
            "decision": candidate.decision.value,
            "status": candidate.status.value,
            "reason": candidate.reason,
            "metadata": candidate.metadata,
        }

    @staticmethod
    def _serialize_experiment(experiment: RadarExperiment) -> dict[str, object]:
        return {
            "experiment_id": experiment.experiment_id,
            "run_id": experiment.run_id,
            "candidate_id": experiment.candidate_id,
            "branch_name": experiment.branch_name,
            "hypothesis": experiment.hypothesis,
            "artifact_path": experiment.artifact_path,
            "validation_command": experiment.validation_command,
            "status": experiment.status.value,
            "recommended": experiment.recommended,
            "source_commit": experiment.source_commit,
            "experiment_commit": experiment.experiment_commit,
            "notes": experiment.notes,
        }

    @staticmethod
    def _serialize_promotion(promotion: RadarPromotion) -> dict[str, object]:
        return {
            "promotion_id": promotion.promotion_id,
            "run_id": promotion.run_id,
            "candidate_id": promotion.candidate_id,
            "experiment_id": promotion.experiment_id,
            "status": promotion.status.value,
            "source_branch": promotion.source_branch,
            "base_commit": promotion.base_commit,
            "experiment_commit": promotion.experiment_commit,
            "main_commit": promotion.main_commit,
            "rollback_target": promotion.rollback_target,
            "pushed": promotion.pushed,
            "metadata": promotion.metadata,
        }

    @staticmethod
    def _serialize_evidence(item: Any) -> dict[str, object]:
        return {
            "evidence_id": item.evidence_id,
            "run_id": item.run_id,
            "candidate_id": item.candidate_id,
            "provider": item.provider,
            "provider_object_type": item.provider_object_type,
            "provider_object_id": item.provider_object_id,
            "provider_url": item.provider_url,
            "evidence_kind": item.evidence_kind,
            "source": item.source,
            "summary": item.summary,
            "payload": item.payload,
            "created_at": item.created_at,
        }

    @staticmethod
    def _serialize_schedule(schedule: Any) -> dict[str, object]:
        return {
            "schedule_id": schedule.schedule_id,
            "enabled": schedule.enabled,
            "window": schedule.window,
            "limit": schedule.limit,
            "target_command": schedule.target_command,
            "windows_task": {
                "folder": schedule.windows_task.folder,
                "description": schedule.windows_task.description,
                "schedule_expression": schedule.windows_task.schedule_expression,
                "trigger_command": schedule.windows_task.trigger_command,
            },
        }

    @staticmethod
    def _serialize_event(event: Any) -> dict[str, object]:
        return {
            "event_id": event.event_id,
            "kind": event.kind.value,
            "summary": event.summary,
            "actor": event.actor,
            "artifact_refs": list(event.artifact_refs),
            "payload": event.payload,
            "created_at": event.created_at,
        }

    @staticmethod
    def _serialize_memory(record: Any) -> dict[str, object]:
        return {
            "record_id": record.record_id,
            "layer": record.layer.value,
            "summary": record.summary,
            "source_refs": list(record.source_refs),
            "confidence": record.confidence,
            "status": record.status.value,
            "metadata": record.metadata,
            "run_id": record.run_id,
            "supersedes": record.supersedes,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        }



