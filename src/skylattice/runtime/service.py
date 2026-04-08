"""Executable task-agent runtime service."""

from __future__ import annotations

import os
import re
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any

from skylattice.actions import GitAdapter, GitHubAdapter, RepoWorkspaceAdapter
from skylattice.governance import GovernanceDecision, GovernanceGate, GovernanceRequest, PermissionTier
from skylattice.kernel import build_kernel_summary, load_kernel_config
from skylattice.ledger import EventKind, LedgerStore
from skylattice.memory import MemoryLayer, SQLiteMemoryRepository
from skylattice.planning import TaskPlanner
from skylattice.providers import OpenAIProvider
from skylattice.radar import GitHubRadarSource, RadarRepository, RadarService
from skylattice.runtime.models import RunStatus, RunStep, RunStepStatus, TaskRun

from .db import RuntimeDatabase
from .models import ApprovalGrant
from .repositories import RunRepository


class TaskAgentService:
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
        workspace = RepoWorkspaceAdapter(root)
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
        repo_context = self._build_repo_context()
        plan = self.planner.create_plan(goal=goal_text, repo_context=repo_context)
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
                status = RunStatus.HALTED if step.required_tier in {PermissionTier.REPO_WRITE, PermissionTier.EXTERNAL_WRITE} else RunStatus.FAILED
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

        if step.action_name == "workspace.edit_file":
            if self.provider is None:
                raise RuntimeError("No content provider is available for file edits")
            path = str(step.action_args["path"])
            current_content = self.workspace.read_text(path)
            updated = self.provider.rewrite_file(
                goal=run.goal,
                path=path,
                current_content=current_content,
                instructions=str(step.action_args["instructions"]),
                plan_summary=run.plan_summary,
                repo_context=self._build_repo_context(),
            )
            written = self.workspace.write_text(
                path,
                updated,
                create_if_missing=bool(step.action_args.get("create_if_missing", False)),
            )
            return {"path": written, "artifact_refs": [written]}

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

    def _verify_step(self, step: RunStep, result: dict[str, object]) -> bool:
        if step.action_name == "workspace.run_check":
            if int(result.get("returncode", 1)) != 0:
                raise RuntimeError(f"Check failed: {result.get('command')}")
            return True
        if step.action_name == "workspace.edit_file":
            path = step.action_args["path"]
            if not self.workspace.read_text(str(path)).strip():
                raise RuntimeError(f"Edited file is empty: {path}")
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

    def _build_repo_context(self) -> dict[str, object]:
        files = self.workspace.list_files(limit=120)
        context = {
            "repo_root": ".",
            "current_branch": self._safe_call(self.git.current_branch, default="main"),
            "remote_url": self._safe_call(self.git.remote_url, default=""),
            "files": files,
        }
        for candidate in ("README.md", "docs/roadmap.md", "docs/architecture.md"):
            if candidate in files:
                context[candidate] = self.workspace.read_text(candidate)[:4000]
        return context

    def _display_path(self, path: Path) -> str:
        try:
            relative = path.relative_to(self.repo_root)
        except ValueError:
            return str(path)
        return relative.as_posix() if relative.parts else "."

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
            steps.append(
                RunStep(
                    run_id=run_id,
                    step_index=step_index,
                    step_id=f"edit-{step_index}",
                    summary=f"Edit {path}",
                    required_tier=PermissionTier.REPO_WRITE,
                    action_name="workspace.edit_file",
                    action_args={
                        "path": path,
                        "create_if_missing": bool(operation.get("create_if_missing", False)),
                        "instructions": str(operation["instructions"]),
                    },
                    verification={"path": path},
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
                action_args={"message": str(plan["commit_message"])} ,
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
                metadata={"workflow": "repo-ops-github-triage"},
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
        }
