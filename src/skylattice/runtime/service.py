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
from skylattice.radar import GitHubRadarSource, RadarRepository, RadarService
from skylattice.runtime.models import RunStatus, RunStep, RunStepStatus, TaskRun

from .db import RuntimeDatabase
from .models import ApprovalGrant
from .repositories import RunRepository
from .task_config import TaskValidationPolicy, load_task_validation_policy


class TaskAgentService:
    MEMORY_CONTEXT_LIMIT = 3

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
        radar_source: GitHubRadarSource | None = None,
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
            },
            "radar": self.radar.state_snapshot(),
        }

    def run_task(
        self,
        *,
        goal_input: str,
        allow_repo_write: bool = False,
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
            allowed_validation_commands=self.task_validation_policy.allowed_commands,
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
            self._build_approvals(allow_repo_write=allow_repo_write, allow_external_write=allow_external_write),
        )
        return self._execute_until_blocked(run_id)

    def resume_task(
        self,
        *,
        run_id: str,
        allow_repo_write: bool = False,
        allow_external_write: bool = False,
    ) -> TaskRun:
        self.run_repository.grant_approvals(
            run_id,
            self._build_approvals(allow_repo_write=allow_repo_write, allow_external_write=allow_external_write),
        )
        self.ledger.append(
            run_id=run_id,
            kind=EventKind.APPROVAL,
            summary="Approvals updated for run",
            actor="operator",
            payload={
                "repo_write": allow_repo_write,
                "external_write": allow_external_write,
            },
        )
        return self._execute_until_blocked(run_id)

    def get_run(self, run_id: str) -> TaskRun:
        return self.run_repository.get_run(run_id)

    def inspect_run(self, run_id: str) -> dict[str, object]:
        run = self.run_repository.get_run(run_id)
        return {
            "run": self._serialize_run(run),
            "steps": [self._serialize_step(step) for step in self.run_repository.list_steps(run_id)],
            "events": [self._serialize_event(event) for event in self.ledger.list_for_run(run_id)],
            "memory": [self._serialize_memory(record) for record in self.memory.list_for_run(run_id)],
        }

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
            outcome = self.governance.evaluate(
                GovernanceRequest(
                    tier=step.required_tier,
                    summary=step.summary,
                    target_path=str(step.action_args.get("path", "")) or None,
                    destructive=False,
                    user_approved=bool(approved and approved.granted),
                )
            )
            if outcome.decision is GovernanceDecision.DENIED:
                self.run_repository.update_status(run_id, RunStatus.WAITING_APPROVAL, error=outcome.reason)
                blocked_step = RunStep(
                    **{**asdict(step), "status": RunStepStatus.BLOCKED, "result": {"reason": outcome.reason}}
                )
                self.run_repository.update_step(blocked_step)
                self.ledger.append(
                    run_id=run_id,
                    kind=EventKind.APPROVAL,
                    summary=f"Run paused before step {step.step_id}",
                    actor="governance",
                    payload={"reason": outcome.reason, "required_tier": step.required_tier.value},
                )
                return self.run_repository.get_run(run_id)

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
                failed_step = RunStep(
                    **{**asdict(step), "status": RunStepStatus.FAILED, "result": {"error": str(exc)}}
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

            verified_step = RunStep(
                **{**asdict(step), "status": RunStepStatus.VERIFIED, "result": {**result, "verified": verified}}
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

        if step.action_name in {"workspace.edit_file", "workspace.rewrite_file"}:
            return self._execute_rewrite_step(run, step)

        if step.action_name in {"workspace.replace_text", "workspace.insert_after", "workspace.append_text"}:
            return self._execute_materialized_edit_step(run, step)

        if step.action_name == "workspace.run_check":
            return self.workspace.run_check(str(step.action_args["command"]))

        if step.action_name == "git.commit_all":
            self.git.add_all()
            message = self.git.commit(str(step.action_args["message"]))
            return {"message": message}

        if step.action_name == "git.push_branch":
            branch_name = str(step.action_args["branch_name"])
            pushed = self.git.push(branch_name, remote=str(step.action_args.get("remote", "origin")))
            return {"branch_name": pushed}

        if step.action_name == "github.sync_pull_request":
            if self.github is None:
                raise RuntimeError("GitHub adapter is not configured")
            response = self.github.create_or_update_draft_pr(
                head_branch=str(step.action_args["head_branch"]),
                base_branch=str(step.action_args["base_branch"]),
                title=str(step.action_args["title"]),
                body=str(step.action_args["body"]),
            )
            return {
                "number": response.get("number"),
                "html_url": response.get("html_url"),
                "artifact_refs": [str(response.get("html_url", ""))] if response.get("html_url") else [],
            }

        if step.action_name == "github.add_issue_comment":
            if self.github is None:
                raise RuntimeError("GitHub adapter is not configured")
            response = self.github.add_issue_comment(
                issue_number=int(step.action_args["issue_number"]),
                body=str(step.action_args["body"]),
            )
            return {
                "html_url": response.get("html_url"),
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
        written = self.workspace.apply_materialized_edit(
            path,
            payload,
            create_if_missing=bool(step.action_args.get("create_if_missing", False)),
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
            "artifact_refs": [written],
            "materialized_edit": payload,
            "verification_metadata": {
                "content_length": len(self.workspace.read_text(path)),
                "expected_occurrences": payload.get("expected_occurrences"),
            },
        }

    def _verify_step(self, step: RunStep, result: dict[str, object]) -> bool:
        if step.action_name == "workspace.run_check":
            if int(result.get("returncode", 1)) != 0:
                raise RuntimeError(f"Check failed: {result.get('command')}")
            return True
        if step.action_name in {
            "workspace.edit_file",
            "workspace.rewrite_file",
            "workspace.replace_text",
            "workspace.insert_after",
            "workspace.append_text",
        }:
            path = step.action_args["path"]
            if not self.workspace.read_text(str(path)).strip():
                raise RuntimeError(f"Edited file is empty: {path}")
            if "materialized_edit" not in result:
                raise RuntimeError(f"Edit step did not record a materialized payload: {path}")
            return True
        if step.action_name == "git.commit_all":
            if self.git.status_porcelain().strip():
                raise RuntimeError("Worktree is still dirty after commit")
            return True
        if step.action_name == "github.sync_pull_request":
            if not result.get("html_url"):
                raise RuntimeError("GitHub PR sync did not return html_url")
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
            "supported_edit_modes": ["rewrite", "replace_text", "insert_after", "append_text"],
            "memory_context": self._memory_context_for_goal(goal_text),
        }
        for candidate in ("README.md", "docs/roadmap.md", "docs/architecture.md"):
            if candidate in files:
                context[candidate] = self.workspace.read_text(candidate)[:4000]
        return context

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
                        "instructions": str(operation["instructions"]),
                    },
                    verification={"path": path, "mode": mode},
                )
            )
            step_index += 1

        for command in plan.get("validation_commands", []):
            steps.append(
                RunStep(
                    run_id=run_id,
                    step_index=step_index,
                    step_id=f"check-{step_index}",
                    summary=f"Run check {command}",
                    required_tier=PermissionTier.OBSERVE,
                    action_name="workspace.run_check",
                    action_args={"command": str(command)},
                    verification={"returncode": 0},
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

    def _build_approvals(self, *, allow_repo_write: bool, allow_external_write: bool) -> list[ApprovalGrant]:
        approvals: list[ApprovalGrant] = []
        if allow_repo_write:
            approvals.append(ApprovalGrant(tier=PermissionTier.REPO_WRITE, granted=True))
        if allow_external_write:
            approvals.append(ApprovalGrant(tier=PermissionTier.EXTERNAL_WRITE, granted=True))
        return approvals

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
