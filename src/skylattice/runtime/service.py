"""Executable task-agent runtime service."""

from __future__ import annotations

import os
import re
import uuid
import json
from datetime import UTC, datetime
from dataclasses import asdict
from pathlib import Path
from typing import Any

from skylattice.actions import GitAdapter, GitHubAdapter, RepoWorkspaceAdapter
from skylattice.governance import GovernanceDecision, GovernanceGate, GovernanceRequest, PermissionTier
from skylattice.kernel import build_kernel_summary, load_kernel_config
from skylattice.ledger import EventKind, LedgerStore
from skylattice.memory.interfaces import MemoryLayer, RecordStatus, RetrievalRequest, RetrievalSort
from skylattice.memory.repository import SQLiteMemoryRepository
from skylattice.planning import TaskPlanner
from skylattice.providers import OpenAIProvider
from skylattice.radar import GitHubRadarSource, RadarDiscoverySource, RadarRepository, RadarService
from skylattice.runtime.models import RunStatus, RunStep, RunStepStatus, TaskRun

from .db import RuntimeDatabase
from .models import ApprovalGrant
from .repositories import RunRepository
from .task_config import TaskValidationPolicy, load_task_validation_policy


class TaskAgentService:
    MEMORY_CONTEXT_LIMIT = 3
    SUPPORTED_EDIT_MODES = (
        "rewrite",
        "replace_text",
        "insert_after",
        "append_text",
        "create_file",
        "copy_file",
        "move_file",
        "delete_file",
    )

    def __init__(
        self,
        *,
        repo_root: Path,
        database: RuntimeDatabase,
        run_repository: RunRepository,
        ledger: LedgerStore,
        memory: SQLiteMemoryRepository,
        governance: GovernanceGate,
        workspace: RepoWorkspaceAdapter,
        git: GitAdapter,
        task_validation_policy: TaskValidationPolicy,
        planner: TaskPlanner | None,
        provider: object | None,
        github: GitHubAdapter | None,
        radar_service: RadarService,
    ) -> None:
        self.repo_root = repo_root.resolve()
        self.database = database
        self.run_repository = run_repository
        self.ledger = ledger
        self.memory = memory
        self.governance = governance
        self.workspace = workspace
        self.git = git
        self.task_validation_policy = task_validation_policy
        self.planner = planner
        self.provider = provider
        self.github = github
        self.radar = radar_service

    @classmethod
    def from_repo(
        cls,
        *,
        repo_root: Path | None = None,
        provider: object | None = None,
        github_adapter: GitHubAdapter | None = None,
        radar_source: RadarDiscoverySource | None = None,
        db_path: Path | None = None,
    ) -> "TaskAgentService":
        root = (repo_root or Path(__file__).resolve().parents[3]).resolve()
        database = RuntimeDatabase(repo_root=root, db_path=db_path)
        kernel = load_kernel_config(root)

        actual_provider = provider
        if actual_provider is None and os.environ.get("OPENAI_API_KEY"):
            actual_provider = OpenAIProvider()

        planner = TaskPlanner(actual_provider) if actual_provider is not None else None

        actual_github = github_adapter
        repo_hint = os.environ.get("SKYLATTICE_GITHUB_REPOSITORY") or kernel.runtime.remote_ledger
        if actual_github is None and os.environ.get("GITHUB_TOKEN") and repo_hint:
            actual_github = GitHubAdapter(repository=repo_hint)

        run_repository = RunRepository(database)
        ledger = LedgerStore(database)
        memory = SQLiteMemoryRepository(database)
        governance = GovernanceGate.from_repo(root)
        task_validation_policy = load_task_validation_policy(root)
        workspace = RepoWorkspaceAdapter(
            root,
            allowed_check_commands=task_validation_policy.allowed_commands,
            check_shell=task_validation_policy.runner,
        )
        git = GitAdapter(root)
        radar_repository = RadarRepository(database)
        radar = RadarService.from_repo(
            repo_root=root,
            radar_repository=radar_repository,
            run_repository=run_repository,
            ledger=ledger,
            memory=memory,
            governance=governance,
            workspace=workspace,
            git=git,
            github=actual_github,
            source=radar_source,
        )

        return cls(
            repo_root=root,
            database=database,
            run_repository=run_repository,
            ledger=ledger,
            memory=memory,
            governance=governance,
            workspace=workspace,
            git=git,
            task_validation_policy=task_validation_policy,
            planner=planner,
            provider=actual_provider,
            github=actual_github,
            radar_service=radar,
        )

    def doctor_report(self) -> dict[str, object]:
        with self.database.connect() as connection:
            run_count = int(connection.execute("SELECT COUNT(*) FROM runs").fetchone()[0])
            radar_run_count = int(connection.execute("SELECT COUNT(*) FROM radar_runs").fetchone()[0])
        return {
            "status": "ok",
            "kernel": build_kernel_summary(self.repo_root),
            "governance": self.governance.policy_snapshot(),
            "runtime": {
                "db_path": self._display_path(self.database.db_path),
                "run_count": run_count,
                "radar_run_count": radar_run_count,
                "planner_available": self.planner is not None,
                "github_available": self.github is not None,
                "validation_config": self._display_path(self.task_validation_policy.config_path),
                "validation_commands": list(self.task_validation_policy.allowed_commands),
                "validation_command_ids": list(self.task_validation_policy.command_ids),
                "validation_profiles": {
                    name: list(values) for name, values in self.task_validation_policy.profiles.items()
                },
                "default_validation_profile": self.task_validation_policy.default_profile,
                "supported_edit_modes": list(self.SUPPORTED_EDIT_MODES),
                "task_allow_flags": [
                    "repo-write",
                    PermissionTier.DESTRUCTIVE_REPO_WRITE.value,
                    "external-write",
                ],
            },
            "radar": self.radar.state_snapshot(),
        }

    def auth_preflight_report(self) -> dict[str, object]:
        kernel = load_kernel_config(self.repo_root)
        github_local = GitHubAdapter.inspect_local_auth(repo_root=self.repo_root)
        repo_hint_env = str(os.environ.get("SKYLATTICE_GITHUB_REPOSITORY", "")).strip()
        repo_hint_kernel = str(kernel.runtime.remote_ledger).strip()
        repo_hint_effective = repo_hint_env or repo_hint_kernel or None
        auth = {
            "gh_cli_available": github_local["gh_cli_available"],
            "gh_auth_logged_in": github_local["gh_auth_logged_in"],
            "gh_auth_token_accessible": github_local["gh_auth_token_accessible"],
            "gh_account": github_local["gh_account"],
            "github_token_env_present": bool(str(os.environ.get("GITHUB_TOKEN", "")).strip()),
            "openai_key_env_present": bool(str(os.environ.get("OPENAI_API_KEY", "")).strip()),
            "repo_hint_env_present": bool(repo_hint_env),
            "repo_hint_kernel_present": bool(repo_hint_kernel),
            "repo_hint_effective": repo_hint_effective,
            "repo_hint_origin_detected": github_local["repo_hint_origin_detected"],
            "origin_remote_url": github_local["origin_remote_url"],
            "bridge_command": "python -m skylattice.cli doctor github-bridge --format env",
        }
        capabilities = {
            "planner_available": self.planner is not None,
            "github_available": self.github is not None,
            "radar_source_available": self.radar.source is not None,
            "default_provider": self.radar.config.providers.default_provider,
            "default_schedule": self.radar.config.schedule.default_schedule,
        }
        return {
            "status": "ok",
            "auth": auth,
            "capabilities": capabilities,
            "remediation": self._build_auth_preflight_remediation(auth, capabilities),
        }

    def github_bridge_report(self) -> dict[str, object]:
        kernel = load_kernel_config(self.repo_root)
        preferred_repository = (
            str(os.environ.get("SKYLATTICE_GITHUB_REPOSITORY", "")).strip()
            or str(kernel.runtime.remote_ledger).strip()
            or None
        )
        bridge = GitHubAdapter.build_explicit_bridge(
            repo_root=self.repo_root,
            preferred_repository=preferred_repository,
        )
        return {
            "status": "ok" if bridge["bridge_ready"] else "blocked",
            "bridge_ready": bridge["bridge_ready"],
            "token_source": bridge["token_source"],
            "repo_hint_source": bridge["repo_hint_source"],
            "repo_hint": bridge["repo_hint"],
            "issues": list(bridge["issues"]),
            "diagnostics": bridge["diagnostics"],
            "recommended_command": "python -m skylattice.cli doctor github-bridge --format env",
        }

    def github_bridge_env_exports(self) -> str:
        kernel = load_kernel_config(self.repo_root)
        preferred_repository = (
            str(os.environ.get("SKYLATTICE_GITHUB_REPOSITORY", "")).strip()
            or str(kernel.runtime.remote_ledger).strip()
            or None
        )
        bridge = GitHubAdapter.build_explicit_bridge(
            repo_root=self.repo_root,
            preferred_repository=preferred_repository,
        )
        return GitHubAdapter.format_explicit_bridge_env(bridge)

    def run_task(
        self,
        *,
        goal_input: str,
        allow_repo_write: bool = False,
        allow_destructive_repo_write: bool = False,
        allow_external_write: bool = False,
    ) -> TaskRun:
        if self.planner is None:
            raise RuntimeError("No planner is configured. Set OPENAI_API_KEY or inject a provider.")

        goal_text, goal_source = self._load_goal(goal_input)
        run_id = f"run-{uuid.uuid4().hex}"
        runtime_snapshot = self.doctor_report()["kernel"]
        self.run_repository.create_run(
            run_id=run_id,
            goal=goal_text,
            goal_source=goal_source,
            runtime_snapshot=runtime_snapshot,
            status=RunStatus.CREATED,
        )
        self.ledger.append(
            run_id=run_id,
            kind=EventKind.RUN,
            summary="Task run created",
            actor="skylattice",
            payload={"goal_source": goal_source},
        )
        self.memory.create(
            layer=MemoryLayer.WORKING,
            summary=f"Active task: {goal_text[:160]}",
            run_id=run_id,
            source_refs=[goal_source],
            metadata={"phase": "active"},
        )
        repo_context = self._build_repo_context(goal_text=goal_text)
        plan = self.planner.create_plan(
            goal=goal_text,
            repo_context=repo_context,
            allowed_validation_commands=self.task_validation_policy.allowed_refs,
        )
        branch_name = self._build_branch_name(plan.get("branch_name", "task"), run_id)
        steps = self._plan_to_steps(run_id=run_id, plan=plan, branch_name=branch_name)
        self.run_repository.save_plan(
            run_id,
            plan_summary=str(plan.get("summary", "")),
            plan=plan,
            branch_name=branch_name,
            steps=steps,
        )
        self.ledger.append(
            run_id=run_id,
            kind=EventKind.RUN,
            summary="Task plan created",
            actor="planner",
            payload={"branch_name": branch_name, "step_count": len(steps)},
        )
        self.run_repository.grant_approvals(
            run_id,
            self._build_approvals(
                allow_repo_write=allow_repo_write,
                allow_destructive_repo_write=allow_destructive_repo_write,
                allow_external_write=allow_external_write,
            ),
        )
        return self._execute_until_blocked(run_id)

    def resume_task(
        self,
        *,
        run_id: str,
        allow_repo_write: bool = False,
        allow_destructive_repo_write: bool = False,
        allow_external_write: bool = False,
    ) -> TaskRun:
        run = self.run_repository.get_run(run_id)
        recovery = self._build_recovery_summary(run, self.run_repository.list_steps(run_id))
        self.run_repository.grant_approvals(
            run_id,
            self._build_approvals(
                allow_repo_write=allow_repo_write,
                allow_destructive_repo_write=allow_destructive_repo_write,
                allow_external_write=allow_external_write,
            ),
        )
        self.ledger.append(
            run_id=run_id,
            kind=EventKind.APPROVAL,
            summary="Approvals updated for run",
            actor="operator",
            payload={
                "repo_write": allow_repo_write,
                "destructive_repo_write": allow_destructive_repo_write,
                "external_write": allow_external_write,
            },
        )
        self.ledger.append(
            run_id=run_id,
            kind=EventKind.RUN,
            summary="Task run resume requested",
            actor="operator",
            payload={
                "resumable": recovery.get("resumable", False),
                "next_step_id": recovery.get("next_step_id"),
                "next_action_name": recovery.get("next_action_name"),
                "recommended_allows": recovery.get("recommended_allows", []),
            },
        )
        return self._execute_until_blocked(run_id)

    def get_run(self, run_id: str) -> TaskRun:
        return self.run_repository.get_run(run_id)

    def inspect_run(self, run_id: str) -> dict[str, object]:
        run = self.run_repository.get_run(run_id)
        steps = self.run_repository.list_steps(run_id)
        return {
            "run": self._serialize_run(run),
            "recovery": self._build_recovery_summary(run, steps),
            "steps": [self._serialize_step(step) for step in steps],
            "events": [self._serialize_event(event) for event in self.ledger.list_for_run(run_id)],
            "memory": [self._serialize_memory(record) for record in self.memory.list_for_run(run_id)],
        }

    def get_run_recovery(self, run_id: str) -> dict[str, object]:
        run = self.run_repository.get_run(run_id)
        return self._build_recovery_summary(run, self.run_repository.list_steps(run_id))

    def scan_radar(self, *, window: str = "manual", limit: int | None = None):
        return self.radar.scan(window=window, limit=limit)

    def get_radar_run(self, run_id: str):
        return self.radar.get_run(run_id)

    def inspect_radar_run(self, run_id: str) -> dict[str, object]:
        return self.radar.inspect_run(run_id)

    def inspect_radar_target(self, identifier: str) -> dict[str, object]:
        return self.radar.inspect_target(identifier)

    def replay_radar_candidate(self, candidate_id: str):
        return self.radar.replay_candidate(candidate_id)

    def rollback_radar_promotion(self, promotion_id: str):
        return self.radar.rollback_promotion(promotion_id)

    def latest_radar_digest(self) -> dict[str, object]:
        return self.radar.latest_digest()

    def list_memory_records(
        self,
        *,
        layers: tuple[MemoryLayer, ...] | None = None,
        statuses: tuple[RecordStatus, ...] | None = None,
        limit: int = 50,
    ) -> list[dict[str, object]]:
        effective_statuses = statuses if statuses is not None else (RecordStatus.ACTIVE,)
        records = self.memory.list_records(layers=layers, statuses=effective_statuses, limit=limit)
        return [self._serialize_memory(record) for record in records]

    def inspect_memory_record(self, record_id: str) -> dict[str, object]:
        return self._serialize_memory(self.memory.get_record(record_id))

    def search_memory(
        self,
        *,
        query: str,
        layers: tuple[MemoryLayer, ...] | None = None,
        statuses: tuple[RecordStatus, ...] | None = None,
        limit: int = 5,
    ) -> list[dict[str, object]]:
        records = self.memory.retrieve(
            RetrievalRequest(
                layers=layers or tuple(MemoryLayer),
                query=query,
                limit=limit,
                include_stale=statuses is not None,
                statuses=statuses or (),
                sort_by=RetrievalSort.RELEVANCE,
            )
        )
        return [self._serialize_memory(record) for record in records]

    def list_memory_review_queue(self, *, limit: int = 50) -> list[dict[str, object]]:
        records = self.memory.list_records(statuses=(RecordStatus.CONSTRAINED,), limit=limit)
        return [self._serialize_memory(record) for record in records]

    def propose_profile_memory(self, *, key: str, value: str, reason: str) -> dict[str, object]:
        profile_key = key.strip()
        profile_value = value.strip()
        rationale = reason.strip()
        if not profile_key or not profile_value or not rationale:
            raise RuntimeError("Profile memory proposals require non-empty key, value, and reason.")
        record = self.memory.create(
            layer=MemoryLayer.PROFILE,
            summary=f"Profile preference for {profile_key}: {profile_value}",
            source_refs=[profile_key],
            metadata={
                "proposal_type": "profile_update",
                "profile_key": profile_key,
                "value": profile_value,
                "reason": rationale,
            },
            status=RecordStatus.CONSTRAINED,
        )
        return self._serialize_memory(record)

    def confirm_memory_record(self, record_id: str) -> dict[str, object]:
        record = self.memory.get_record(record_id)
        if record.status is not RecordStatus.CONSTRAINED:
            raise RuntimeError(f"Memory record {record_id} is not waiting for review.")
        proposal_type = str(record.metadata.get("proposal_type", ""))
        if proposal_type == "profile_update":
            confirmed = self._confirm_profile_record(record)
        elif proposal_type == "semantic_compaction":
            confirmed = self._confirm_semantic_compaction(record)
        elif proposal_type == "procedural_dedup":
            confirmed = self._confirm_procedural_dedup(record)
        else:
            confirmed = self.memory.update_record(record.record_id, status=RecordStatus.ACTIVE)
        return self._serialize_memory(confirmed)

    def reject_memory_record(self, record_id: str) -> dict[str, object]:
        record = self.memory.get_record(record_id)
        if record.status is not RecordStatus.CONSTRAINED:
            raise RuntimeError(f"Memory record {record_id} is not waiting for review.")
        self.memory.rollback(record.record_id)
        return self._serialize_memory(self.memory.get_record(record.record_id))

    def rollback_memory_record(self, record_id: str) -> dict[str, object]:
        record = self.memory.get_record(record_id)
        if record.status is not RecordStatus.ACTIVE:
            raise RuntimeError(f"Only active memory records can be rolled back: {record_id}")
        self.memory.rollback(record.record_id)
        return self._serialize_memory(self.memory.get_record(record.record_id))

    def create_semantic_compaction_proposals(self) -> list[dict[str, object]]:
        active_records = self.memory.list_records(
            layers=(MemoryLayer.SEMANTIC,),
            statuses=(RecordStatus.ACTIVE,),
        )
        proposals: list[dict[str, object]] = []
        groups: dict[tuple[str, str], list[object]] = {}

        for record in active_records:
            normalized = self._normalize_summary(record.summary)
            if normalized:
                groups.setdefault(("summary", normalized), []).append(record)
            for tag in sorted(self._coerce_tag_list(record.metadata.get("topic_tags"))):
                groups.setdefault(("tag", tag), []).append(record)

        for (basis, value), records in groups.items():
            deduped = self._dedupe_records(records)
            if len(deduped) < 2:
                continue
            if basis == "summary":
                summary = deduped[0].summary
            else:
                summary = f"Compacted semantic memory for topic '{value}'."
            proposal = self._create_semantic_proposal(
                summary=summary,
                basis=basis,
                basis_value=value,
                records=deduped,
            )
            if proposal is not None:
                proposals.append(self._serialize_memory(proposal))

        return proposals

    def create_procedural_dedup_proposals(self) -> list[dict[str, object]]:
        active_records = self.memory.list_records(
            layers=(MemoryLayer.PROCEDURAL,),
            statuses=(RecordStatus.ACTIVE,),
        )
        by_workflow: dict[str, list[object]] = {}
        for record in active_records:
            workflow = str(record.metadata.get("workflow", "")).strip()
            if workflow:
                by_workflow.setdefault(workflow, []).append(record)

        proposals: list[dict[str, object]] = []
        for workflow, records in sorted(by_workflow.items()):
            deduped = self._dedupe_records(records)
            if len(deduped) < 2:
                continue
            proposal = self._create_procedural_proposal(workflow=workflow, records=deduped)
            if proposal is not None:
                proposals.append(self._serialize_memory(proposal))
        return proposals

    def export_memory_records(
        self,
        *,
        layers: tuple[MemoryLayer, ...] | None = None,
        statuses: tuple[RecordStatus, ...] | None = None,
        output_path: str | None = None,
    ) -> dict[str, object]:
        records = self.memory.list_records(layers=layers, statuses=statuses)
        destination = self._resolve_memory_export_path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "export_version": 1,
            "generated_at": datetime.now(UTC).isoformat(),
            "filters": {
                "layers": [layer.value for layer in layers or ()],
                "statuses": [status.value for status in statuses or ()],
            },
            "count": len(records),
            "records": [self._serialize_memory(record) for record in records],
        }
        destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return {
            "path": self._display_path(destination),
            "count": len(records),
            "export_version": 1,
        }

    def _execute_until_blocked(self, run_id: str) -> TaskRun:
        run = self.run_repository.get_run(run_id)
        steps = self.run_repository.list_steps(run_id)
        approval_map = run.approval_map()
        self.run_repository.update_status(run_id, RunStatus.RUNNING)

        for step in steps:
            if step.status is RunStepStatus.VERIFIED:
                continue
            approved = approval_map.get(step.required_tier)
            destructive = self._step_is_destructive(step)
            destructive_approved = approval_map.get(PermissionTier.DESTRUCTIVE_REPO_WRITE)
            outcome = self.governance.evaluate(
                GovernanceRequest(
                    tier=step.required_tier,
                    summary=step.summary,
                    target_path=str(step.action_args.get("path", "")) or None,
                    destructive=destructive,
                    user_approved=bool(approved and approved.granted),
                    destructive_approved=bool(destructive_approved and destructive_approved.granted),
                )
            )
            if outcome.decision is GovernanceDecision.DENIED:
                self.run_repository.update_status(run_id, RunStatus.WAITING_APPROVAL, error=outcome.reason)
                blocked_result = {
                    **step.result,
                    "recovery": self._step_recovery_metadata(
                        step,
                        run_status=RunStatus.WAITING_APPROVAL,
                        reason=outcome.reason,
                    ),
                }
                blocked_step = RunStep(
                    **{**asdict(step), "status": RunStepStatus.BLOCKED, "result": blocked_result}
                )
                self.run_repository.update_step(blocked_step)
                self.ledger.append(
                    run_id=run_id,
                    kind=EventKind.APPROVAL,
                    summary=f"Run paused before step {step.step_id}",
                    actor="governance",
                    payload={
                        "reason": outcome.reason,
                        "required_tier": step.required_tier.value,
                        "destructive": destructive,
                    },
                )
                return self.run_repository.get_run(run_id)

            next_attempt = self._next_attempt_count(step)
            if step.status in {RunStepStatus.FAILED, RunStepStatus.BLOCKED}:
                self.ledger.append(
                    run_id=run_id,
                    kind=EventKind.RUN,
                    summary=f"Retrying step {step.step_id}",
                    actor="skylattice",
                    payload={
                        "step_id": step.step_id,
                        "attempt_count": next_attempt,
                        "action_name": step.action_name,
                    },
                )

            self.run_repository.set_current_step(run_id, step.step_index)
            running_step = RunStep(**{**asdict(step), "status": RunStepStatus.RUNNING})
            self.run_repository.update_step(running_step)
            try:
                result = self._execute_step(run, step)
                verified = self._verify_step(step, result)
            except Exception as exc:  # noqa: BLE001
                status = (
                    RunStatus.HALTED
                    if step.required_tier in {PermissionTier.REPO_WRITE, PermissionTier.EXTERNAL_WRITE}
                    else RunStatus.FAILED
                )
                failed_result = self._build_failed_step_result(step, error=str(exc), run_status=status)
                failed_step = RunStep(
                    **{**asdict(step), "status": RunStepStatus.FAILED, "result": failed_result}
                )
                self.run_repository.update_step(failed_step)
                self.run_repository.update_status(run_id, status, error=str(exc))
                self._finalize_memory(run_id, success=False)
                self.ledger.append(
                    run_id=run_id,
                    kind=EventKind.EVALUATION,
                    summary=f"Step {step.step_id} failed",
                    actor="verifier",
                    payload={"error": str(exc)},
                    reversible=False,
                )
                return self.run_repository.get_run(run_id)

            verified_result = self._build_verified_step_result(step, {**result, "verified": verified})
            verified_step = RunStep(
                **{**asdict(step), "status": RunStepStatus.VERIFIED, "result": verified_result}
            )
            self.run_repository.update_step(verified_step)
            self.ledger.append(
                run_id=run_id,
                kind=EventKind.ACTION,
                summary=step.summary,
                actor="executor",
                payload=result,
                artifact_refs=tuple(result.get("artifact_refs", [])),
            )
            self.ledger.append(
                run_id=run_id,
                kind=EventKind.EVALUATION,
                summary=f"Step {step.step_id} verified",
                actor="verifier",
                payload={"step_id": step.step_id},
            )
            run = self.run_repository.get_run(run_id)

        self.run_repository.update_status(run_id, RunStatus.VERIFYING)
        result = {
            "branch_name": run.branch_name,
            "step_count": len(steps),
            "status": "completed",
        }
        if self.github is not None:
            latest_events = self.ledger.list_for_run(run_id)
            for event in reversed(latest_events):
                url = event.payload.get("html_url") if isinstance(event.payload, dict) else None
                if url:
                    result["html_url"] = url
                    break
        self.run_repository.set_result(run_id, result)
        self.run_repository.update_status(run_id, RunStatus.COMPLETED)
        self._finalize_memory(run_id, success=True)
        self.ledger.append(
            run_id=run_id,
            kind=EventKind.RUN,
            summary="Task run completed",
            actor="skylattice",
            payload=result,
        )
        return self.run_repository.get_run(run_id)

    def _execute_step(self, run: TaskRun, step: RunStep) -> dict[str, object]:
        if step.action_name == "git.create_branch":
            return self.git.create_branch(str(step.action_args["branch_name"]))

        if step.action_name in {"workspace.edit_file", "workspace.rewrite_file", "workspace.create_file"}:
            return self._execute_rewrite_step(run, step)

        if step.action_name == "workspace.copy_file":
            return self._execute_copy_step(step)

        if step.action_name == "workspace.move_file":
            return self._execute_move_step(step)

        if step.action_name == "workspace.delete_file":
            return self._execute_delete_step(step)

        if step.action_name in {"workspace.replace_text", "workspace.insert_after", "workspace.append_text"}:
            return self._execute_materialized_edit_step(run, step)

        if step.action_name in {"workspace.run_check", "workspace.run_validation"}:
            result = self.workspace.run_check(str(step.action_args["command"]))
            if step.action_args.get("command_id"):
                result["validation_id"] = str(step.action_args["command_id"])
            return result

        if step.action_name == "git.commit_all":
            self.git.add_all()
            message = self.git.commit(str(step.action_args["message"]))
            return {"message": message}

        if step.action_name == "git.push_branch":
            branch_name = str(step.action_args["branch_name"])
            pushed = self.git.push(branch_name, remote=str(step.action_args.get("remote", "origin")))
            return {"branch_name": pushed}

        if step.action_name == "github.inspect_issue":
            if self.github is None:
                raise RuntimeError(
                    "GitHub adapter is not configured. Run `python -m skylattice.cli doctor auth` to inspect token and repo-hint requirements."
                )
            issue_number = int(step.action_args["issue_number"])
            issue = self.github.get_issue(issue_number)
            dedupe_key = str(step.action_args.get("dedupe_key", "")).strip()
            dedupe_comment_exists = False
            dedupe_comment_url = None
            if dedupe_key and hasattr(self.github, "list_issue_comments"):
                marker = f"<!-- skylattice:{dedupe_key} -->"
                for comment in self.github.list_issue_comments(issue_number=issue_number):
                    if marker in str(comment.get("body", "")):
                        dedupe_comment_exists = True
                        dedupe_comment_url = comment.get("html_url")
                        break
            return {
                "issue_number": int(issue.get("number", issue_number)),
                "title": issue.get("title"),
                "state": issue.get("state"),
                "html_url": issue.get("html_url"),
                "remote_target_kind": "issue",
                "remote_target_state": str(issue.get("state", "") or "unknown").lower(),
                "dedupe_comment_exists": dedupe_comment_exists,
                "dedupe_comment_url": dedupe_comment_url,
                "artifact_refs": [str(issue.get("html_url", ""))] if issue.get("html_url") else [],
            }

        if step.action_name == "github.inspect_pull_request":
            if self.github is None:
                raise RuntimeError(
                    "GitHub adapter is not configured. Run `python -m skylattice.cli doctor auth` to inspect token and repo-hint requirements."
                )
            head_branch = str(step.action_args["head_branch"])
            base_branch = str(step.action_args.get("base_branch", ""))
            pull_request = self.github.find_open_pull_request_by_head(head_branch)
            if pull_request is None:
                return {
                    "number": None,
                    "html_url": None,
                    "state": "none",
                    "draft": False,
                    "head_branch": head_branch,
                    "base_branch": base_branch,
                    "remote_target_kind": "pull_request",
                    "remote_target_state": "none",
                    "artifact_refs": [],
                }
            return {
                "number": pull_request.get("number"),
                "html_url": pull_request.get("html_url"),
                "state": str(pull_request.get("state", "open") or "open"),
                "draft": bool(pull_request.get("draft", False)),
                "head_branch": str(pull_request.get("head_branch", head_branch) or head_branch),
                "base_branch": str(pull_request.get("base_branch", base_branch) or base_branch),
                "remote_target_kind": "pull_request",
                "remote_target_state": self._pull_request_remote_state(
                    state=pull_request.get("state"),
                    draft=pull_request.get("draft"),
                ),
                "artifact_refs": [str(pull_request.get("html_url", ""))] if pull_request.get("html_url") else [],
            }

        if step.action_name == "github.sync_pull_request":
            if self.github is None:
                raise RuntimeError(
                    "GitHub adapter is not configured. Run `python -m skylattice.cli doctor auth` to inspect token and repo-hint requirements."
                )
            response = self.github.create_or_update_draft_pr(
                head_branch=str(step.action_args["head_branch"]),
                base_branch=str(step.action_args["base_branch"]),
                title=str(step.action_args["title"]),
                body=str(step.action_args["body"]),
            )
            return {
                "number": response.get("number"),
                "html_url": response.get("html_url"),
                "state": str(response.get("state", "open") or "open"),
                "draft": bool(response.get("draft", False)),
                "head_branch": str(response.get("head_branch", step.action_args["head_branch"])),
                "base_branch": str(response.get("base_branch", step.action_args["base_branch"])),
                "reused": bool(response.get("reused", False)),
                "sync_mode": str(response.get("sync_mode", "create")),
                "dedupe_key": str(response.get("dedupe_key", step.action_args["head_branch"])),
                "remote_target_kind": "pull_request",
                "remote_target_state": self._pull_request_remote_state(
                    state=response.get("state"),
                    draft=response.get("draft"),
                ),
                "artifact_refs": [str(response.get("html_url", ""))] if response.get("html_url") else [],
            }

        if step.action_name == "github.add_issue_comment":
            if self.github is None:
                raise RuntimeError(
                    "GitHub adapter is not configured. Run `python -m skylattice.cli doctor auth` to inspect token and repo-hint requirements."
                )
            issue_number = int(step.action_args["issue_number"])
            body = str(step.action_args["body"])
            dedupe_key = self._dedupe_key_for_step(step)
            if hasattr(self.github, "create_or_reuse_issue_comment"):
                response = self.github.create_or_reuse_issue_comment(
                    issue_number=issue_number,
                    body=body,
                    dedupe_key=dedupe_key or f"{step.run_id}:{step.step_id}",
                )
            else:
                response = self.github.add_issue_comment(issue_number=issue_number, body=body)
            return {
                "issue_number": int(response.get("issue_number", issue_number)),
                "html_url": response.get("html_url"),
                "reused": bool(response.get("reused", False)),
                "sync_mode": str(response.get("sync_mode", "create")),
                "dedupe_key": str(response.get("dedupe_key", dedupe_key or "")),
                "remote_target_kind": "issue",
                "artifact_refs": [str(response.get("html_url", ""))] if response.get("html_url") else [],
            }

        raise RuntimeError(f"Unsupported action: {step.action_name}")

    def _execute_rewrite_step(self, run: TaskRun, step: RunStep) -> dict[str, object]:
        if self.provider is None:
            raise RuntimeError("No content provider is available for file edits")
        path = str(step.action_args["path"])
        updated = self.provider.rewrite_file(
            goal=run.goal,
            path=path,
            current_content=self.workspace.read_text(path),
            instructions=str(step.action_args["instructions"]),
            plan_summary=run.plan_summary,
            repo_context=self._build_repo_context(goal_text=run.goal),
        )
        payload = {"mode": "rewrite", "content": updated}
        if step.action_name == "workspace.create_file":
            payload["mode"] = "create_file"
        written = self.workspace.apply_materialized_edit(
            path,
            payload,
            create_if_missing=bool(step.action_args.get("create_if_missing", step.action_name == "workspace.create_file")),
        )
        return {
            "path": written,
            "artifact_refs": [written],
            "materialized_edit": payload,
            "verification_metadata": {"content_length": len(updated)},
        }

    def _execute_materialized_edit_step(self, run: TaskRun, step: RunStep) -> dict[str, object]:
        if self.provider is None:
            raise RuntimeError("No content provider is available for file edits")
        path = str(step.action_args["path"])
        payload = self.provider.materialize_edit(
            goal=run.goal,
            path=path,
            mode=str(step.action_args["mode"]),
            current_content=self.workspace.read_text(path),
            instructions=str(step.action_args["instructions"]),
            plan_summary=run.plan_summary,
            repo_context=self._build_repo_context(goal_text=run.goal),
        )
        written = self.workspace.apply_materialized_edit(
            path,
            payload,
            create_if_missing=bool(step.action_args.get("create_if_missing", False)),
        )
        return {
            "path": written,
            "source_path": payload.get("source_path"),
            "artifact_refs": [written],
            "materialized_edit": payload,
            "verification_metadata": {
                "content_length": len(self.workspace.read_text(path)),
                "expected_occurrences": payload.get("expected_occurrences"),
            },
        }

    def _execute_copy_step(self, step: RunStep) -> dict[str, object]:
        source_path = str(step.action_args["source_path"])
        destination_path = str(step.action_args["path"])
        written = self.workspace.copy_file(source_path, destination_path)
        payload = {
            "mode": "copy_file",
            "source_path": source_path,
        }
        return {
            "path": written,
            "source_path": source_path,
            "artifact_refs": [written],
            "materialized_edit": payload,
            "verification_metadata": {
                "content_length": len(self.workspace.read_text(destination_path)),
            },
        }

    def _execute_move_step(self, step: RunStep) -> dict[str, object]:
        source_path = str(step.action_args["source_path"])
        destination_path = str(step.action_args["path"])
        written = self.workspace.move_file(source_path, destination_path)
        payload = {
            "mode": "move_file",
            "source_path": source_path,
        }
        return {
            "path": written,
            "source_path": source_path,
            "artifact_refs": [written],
            "materialized_edit": payload,
            "verification_metadata": {
                "content_length": len(self.workspace.read_text(destination_path)),
            },
        }

    def _execute_delete_step(self, step: RunStep) -> dict[str, object]:
        target_path = str(step.action_args["path"])
        deleted = self.workspace.delete_file(target_path)
        payload = {"mode": "delete_file"}
        return {
            "path": deleted,
            "artifact_refs": [],
            "materialized_edit": payload,
            "verification_metadata": {
                "deleted": True,
            },
        }

    def _verify_step(self, step: RunStep, result: dict[str, object]) -> bool:
        if step.action_name in {"workspace.run_check", "workspace.run_validation"}:
            expected_returncode = int(step.verification.get("expected_returncode", 0))
            if int(result.get("returncode", 1)) != expected_returncode:
                raise RuntimeError(
                    f"Check failed: {result.get('command')} returned {result.get('returncode', 1)}; "
                    f"expected {expected_returncode}"
                )
            stdout = str(result.get("stdout", ""))
            stderr = str(result.get("stderr", ""))
            for expected in step.verification.get("stdout_contains", []):
                if str(expected) not in stdout:
                    raise RuntimeError(f"Check failed: stdout missing expected text {expected!r}")
            for expected in step.verification.get("stderr_contains", []):
                if str(expected) not in stderr:
                    raise RuntimeError(f"Check failed: stderr missing expected text {expected!r}")
            return True
        if step.action_name == "workspace.delete_file":
            path = self.repo_root / str(step.action_args["path"])
            if path.exists():
                raise RuntimeError(f"Deleted file still exists: {step.action_args['path']}")
            if "materialized_edit" not in result:
                raise RuntimeError(f"Delete step did not record a materialized payload: {step.action_args['path']}")
            return True
        if step.action_name == "workspace.move_file":
            path = self.repo_root / str(step.action_args["path"])
            source_path = self.repo_root / str(step.action_args["source_path"])
            if source_path.exists():
                raise RuntimeError(f"Moved source still exists: {step.action_args['source_path']}")
            if not path.exists():
                raise RuntimeError(f"Moved destination is missing: {step.action_args['path']}")
            if "materialized_edit" not in result:
                raise RuntimeError(f"Move step did not record a materialized payload: {step.action_args['path']}")
            return True
        if step.action_name in {
            "workspace.edit_file",
            "workspace.rewrite_file",
            "workspace.create_file",
            "workspace.replace_text",
            "workspace.insert_after",
            "workspace.append_text",
            "workspace.copy_file",
        }:
            path = step.action_args["path"]
            if not self.workspace.read_text(str(path)).strip():
                raise RuntimeError(f"Edited file is empty: {path}")
            if "materialized_edit" not in result:
                raise RuntimeError(f"Edit step did not record a materialized payload: {path}")
            if step.action_name == "workspace.copy_file":
                source_path = result.get("source_path")
                if not source_path:
                    raise RuntimeError(f"Copy step did not record source_path: {path}")
                if self.workspace.read_text(str(source_path)) != self.workspace.read_text(str(path)):
                    raise RuntimeError(f"Copied file does not match source: {path}")
            return True
        if step.action_name == "git.commit_all":
            if self.git.status_porcelain().strip():
                raise RuntimeError("Worktree is still dirty after commit")
            return True
        if step.action_name == "github.inspect_pull_request":
            state = str(result.get("remote_target_state", "none"))
            if state not in {"none", "open-draft", "open-ready"}:
                raise RuntimeError(f"Unexpected pull request preflight state: {state}")
            return True
        if step.action_name == "github.sync_pull_request":
            if not result.get("html_url"):
                raise RuntimeError("GitHub PR sync did not return html_url")
            return True
        if step.action_name == "github.inspect_issue":
            if str(result.get("state", "")).lower() != "open":
                raise RuntimeError(f"GitHub issue is not open: {result.get('issue_number')}")
            return True
        if step.action_name == "github.add_issue_comment":
            if not result.get("html_url"):
                raise RuntimeError("GitHub comment did not return html_url")
            return True
        return True

    def _build_repo_context(self, *, goal_text: str = "") -> dict[str, object]:
        files = self.workspace.list_files(limit=120)
        context = {
            "repo_root": ".",
            "current_branch": self._safe_call(self.git.current_branch, default="main"),
            "remote_url": self._safe_call(self.git.remote_url, default=""),
            "files": files,
            "allowed_validation_commands": list(self.task_validation_policy.allowed_commands),
            "allowed_validation_refs": list(self.task_validation_policy.allowed_refs),
            "default_validation_profile": self.task_validation_policy.default_profile,
            "validation_profiles": {
                name: list(values) for name, values in self.task_validation_policy.profiles.items()
            },
            "validation_catalog": self.task_validation_policy.command_catalog(),
            "supported_edit_modes": list(self.SUPPORTED_EDIT_MODES),
            "destructive_edit_modes": ["move_file", "delete_file"],
            "memory_context": self._memory_context_for_goal(goal_text),
        }
        if self.github is not None:
            context["github_context"] = self._github_sync_context()
        for candidate in ("README.md", "docs/roadmap.md", "docs/architecture.md"):
            if candidate in files:
                context[candidate] = self.workspace.read_text(candidate)[:4000]
        return context

    def _github_sync_context(self) -> dict[str, object]:
        if self.github is None:
            return {}
        try:
            issues = self.github.list_issues(state="open", per_page=5)
            pulls = self.github.list_pull_requests(state="open", per_page=5)
        except Exception as exc:  # noqa: BLE001
            return {"available": False, "error": str(exc)}
        return {
            "available": True,
            "repository": self.github.repo.slug,
            "open_issues": [
                {
                    "number": item.get("number"),
                    "title": item.get("title"),
                    "state": item.get("state"),
                    "html_url": item.get("html_url"),
                }
                for item in issues
            ],
            "open_pull_requests": [
                {
                    "number": item.get("number"),
                    "title": item.get("title"),
                    "state": item.get("state"),
                    "html_url": item.get("html_url"),
                    "head_ref": item.get("head", {}).get("ref") if isinstance(item.get("head"), dict) else None,
                    "base_ref": item.get("base", {}).get("ref") if isinstance(item.get("base"), dict) else None,
                }
                for item in pulls
            ],
        }

    def _build_recovery_summary(self, run: TaskRun, steps: list[RunStep]) -> dict[str, object]:
        step: RunStep | None = None
        status_label = "not_needed"
        resumable = False
        reason = ""

        if run.status is RunStatus.WAITING_APPROVAL:
            step = next((item for item in steps if item.status is RunStepStatus.BLOCKED), None)
            status_label = "awaiting_approval"
            resumable = True
            reason = run.error or "Task run is waiting for operator approval."
        elif run.status is RunStatus.HALTED:
            step = next((item for item in reversed(steps) if item.status is RunStepStatus.FAILED), None)
            status_label = "retryable"
            resumable = True
            reason = run.error or "Task run halted after a retryable repo or external write failure."
        elif run.status is RunStatus.FAILED:
            step = next((item for item in reversed(steps) if item.status is RunStepStatus.FAILED), None)
            status_label = "not_resumable"
            reason = run.error or "Task run failed in a non-retryable state."
        elif run.status is RunStatus.COMPLETED:
            status_label = "completed"
            reason = "Task run completed."
        else:
            step = next((item for item in steps if item.status in {RunStepStatus.BLOCKED, RunStepStatus.FAILED}), None)
            status_label = "in_progress"
            reason = "Task run is active."

        if step is None:
            latest_remote_step = next(
                (
                    item
                    for item in reversed(steps)
                    if item.action_name in {"github.sync_pull_request", "github.add_issue_comment", "github.inspect_issue"}
                    and item.status is RunStepStatus.VERIFIED
                ),
                None,
            )
            remote_target = self._remote_target_context(latest_remote_step, steps) if latest_remote_step is not None else {}
            return {
                "status": status_label,
                "resumable": resumable,
                "reason": reason,
                "next_step_id": None,
                "next_step_index": None,
                "next_action_name": None,
                "required_tier": None,
                "recommended_allows": [],
                "side_effect_risk": "none",
                "destructive": False,
                "attempt_count": 0,
                "last_error": run.error,
                "dedupe_key": None,
                "remote_target_kind": remote_target.get("remote_target_kind"),
                "remote_target_number": remote_target.get("remote_target_number"),
                "remote_target_url": remote_target.get("remote_target_url"),
                "remote_target_state": remote_target.get("remote_target_state"),
                "remote_target_draft": remote_target.get("remote_target_draft"),
                "sync_mode": remote_target.get("sync_mode"),
                "guidance": [],
            }

        recovery = self._step_recovery_metadata(step, run_status=run.status, reason=reason, steps=steps)
        stored = step.result.get("recovery")
        if isinstance(stored, dict):
            recovery = {**recovery, **stored}
        return {
            "status": status_label,
            "resumable": resumable,
            "reason": reason,
            "next_step_id": step.step_id,
            "next_step_index": step.step_index,
            "next_action_name": step.action_name,
            "required_tier": step.required_tier.value,
            "recommended_allows": recovery.get("recommended_allows", []),
            "side_effect_risk": recovery.get("side_effect_risk", "low"),
            "destructive": bool(recovery.get("destructive", False)),
            "attempt_count": self._step_attempt_count(step),
            "last_error": step.result.get("last_error", run.error),
            "dedupe_key": recovery.get("dedupe_key"),
            "remote_target_kind": recovery.get("remote_target_kind"),
            "remote_target_number": recovery.get("remote_target_number"),
            "remote_target_url": recovery.get("remote_target_url"),
            "remote_target_state": recovery.get("remote_target_state"),
            "remote_target_draft": recovery.get("remote_target_draft"),
            "sync_mode": recovery.get("sync_mode"),
            "guidance": recovery.get("guidance", []),
        }

    def _memory_context_for_goal(self, goal_text: str) -> dict[str, list[dict[str, object]]]:
        query = goal_text.strip()
        return {
            "profile": [
                self._serialize_memory(record)
                for record in self.memory.retrieve(
                    RetrievalRequest(
                        layers=(MemoryLayer.PROFILE,),
                        query=query,
                        limit=self.MEMORY_CONTEXT_LIMIT,
                        sort_by=RetrievalSort.RELEVANCE,
                    )
                )
            ],
            "procedural": [
                self._serialize_memory(record)
                for record in self.memory.retrieve(
                    RetrievalRequest(
                        layers=(MemoryLayer.PROCEDURAL,),
                        query=query,
                        limit=self.MEMORY_CONTEXT_LIMIT,
                        sort_by=RetrievalSort.RELEVANCE,
                    )
                )
            ],
            "semantic": [
                self._serialize_memory(record)
                for record in self.memory.retrieve(
                    RetrievalRequest(
                        layers=(MemoryLayer.SEMANTIC,),
                        query=query,
                        limit=self.MEMORY_CONTEXT_LIMIT,
                        sort_by=RetrievalSort.RELEVANCE,
                    )
                )
            ],
        }

    def _display_path(self, path: Path) -> str:
        try:
            relative = path.relative_to(self.repo_root)
        except ValueError:
            return str(path)
        return relative.as_posix() if relative.parts else "."

    @staticmethod
    def _step_attempt_count(step: RunStep) -> int:
        raw = step.result.get("attempt_count", 0)
        try:
            return int(raw)
        except (TypeError, ValueError):
            return 0

    def _next_attempt_count(self, step: RunStep) -> int:
        return self._step_attempt_count(step) + 1

    @staticmethod
    def _step_error_history(step: RunStep) -> list[str]:
        history: list[str] = []
        previous = step.result.get("previous_errors", [])
        if isinstance(previous, list):
            history.extend(str(item) for item in previous if str(item).strip())
        last_error = step.result.get("last_error")
        if isinstance(last_error, str) and last_error.strip():
            history.append(last_error)
        return list(dict.fromkeys(history))

    def _required_allows_for_step(self, step: RunStep) -> list[str]:
        allows: list[str] = []
        if step.required_tier is PermissionTier.REPO_WRITE:
            allows.append("repo-write")
        if self._step_is_destructive(step):
            allows.append(PermissionTier.DESTRUCTIVE_REPO_WRITE.value)
        if step.required_tier is PermissionTier.EXTERNAL_WRITE:
            allows.append("external-write")
        return allows

    @staticmethod
    def _side_effect_risk(action_name: str) -> str:
        if action_name in {"workspace.delete_file", "workspace.move_file"}:
            return "high"
        if action_name == "github.add_issue_comment":
            return "medium"
        if action_name in {"github.sync_pull_request", "git.push_branch"}:
            return "low"
        if action_name.startswith("workspace.") or action_name == "git.commit_all":
            return "low"
        return "none"

    @staticmethod
    def _step_is_destructive(step: RunStep) -> bool:
        return step.action_name in {"workspace.delete_file", "workspace.move_file"} or bool(
            step.action_args.get("destructive", False)
        )

    @staticmethod
    def _format_allow_flags(allows: list[str]) -> str:
        return " ".join(f"--allow {value}" for value in allows)

    def _dedupe_key_for_step(self, step: RunStep) -> str | None:
        if step.action_name == "github.sync_pull_request":
            return str(step.action_args.get("head_branch", ""))
        if step.action_name == "github.add_issue_comment":
            return f"{step.run_id}:{step.step_id}"
        if step.action_name == "git.push_branch":
            return str(step.action_args.get("branch_name", ""))
        return None

    def _step_recovery_metadata(
        self,
        step: RunStep,
        *,
        run_status: RunStatus,
        reason: str,
        steps: list[RunStep] | None = None,
    ) -> dict[str, object]:
        recommended_allows = self._required_allows_for_step(step)
        guidance: list[str] = []
        status_label = "not_needed"
        resumable = False
        remote_target = self._remote_target_context(step, steps)
        sync_mode = self._suggested_sync_mode(step, remote_target)

        if run_status is RunStatus.WAITING_APPROVAL:
            status_label = "awaiting_approval"
            resumable = True
            if recommended_allows:
                guidance.append(
                    f"Resume with {self._format_allow_flags(recommended_allows)} once you approve this step."
                )
            else:
                guidance.append("This step is waiting for approval before execution can continue.")
        elif run_status is RunStatus.HALTED:
            status_label = "retryable"
            resumable = True
            guidance.append("Review the last error before retrying this step.")
            if step.required_tier is PermissionTier.EXTERNAL_WRITE:
                guidance.append("Check whether the previous external write partially succeeded before resuming.")
            if recommended_allows:
                guidance.append(
                    f"Resume with {self._format_allow_flags(recommended_allows)} after verifying side effects."
                )
        elif run_status is RunStatus.FAILED:
            status_label = "not_resumable"
            guidance.append("Fix the underlying issue and start a new run once the repo is ready.")
        elif run_status is RunStatus.COMPLETED:
            status_label = "completed"
        else:
            status_label = "in_progress"

        if step.action_name == "github.sync_pull_request":
            if remote_target.get("remote_target_state") in {"open-draft", "open-ready"}:
                guidance.append(
                    f"Remote target is PR #{remote_target.get('remote_target_number')}; resuming will update the existing "
                    f"{'draft' if remote_target.get('remote_target_draft') else 'open'} pull request."
                )
            else:
                guidance.append("No open PR was observed for this branch; resuming will create a new draft pull request.")
        if step.action_name == "github.add_issue_comment":
            issue_number = remote_target.get("remote_target_number")
            guidance.append(f"Remote target is issue #{issue_number}." if issue_number else "Remote target is a GitHub issue comment.")
            if remote_target.get("dedupe_comment_exists"):
                guidance.append("A matching dedupe comment was already observed, so resume should reuse it instead of posting a duplicate.")
            else:
                guidance.append("No matching dedupe comment was observed during preflight.")
        if step.action_name == "github.inspect_issue" and remote_target.get("dedupe_comment_exists"):
            guidance.append("A matching dedupe comment already exists on the target issue.")

        return {
            "status": status_label,
            "resumable": resumable,
            "recommended_allows": recommended_allows,
            "side_effect_risk": self._side_effect_risk(step.action_name),
            "destructive": self._step_is_destructive(step),
            "dedupe_key": self._dedupe_key_for_step(step),
            "remote_target_kind": remote_target.get("remote_target_kind"),
            "remote_target_number": remote_target.get("remote_target_number"),
            "remote_target_url": remote_target.get("remote_target_url"),
            "remote_target_state": remote_target.get("remote_target_state"),
            "remote_target_draft": remote_target.get("remote_target_draft"),
            "sync_mode": sync_mode,
            "dedupe_comment_exists": remote_target.get("dedupe_comment_exists"),
            "guidance": guidance,
            "reason": reason,
        }

    def _build_failed_step_result(self, step: RunStep, *, error: str, run_status: RunStatus) -> dict[str, object]:
        return {
            "attempt_count": self._next_attempt_count(step),
            "last_error": error,
            "previous_errors": self._step_error_history(step),
            "recovery": self._step_recovery_metadata(step, run_status=run_status, reason=error),
        }

    def _build_verified_step_result(self, step: RunStep, result: dict[str, object]) -> dict[str, object]:
        payload = dict(result)
        payload["attempt_count"] = self._next_attempt_count(step)
        previous_errors = self._step_error_history(step)
        if previous_errors:
            payload["previous_errors"] = previous_errors
        return payload

    @staticmethod
    def _pull_request_remote_state(*, state: object, draft: object) -> str:
        normalized = str(state or "none").lower()
        if normalized in {"", "none", "null"}:
            return "none"
        if normalized != "open":
            return normalized
        return "open-draft" if bool(draft) else "open-ready"

    def _suggested_sync_mode(self, step: RunStep, remote_target: dict[str, object]) -> str | None:
        if step.action_name == "github.sync_pull_request":
            if remote_target.get("remote_target_state") in {"open-draft", "open-ready"}:
                return "update"
            return "create"
        return step.result.get("sync_mode") if isinstance(step.result, dict) else None

    def _remote_target_context(self, step: RunStep, steps: list[RunStep] | None = None) -> dict[str, object]:
        all_steps = steps or self.run_repository.list_steps(step.run_id)
        base = {
            "remote_target_kind": None,
            "remote_target_number": None,
            "remote_target_url": None,
            "remote_target_state": None,
            "remote_target_draft": None,
            "sync_mode": step.result.get("sync_mode") if isinstance(step.result, dict) else None,
            "dedupe_comment_exists": None,
        }
        if step.action_name in {"github.inspect_pull_request", "github.sync_pull_request"}:
            payload = self._matching_step_result(
                step=step,
                steps=all_steps,
                action_name="github.inspect_pull_request",
                key="head_branch",
            )
            if step.action_name == "github.inspect_pull_request" or step.result.get("number") or step.result.get("html_url"):
                payload = {**payload, **step.result}
            elif self.github is not None:
                observed = self.github.find_open_pull_request_by_head(str(step.action_args.get("head_branch", "")))
                if observed is not None:
                    payload = {**payload, **observed}
            state = str(payload.get("remote_target_state") or "").strip()
            if state in {"", "none"} and payload.get("state") not in {None, "", "none"}:
                state = self._pull_request_remote_state(
                    state=payload.get("state"),
                    draft=payload.get("draft"),
                )
            elif not state:
                state = "none"
            return {
                **base,
                "remote_target_kind": "pull_request",
                "remote_target_number": payload.get("number"),
                "remote_target_url": payload.get("html_url"),
                "remote_target_state": state,
                "remote_target_draft": bool(payload.get("draft", False)) if state != "none" else False,
                "sync_mode": step.result.get("sync_mode") or ("update" if state in {"open-draft", "open-ready"} else "create"),
            }
        if step.action_name in {"github.inspect_issue", "github.add_issue_comment"}:
            payload = self._matching_step_result(
                step=step,
                steps=all_steps,
                action_name="github.inspect_issue",
                key="issue_number",
            )
            if step.action_name == "github.inspect_issue":
                payload = {**payload, **step.result}
            elif self.github is not None and hasattr(self.github, "list_issue_comments"):
                issue_number = int(step.action_args.get("issue_number", 0))
                dedupe_key = self._dedupe_key_for_step(step)
                marker = f"<!-- skylattice:{dedupe_key} -->" if dedupe_key else ""
                if marker:
                    for comment in self.github.list_issue_comments(issue_number=issue_number):
                        if marker in str(comment.get("body", "")):
                            payload["dedupe_comment_exists"] = True
                            payload["html_url"] = payload.get("html_url") or comment.get("html_url")
                            break
            return {
                **base,
                "remote_target_kind": "issue",
                "remote_target_number": payload.get("issue_number") or step.action_args.get("issue_number"),
                "remote_target_url": payload.get("html_url"),
                "remote_target_state": payload.get("remote_target_state") or payload.get("state"),
                "remote_target_draft": None,
                "sync_mode": step.result.get("sync_mode"),
                "dedupe_comment_exists": payload.get("dedupe_comment_exists"),
            }
        return base

    @staticmethod
    def _matching_step_result(
        *,
        step: RunStep,
        steps: list[RunStep],
        action_name: str,
        key: str,
    ) -> dict[str, object]:
        for candidate in reversed(steps):
            if candidate.step_index > step.step_index:
                continue
            if candidate.action_name != action_name:
                continue
            if candidate.action_args.get(key) != step.action_args.get(key):
                continue
            if isinstance(candidate.result, dict):
                return dict(candidate.result)
        return {}

    def _resolve_memory_export_path(self, output_path: str | None) -> Path:
        if output_path:
            candidate = Path(output_path)
            resolved = candidate if candidate.is_absolute() else (self.repo_root / candidate).resolve()
        else:
            timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
            resolved = self.database.paths.memory_root / "exports" / f"{timestamp}.json"
        try:
            resolved.relative_to(self.database.paths.local_root)
        except ValueError as exc:
            raise RuntimeError("Memory exports must stay under .local/.") from exc
        return resolved

    @staticmethod
    def _normalize_summary(summary: str) -> str:
        return " ".join(re.findall(r"[a-z0-9]+", summary.lower()))

    @staticmethod
    def _coerce_tag_list(value: object) -> list[str]:
        if isinstance(value, (list, tuple, set)):
            tags = [str(item).strip().lower() for item in value if str(item).strip()]
            return sorted(dict.fromkeys(tags))
        return []

    @staticmethod
    def _dedupe_records(records: list[Any]) -> list[Any]:
        deduped: dict[str, Any] = {}
        for record in records:
            deduped[record.record_id] = record
        return sorted(
            deduped.values(),
            key=lambda item: (item.confidence, item.created_at or "", item.record_id),
            reverse=True,
        )

    def _matching_records_by_metadata(
        self,
        *,
        layer: MemoryLayer,
        statuses: tuple[RecordStatus, ...],
        key: str,
        value: str,
    ) -> list[Any]:
        matches: list[Any] = []
        for record in self.memory.list_records(layers=(layer,), statuses=statuses):
            candidate = record.metadata.get(key)
            if isinstance(candidate, (list, tuple, set)):
                values = {str(item).strip().lower() for item in candidate}
                if value.strip().lower() in values:
                    matches.append(record)
            elif str(candidate).strip().lower() == value.strip().lower():
                matches.append(record)
        return matches

    def _existing_proposal(
        self,
        *,
        layer: MemoryLayer,
        proposal_type: str,
        source_record_ids: list[str],
        discriminator_key: str,
        discriminator_value: str,
    ) -> Any | None:
        source_signature = "|".join(sorted(source_record_ids))
        for record in self.memory.list_records(layers=(layer,), statuses=(RecordStatus.CONSTRAINED,)):
            metadata = record.metadata
            if str(metadata.get("proposal_type", "")) != proposal_type:
                continue
            if str(metadata.get(discriminator_key, "")) != discriminator_value:
                continue
            existing_signature = "|".join(sorted(str(item) for item in metadata.get("source_record_ids", [])))
            if existing_signature == source_signature:
                return record
        return None

    def _create_semantic_proposal(self, *, summary: str, basis: str, basis_value: str, records: list[Any]) -> Any | None:
        source_record_ids = [record.record_id for record in records]
        existing = self._existing_proposal(
            layer=MemoryLayer.SEMANTIC,
            proposal_type="semantic_compaction",
            source_record_ids=source_record_ids,
            discriminator_key="proposal_signature",
            discriminator_value=f"{basis}:{basis_value}",
        )
        if existing is not None:
            return None
        merged_tags = sorted(
            {
                tag
                for record in records
                for tag in self._coerce_tag_list(record.metadata.get("topic_tags"))
            }
        )
        merged_sources = list(dict.fromkeys(ref for record in records for ref in record.source_refs))
        return self.memory.create(
            layer=MemoryLayer.SEMANTIC,
            summary=summary,
            source_refs=merged_sources,
            metadata={
                "proposal_type": "semantic_compaction",
                "proposal_basis": basis,
                "proposal_basis_value": basis_value,
                "proposal_signature": f"{basis}:{basis_value}",
                "source_record_ids": source_record_ids,
                "compacted_from": source_record_ids,
                "topic_tags": merged_tags,
                "origin": "memory-review",
            },
            confidence=round(sum(record.confidence for record in records) / len(records), 3),
            status=RecordStatus.CONSTRAINED,
        )

    def _create_procedural_proposal(self, *, workflow: str, records: list[Any]) -> Any | None:
        source_record_ids = [record.record_id for record in records]
        existing = self._existing_proposal(
            layer=MemoryLayer.PROCEDURAL,
            proposal_type="procedural_dedup",
            source_record_ids=source_record_ids,
            discriminator_key="workflow",
            discriminator_value=workflow,
        )
        if existing is not None:
            return None
        canonical = sorted(
            records,
            key=lambda item: (-item.confidence, item.created_at or "", item.record_id),
        )[0]
        merged_sources = list(dict.fromkeys(ref for record in records for ref in record.source_refs))
        return self.memory.create(
            layer=MemoryLayer.PROCEDURAL,
            summary=f"Canonical procedural workflow for {workflow}.",
            source_refs=merged_sources,
            metadata={
                "proposal_type": "procedural_dedup",
                "workflow": workflow,
                "source_record_ids": source_record_ids,
                "canonical_record_id": canonical.record_id,
                "canonical_summary": canonical.summary,
                "canonical": False,
            },
            confidence=canonical.confidence,
            status=RecordStatus.CONSTRAINED,
        )

    def _confirm_profile_record(self, record: Any) -> Any:
        profile_key = str(record.metadata.get("profile_key", "")).strip()
        if not profile_key:
            raise RuntimeError(f"Profile proposal {record.record_id} is missing profile_key metadata.")
        active_records = self._matching_records_by_metadata(
            layer=MemoryLayer.PROFILE,
            statuses=(RecordStatus.ACTIVE,),
            key="profile_key",
            value=profile_key,
        )
        superseded_id = None
        for active in active_records:
            if active.record_id == record.record_id:
                continue
            if superseded_id is None:
                superseded_id = active.record_id
                self.memory.update_record(active.record_id, status=RecordStatus.SUPERSEDED)
            else:
                self.memory.update_record(active.record_id, status=RecordStatus.TOMBSTONED)
        return self.memory.update_record(record.record_id, status=RecordStatus.ACTIVE, supersedes=superseded_id)

    def _confirm_semantic_compaction(self, record: Any) -> Any:
        source_ids = [str(item) for item in record.metadata.get("source_record_ids", []) if str(item)]
        if len(source_ids) < 2:
            raise RuntimeError(f"Semantic compaction proposal {record.record_id} does not list enough source records.")
        for source_id in source_ids:
            self.memory.update_record(source_id, status=RecordStatus.SUPERSEDED)
        metadata = {**record.metadata, "origin": "memory-review", "compacted_from": source_ids}
        return self.memory.update_record(record.record_id, status=RecordStatus.ACTIVE, metadata=metadata, supersedes=source_ids[0])

    def _confirm_procedural_dedup(self, record: Any) -> Any:
        workflow = str(record.metadata.get("workflow", "")).strip()
        source_ids = [str(item) for item in record.metadata.get("source_record_ids", []) if str(item)]
        canonical_record_id = str(record.metadata.get("canonical_record_id", "")).strip()
        if not workflow or len(source_ids) < 2 or not canonical_record_id:
            raise RuntimeError(f"Procedural dedup proposal {record.record_id} is missing workflow metadata.")
        for source_id in source_ids:
            self.memory.update_record(source_id, status=RecordStatus.SUPERSEDED)
        metadata = {**record.metadata, "canonical": True}
        return self.memory.update_record(record.record_id, status=RecordStatus.ACTIVE, metadata=metadata, supersedes=canonical_record_id)

    def _plan_to_steps(self, *, run_id: str, plan: dict[str, Any], branch_name: str) -> list[RunStep]:
        steps: list[RunStep] = [
            RunStep(
                run_id=run_id,
                step_index=0,
                step_id="branch",
                summary=f"Create working branch {branch_name}",
                required_tier=PermissionTier.REPO_WRITE,
                action_name="git.create_branch",
                action_args={"branch_name": branch_name},
                verification={"branch_name": branch_name},
            )
        ]
        step_index = 1
        for operation in plan.get("file_operations", []):
            path = str(operation["path"])
            mode = str(operation.get("mode", "rewrite"))
            action_name = {
                "rewrite": "workspace.rewrite_file",
                "replace_text": "workspace.replace_text",
                "insert_after": "workspace.insert_after",
                "append_text": "workspace.append_text",
                "create_file": "workspace.create_file",
                "copy_file": "workspace.copy_file",
                "move_file": "workspace.move_file",
                "delete_file": "workspace.delete_file",
            }[mode]
            steps.append(
                RunStep(
                    run_id=run_id,
                    step_index=step_index,
                    step_id=f"edit-{step_index}",
                    summary=f"Apply {mode} to {path}",
                    required_tier=PermissionTier.REPO_WRITE,
                    action_name=action_name,
                    action_args={
                        "path": path,
                        "mode": mode,
                        "create_if_missing": bool(operation.get("create_if_missing", False)),
                        "source_path": str(operation.get("source_path", "")),
                        "instructions": str(operation["instructions"]),
                        "destructive": mode in {"move_file", "delete_file"},
                    },
                    verification={"path": path, "mode": mode},
                )
            )
            step_index += 1

        for command in plan.get("validation_commands", []):
            spec = self.task_validation_policy.resolve_command(str(command))
            steps.append(
                RunStep(
                    run_id=run_id,
                    step_index=step_index,
                    step_id=f"check-{step_index}-{spec.id}",
                    summary=f"Run validation {spec.id}",
                    required_tier=PermissionTier.OBSERVE,
                    action_name="workspace.run_validation",
                    action_args={"command_id": spec.id, "command": spec.command},
                    verification={
                        "expected_returncode": spec.expected_returncode,
                        "stdout_contains": list(spec.stdout_contains),
                        "stderr_contains": list(spec.stderr_contains),
                    },
                )
            )
            step_index += 1

        steps.append(
            RunStep(
                run_id=run_id,
                step_index=step_index,
                step_id="commit",
                summary="Commit planned repository changes",
                required_tier=PermissionTier.REPO_WRITE,
                action_name="git.commit_all",
                action_args={"message": str(plan["commit_message"])},
                verification={"worktree_clean": True},
            )
        )
        step_index += 1

        steps.append(
            RunStep(
                run_id=run_id,
                step_index=step_index,
                step_id="push",
                summary="Push branch to origin",
                required_tier=PermissionTier.EXTERNAL_WRITE,
                action_name="git.push_branch",
                action_args={"branch_name": branch_name, "remote": "origin"},
                verification={"branch_name": branch_name},
            )
        )
        step_index += 1

        pull_request = dict(plan["pull_request"])
        steps.append(
            RunStep(
                run_id=run_id,
                step_index=step_index,
                step_id="pull-request-preflight",
                summary="Inspect branch-scoped pull request before sync",
                required_tier=PermissionTier.OBSERVE,
                action_name="github.inspect_pull_request",
                action_args={
                    "head_branch": branch_name,
                    "base_branch": str(pull_request["base_branch"]),
                },
                verification={"expects_remote_target_state": ["none", "open-draft", "open-ready"]},
            )
        )
        step_index += 1
        steps.append(
            RunStep(
                run_id=run_id,
                step_index=step_index,
                step_id="pull-request",
                summary="Create or update draft pull request",
                required_tier=PermissionTier.EXTERNAL_WRITE,
                action_name="github.sync_pull_request",
                action_args={
                    "head_branch": branch_name,
                    "base_branch": str(pull_request["base_branch"]),
                    "title": str(pull_request["title"]),
                    "body": str(pull_request["body"]),
                },
                verification={"expects": "html_url"},
            )
        )
        step_index += 1

        issue_comment = plan.get("issue_comment")
        if isinstance(issue_comment, dict):
            steps.append(
                RunStep(
                    run_id=run_id,
                    step_index=step_index,
                    step_id="issue-preflight",
                    summary="Inspect target GitHub issue before comment sync",
                    required_tier=PermissionTier.OBSERVE,
                    action_name="github.inspect_issue",
                    action_args={
                        "issue_number": int(issue_comment["issue_number"]),
                        "dedupe_key": f"{run_id}:issue-comment",
                    },
                    verification={"expects_state": "open"},
                )
            )
            step_index += 1
            steps.append(
                RunStep(
                    run_id=run_id,
                    step_index=step_index,
                    step_id="issue-comment",
                    summary="Add related GitHub issue comment",
                    required_tier=PermissionTier.EXTERNAL_WRITE,
                    action_name="github.add_issue_comment",
                    action_args={
                        "issue_number": int(issue_comment["issue_number"]),
                        "body": str(issue_comment["body"]),
                    },
                    verification={"expects": "html_url"},
                )
            )
        return steps

    def _build_approvals(
        self,
        *,
        allow_repo_write: bool,
        allow_destructive_repo_write: bool,
        allow_external_write: bool,
    ) -> list[ApprovalGrant]:
        approvals: list[ApprovalGrant] = []
        if allow_repo_write:
            approvals.append(ApprovalGrant(tier=PermissionTier.REPO_WRITE, granted=True))
        if allow_destructive_repo_write:
            approvals.append(ApprovalGrant(tier=PermissionTier.DESTRUCTIVE_REPO_WRITE, granted=True))
        if allow_external_write:
            approvals.append(ApprovalGrant(tier=PermissionTier.EXTERNAL_WRITE, granted=True))
        return approvals

    @staticmethod
    def _build_auth_preflight_remediation(
        auth: dict[str, object],
        capabilities: dict[str, object],
    ) -> list[dict[str, object]]:
        remediation: list[dict[str, object]] = []
        if not bool(auth["openai_key_env_present"]):
            remediation.append(
                {
                    "code": "missing_openai_key",
                    "summary": "OPENAI_API_KEY is not configured for this shell.",
                    "blocks": [
                        "task planning with the live OpenAI provider",
                        "python tools/run_authenticated_smoke.py --provider openai",
                    ],
                    "next_steps": [
                        "Set OPENAI_API_KEY explicitly before task planning or OpenAI smoke checks.",
                    ],
                }
            )
        if not bool(auth["github_token_env_present"]):
            if bool(auth["gh_auth_logged_in"]):
                remediation.append(
                    {
                        "code": "gh_logged_in_but_not_bridged",
                        "summary": "`gh` is logged in, but Skylattice does not automatically use that login state.",
                        "blocks": [
                            "python tools/run_authenticated_smoke.py --provider github",
                            "python -m skylattice.cli radar scan --window weekly",
                            "python -m skylattice.cli radar schedule run --schedule weekly-github",
                        ],
                        "next_steps": [
                            "Run `python -m skylattice.cli doctor github-bridge --format json` to inspect an explicit bridge.",
                            "Run `python -m skylattice.cli doctor github-bridge --format env` only when you intentionally want copyable env exports.",
                        ],
                    }
                )
            else:
                remediation.append(
                    {
                        "code": "missing_github_token",
                        "summary": "GITHUB_TOKEN is not configured for this shell.",
                        "blocks": [
                            "python tools/run_authenticated_smoke.py --provider github",
                            "python -m skylattice.cli radar scan --window weekly",
                            "python -m skylattice.cli radar schedule run --schedule weekly-github",
                        ],
                        "next_steps": [
                            "Set GITHUB_TOKEN explicitly or run `gh auth login` and then bridge it explicitly.",
                        ],
                    }
                )
        if not bool(auth["repo_hint_effective"]):
            detected = str(auth.get("repo_hint_origin_detected") or "").strip()
            if detected:
                remediation.append(
                    {
                        "code": "origin_repo_detected_but_not_confirmed",
                        "summary": f"`origin` suggests `{detected}`, but Skylattice will not adopt it automatically.",
                        "blocks": [
                            "GitHub adapter initialization",
                            "radar discovery after token setup",
                        ],
                        "next_steps": [
                            "Export SKYLATTICE_GITHUB_REPOSITORY explicitly, or use the bridge helper to print an explicit repo hint.",
                        ],
                    }
                )
            else:
                remediation.append(
                    {
                        "code": "missing_repo_hint",
                        "summary": "No explicit GitHub repository hint is configured, and `origin` did not resolve to a GitHub slug.",
                        "blocks": [
                            "GitHub adapter initialization",
                            "radar discovery after token setup",
                        ],
                        "next_steps": [
                            "Set SKYLATTICE_GITHUB_REPOSITORY explicitly before running GitHub-backed features.",
                        ],
                    }
                )
        if not bool(capabilities["github_available"]) and bool(auth["github_token_env_present"]) and bool(auth["repo_hint_effective"]):
            remediation.append(
                {
                    "code": "github_runtime_unavailable",
                    "summary": "GitHub credentials look present, but the runtime still did not initialize the GitHub adapter.",
                    "blocks": [
                        "task GitHub sync steps",
                        "GitHub authenticated smoke",
                    ],
                    "next_steps": [
                        "Re-run `python -m skylattice.cli doctor auth` and inspect the effective repo hint and runtime capability matrix.",
                    ],
                }
            )
        return remediation

    def _build_branch_name(self, requested: str, run_id: str) -> str:
        slug = re.sub(r"[^a-z0-9-]+", "-", requested.lower()).strip("-") or "task"
        return f"codex/{slug[:30]}-{run_id[-6:]}"

    def _finalize_memory(self, run_id: str, *, success: bool) -> None:
        for record in self.memory.list_for_run(run_id):
            if record.layer is MemoryLayer.WORKING and record.status.value == "active":
                self.memory.rollback(record.record_id)
        run = self.run_repository.get_run(run_id)
        self.memory.create(
            layer=MemoryLayer.EPISODIC,
            summary=f"Run {run_id} {'completed' if success else 'ended with issues'}: {run.plan_summary or run.goal[:120]}",
            run_id=run_id,
            source_refs=[run.goal_source],
            metadata={"status": run.status.value, "branch_name": run.branch_name},
        )
        self.ledger.append(
            run_id=run_id,
            kind=EventKind.MEMORY,
            summary="Episodic memory recorded for run",
            actor="memory",
            payload={"run_id": run_id},
        )
        if success:
            self.memory.create(
                layer=MemoryLayer.PROCEDURAL,
                summary="Branch-edit-validate-commit-push-draft-PR workflow is available for repo ops tasks.",
                run_id=run_id,
                source_refs=[run_id],
                metadata={
                    "workflow": "repo-ops-github-triage",
                    "origin": "task",
                    "canonical": False,
                },
            )
            self.ledger.append(
                run_id=run_id,
                kind=EventKind.MEMORY,
                summary="Procedural memory refreshed from successful run",
                actor="memory",
                payload={"run_id": run_id},
            )

    def _load_goal(self, goal_input: str) -> tuple[str, str]:
        candidate = Path(goal_input)
        if candidate.exists() and candidate.is_file():
            return candidate.read_text(encoding="utf-8"), str(candidate)
        return goal_input, "inline"

    @staticmethod
    def _safe_call(func: Any, *, default: object) -> object:
        try:
            return func()
        except Exception:  # noqa: BLE001
            return default

    @staticmethod
    def _serialize_run(run: TaskRun) -> dict[str, object]:
        return {
            "run_id": run.run_id,
            "goal": run.goal,
            "goal_source": run.goal_source,
            "status": run.status.value,
            "plan_summary": run.plan_summary,
            "branch_name": run.branch_name,
            "current_step": run.current_step,
            "error": run.error,
            "result": run.result,
            "approvals": [
                {"tier": grant.tier.value, "granted": grant.granted, "actor": grant.actor}
                for grant in run.approvals
            ],
            "created_at": run.created_at,
            "updated_at": run.updated_at,
        }

    @staticmethod
    def _serialize_step(step: RunStep) -> dict[str, object]:
        return {
            "step_index": step.step_index,
            "step_id": step.step_id,
            "summary": step.summary,
            "required_tier": step.required_tier.value,
            "action_name": step.action_name,
            "action_args": step.action_args,
            "verification": step.verification,
            "status": step.status.value,
            "result": step.result,
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
