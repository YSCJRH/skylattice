from __future__ import annotations

import json
import subprocess
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from skylattice.actions import GitAdapter, RepoWorkspaceAdapter
from skylattice.api import app, get_task_agent_service
from skylattice.cli import build_doctor_report, main
from skylattice.governance import GovernanceDecision, GovernanceGate, GovernanceRequest, PermissionTier
from skylattice.kernel import load_kernel_config
from skylattice.memory import ConflictStrategy, MemoryLayer, default_memory_policies
from skylattice.providers import FakeProvider
from skylattice.runtime import TaskAgentService


class FakeGitHubAdapter:
    def __init__(self) -> None:
        self.pull_requests: list[dict[str, object]] = []
        self.comments: list[dict[str, object]] = []

    def create_or_update_draft_pr(
        self,
        *,
        head_branch: str,
        base_branch: str,
        title: str,
        body: str,
    ) -> dict[str, object]:
        for payload in self.pull_requests:
            if payload["head_branch"] == head_branch:
                payload.update({"base_branch": base_branch, "title": title, "body": body})
                return {
                    **payload,
                    "reused": True,
                    "sync_mode": "update",
                    "dedupe_key": head_branch,
                }
        payload = {
            "number": len(self.pull_requests) + 1,
            "html_url": f"https://github.com/example/skylattice/pull/{len(self.pull_requests) + 1}",
            "head_branch": head_branch,
            "base_branch": base_branch,
            "title": title,
            "body": body,
        }
        self.pull_requests.append(payload)
        return {
            **payload,
            "reused": False,
            "sync_mode": "create",
            "dedupe_key": head_branch,
        }

    def add_issue_comment(self, *, issue_number: int, body: str) -> dict[str, object]:
        payload = {
            "issue_number": issue_number,
            "body": body,
            "html_url": f"https://github.com/example/skylattice/issues/{issue_number}#issuecomment-{len(self.comments) + 1}",
        }
        self.comments.append(payload)
        return payload

    def list_issue_comments(self, *, issue_number: int, per_page: int = 100) -> list[dict[str, object]]:
        return [comment for comment in self.comments if int(comment["issue_number"]) == issue_number][:per_page]

    def create_or_reuse_issue_comment(self, *, issue_number: int, body: str, dedupe_key: str) -> dict[str, object]:
        marker = f"<!-- skylattice:{dedupe_key} -->"
        for payload in self.list_issue_comments(issue_number=issue_number):
            if marker in str(payload["body"]):
                return {
                    **payload,
                    "reused": True,
                    "sync_mode": "reuse",
                    "dedupe_key": dedupe_key,
                }
        payload = self.add_issue_comment(issue_number=issue_number, body=f"{body}\n\n{marker}")
        return {
            **payload,
            "reused": False,
            "sync_mode": "create",
            "dedupe_key": dedupe_key,
        }


class LocalPushGitAdapter:
    def __init__(self, repo_root: Path) -> None:
        self.delegate = GitAdapter(repo_root)
        self.push_calls: list[dict[str, str]] = []

    def __getattr__(self, name: str):
        return getattr(self.delegate, name)

    def push(self, branch_name: str, remote: str = "origin") -> str:
        self.push_calls.append({"branch_name": branch_name, "remote": remote})
        return branch_name


class FlakyPushGitAdapter(LocalPushGitAdapter):
    def __init__(self, repo_root: Path) -> None:
        super().__init__(repo_root)
        self.failures_remaining = 1

    def push(self, branch_name: str, remote: str = "origin") -> str:
        self.push_calls.append({"branch_name": branch_name, "remote": remote})
        if self.failures_remaining > 0:
            self.failures_remaining -= 1
            raise RuntimeError("simulated push failure")
        return branch_name


class FlakyIssueCommentGitHubAdapter(FakeGitHubAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.failures_remaining = 1

    def create_or_reuse_issue_comment(self, *, issue_number: int, body: str, dedupe_key: str) -> dict[str, object]:
        marker = f"<!-- skylattice:{dedupe_key} -->"
        existing = [
            comment
            for comment in self.list_issue_comments(issue_number=issue_number)
            if marker in str(comment["body"])
        ]
        if not existing and self.failures_remaining > 0:
            self.failures_remaining -= 1
            super().create_or_reuse_issue_comment(issue_number=issue_number, body=body, dedupe_key=dedupe_key)
            raise RuntimeError("simulated issue comment failure")
        return super().create_or_reuse_issue_comment(issue_number=issue_number, body=body, dedupe_key=dedupe_key)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _run(command: list[str], cwd: Path) -> str:
    completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=True)
    return completed.stdout


def create_temp_repo(tmp_path: Path, validation_commands: tuple[str, ...] | None = None) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    commands = validation_commands or ("python -m pytest -q", "python -m compileall src/skylattice", "python -m skylattice.cli doctor", "git status --short")

    _write(
        repo / "configs" / "agent" / "defaults.yaml",
        """
agent:
  id: skylattice
  codename: skylattice
  version: 0.1.0
  owner: local-user
user_model:
  user_id: local-user
  display_name: user
  timezone: UTC
  interaction_style: concise
relationship:
  role: personal evolvable agent
  promises:
    - protect long-term user interests
  escalation_default: ask-before-repo-or-external-write
mission:
  summary: test mission
  constitution:
    - Local-first runtime before remote convenience.
runtime:
  mode: bootstrap
  freeze_mode: false
  active_plan: null
  memory_home: .local/memory
  remote_ledger: ""
  autonomy_mode: proactive-low-risk
adapters:
  shell: planned
""".strip(),
    )
    _write(
        repo / "configs" / "policies" / "governance.yaml",
        """
freeze_mode: false
auto_approve:
  - observe
  - local-safe-write
approval_required:
  - repo-write
  - external-write
  - self-modify
local_safe_roots:
  - .local/work
  - .local/logs
  - .local/state
destructive_keywords:
  - delete
  - reset
""".strip(),
    )
    _write(
        repo / "configs" / "task" / "validation.yaml",
        "runner: powershell\n\nallowed_commands:\n"
        + "".join(f"  - {command}\n" for command in commands),
    )
    _write(repo / "README.md", "# Temp Repo\n\nInitial content.\n")

    _run(["git", "init", "-b", "main"], repo)
    _run(["git", "config", "user.email", "tests@example.com"], repo)
    _run(["git", "config", "user.name", "Skylattice Tests"], repo)
    _run(["git", "add", "--all"], repo)
    _run(["git", "commit", "-m", "initial"], repo)
    return repo


def build_fake_plan() -> dict[str, object]:
    return {
        "summary": "Refresh README and open a draft PR.",
        "branch_name": "readme-refresh",
        "file_operations": [
            {
                "path": "README.md",
                "mode": "rewrite",
                "create_if_missing": False,
                "instructions": "Add one section describing the task agent MVP.",
            }
        ],
        "validation_commands": ["git status --short"],
        "commit_message": "docs: refresh README for task agent MVP",
        "pull_request": {
            "title": "docs: refresh README for task agent MVP",
            "body": "This updates README.md to describe the executable task-agent MVP.",
            "base_branch": "main",
        },
    }


def build_multimode_plan() -> dict[str, object]:
    return {
        "summary": "Refresh README with deterministic text edit primitives.",
        "branch_name": "readme-multimode",
        "file_operations": [
            {
                "path": "README.md",
                "mode": "replace_text",
                "create_if_missing": False,
                "instructions": "Replace the intro sentence with deterministic edit wording.",
            },
            {
                "path": "README.md",
                "mode": "insert_after",
                "create_if_missing": False,
                "instructions": "Insert a Task Agent MVP section after the intro paragraph.",
            },
            {
                "path": "README.md",
                "mode": "append_text",
                "create_if_missing": False,
                "instructions": "Append a note about tracked validation commands.",
            },
        ],
        "validation_commands": ["git diff --stat"],
        "commit_message": "docs: exercise deterministic task-agent edits",
        "pull_request": {
            "title": "docs: exercise deterministic task-agent edits",
            "body": "This uses replace_text, insert_after, and append_text in one task run.",
            "base_branch": "main",
        },
    }


def build_issue_comment_plan() -> dict[str, object]:
    plan = build_fake_plan()
    plan["issue_comment"] = {
        "issue_number": 7,
        "body": "Skylattice prepared a governed repo update and draft PR.",
    }
    return plan


def test_health_and_doctor_reports() -> None:
    report = build_doctor_report()
    client = TestClient(app)

    health = client.get("/health")
    kernel = client.get("/kernel/summary")

    assert report["status"] == "ok"
    assert health.status_code == 200
    assert kernel.status_code == 200
    assert kernel.json()["agent"]["agent_id"] == "skylattice"
    assert report["kernel"]["paths"]["repo_root"] == "."


def test_doctor_command_outputs_runtime_json() -> None:
    buffer = StringIO()
    with redirect_stdout(buffer):
        exit_code = main(["doctor"])

    payload = json.loads(buffer.getvalue())
    assert exit_code == 0
    assert payload["runtime"]["db_path"] == ".local/state/skylattice.sqlite3"
    assert payload["runtime"]["validation_config"] == "configs/task/validation.yaml"
    assert payload["kernel"]["paths"]["repo_root"] == "."


def test_kernel_config_reads_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SKYLATTICE_USER_TIMEZONE", "UTC")
    config = load_kernel_config()
    assert config.user.timezone == "UTC"


def test_governance_requires_approval_for_repo_write() -> None:
    gate = GovernanceGate.from_repo()
    denied = gate.evaluate(GovernanceRequest(tier=PermissionTier.REPO_WRITE, summary="update tracked README"))
    approved = gate.evaluate(
        GovernanceRequest(
            tier=PermissionTier.REPO_WRITE,
            summary="update tracked README",
            user_approved=True,
        )
    )

    assert denied.decision is GovernanceDecision.DENIED
    assert approved.decision is GovernanceDecision.APPROVED


def test_memory_policy_covers_all_layers() -> None:
    policies = default_memory_policies()

    assert set(policies) == {
        MemoryLayer.PROFILE,
        MemoryLayer.EPISODIC,
        MemoryLayer.SEMANTIC,
        MemoryLayer.PROCEDURAL,
        MemoryLayer.WORKING,
    }
    assert policies[MemoryLayer.PROFILE].conflict_resolution is ConflictStrategy.SUPERSEDE
    assert policies[MemoryLayer.WORKING].rollback_mechanism.startswith("Clear")


def test_repo_workspace_supports_deterministic_edit_primitives(tmp_path: Path) -> None:
    repo = create_temp_repo(tmp_path)
    workspace = RepoWorkspaceAdapter(repo, allowed_check_commands=("git status --short",))

    workspace.replace_text("README.md", "Initial content.", "Initial content with deterministic edits.")
    workspace.insert_after(
        "README.md",
        "Initial content with deterministic edits.",
        "\n\n## Task Agent MVP\n\nDeterministic text edits are available.\n",
    )
    workspace.append_text("README.md", "\nValidation commands are tracked.\n")

    updated = (repo / "README.md").read_text(encoding="utf-8")
    assert "Task Agent MVP" in updated
    assert "Validation commands are tracked." in updated

    _write(repo / "notes.md", "alpha\nbeta\nalpha\n")
    with pytest.raises(ValueError, match="matched 2 times"):
        workspace.replace_text("notes.md", "alpha", "ALPHA")
    with pytest.raises(ValueError, match="Target text not found"):
        workspace.replace_text("notes.md", "gamma", "GAMMA")
    with pytest.raises(ValueError, match="Anchor text not found"):
        workspace.insert_after("notes.md", "missing", "\nextra")


def test_task_run_waits_for_approval(tmp_path: Path) -> None:
    repo = create_temp_repo(tmp_path)
    provider = FakeProvider(plan=build_fake_plan(), file_outputs={"README.md": "# Temp Repo\n\nTask agent MVP.\n"})
    service = TaskAgentService.from_repo(repo_root=repo, provider=provider, github_adapter=FakeGitHubAdapter())
    service.git = LocalPushGitAdapter(repo)

    run = service.run_task(goal_input="Refresh the README and prepare a PR.")
    details = service.inspect_run(run.run_id)

    assert run.status.value == "waiting_approval"
    assert details["run"]["status"] == "waiting_approval"
    assert details["steps"][0]["status"] == "blocked"
    assert any(event["kind"] == "approval" for event in details["events"])


def test_task_resume_executes_branch_push_and_pr(tmp_path: Path) -> None:
    repo = create_temp_repo(tmp_path)
    provider = FakeProvider(
        plan=build_fake_plan(),
        file_outputs={"README.md": "# Temp Repo\n\nInitial content.\n\n## Task Agent MVP\n\nThis repo now has an executable task-agent MVP.\n"},
    )
    github = FakeGitHubAdapter()
    service = TaskAgentService.from_repo(repo_root=repo, provider=provider, github_adapter=github)
    fake_git = LocalPushGitAdapter(repo)
    service.git = fake_git

    created = service.run_task(goal_input="Refresh the README and prepare a PR.")
    completed = service.resume_task(
        run_id=created.run_id,
        allow_repo_write=True,
        allow_external_write=True,
    )
    details = service.inspect_run(completed.run_id)

    assert completed.status.value == "completed"
    assert "Task Agent MVP" in (repo / "README.md").read_text(encoding="utf-8")
    assert _run(["git", "branch", "--show-current"], repo).strip().startswith("codex/readme-refresh")
    assert fake_git.push_calls[0]["branch_name"].startswith("codex/readme-refresh")
    assert github.pull_requests[0]["html_url"].endswith("/pull/1")
    assert details["steps"][1]["action_name"] == "workspace.rewrite_file"
    assert details["steps"][1]["result"]["materialized_edit"]["mode"] == "rewrite"
    assert any(record["layer"] == "episodic" for record in details["memory"])
    assert any(record["layer"] == "procedural" for record in details["memory"])
    assert any(record["layer"] == "working" and record["status"] == "tombstoned" for record in details["memory"])
    assert details["recovery"]["status"] == "completed"


def test_task_run_supports_mixed_edit_modes_and_records_materialized_payloads(tmp_path: Path) -> None:
    repo = create_temp_repo(tmp_path, validation_commands=("git diff --stat",))
    provider = FakeProvider(
        plan=build_multimode_plan(),
        edit_outputs={
            "README.md::replace_text": {
                "mode": "replace_text",
                "target_text": "Initial content.",
                "replacement_text": "Initial content with deterministic edits.",
                "expected_occurrences": 1,
            },
            "README.md::insert_after": {
                "mode": "insert_after",
                "anchor_text": "Initial content with deterministic edits.",
                "insert_text": "\n\n## Task Agent MVP\n\nThis repo now supports deterministic text edit primitives.\n",
                "expected_occurrences": 1,
            },
            "README.md::append_text": {
                "mode": "append_text",
                "append_text": "\nValidation commands are tracked in repo config.\n",
            },
        },
    )
    github = FakeGitHubAdapter()
    service = TaskAgentService.from_repo(repo_root=repo, provider=provider, github_adapter=github)
    fake_git = LocalPushGitAdapter(repo)
    service.git = fake_git

    completed = service.run_task(
        goal_input="Refresh the README with deterministic edit primitives.",
        allow_repo_write=True,
        allow_external_write=True,
    )
    details = service.inspect_run(completed.run_id)
    readme = (repo / "README.md").read_text(encoding="utf-8")

    assert completed.status.value == "completed"
    assert "deterministic text edit primitives" in readme
    assert "Validation commands are tracked in repo config." in readme
    assert [step["action_name"] for step in details["steps"][1:4]] == [
        "workspace.replace_text",
        "workspace.insert_after",
        "workspace.append_text",
    ]
    assert details["steps"][4]["action_name"] == "workspace.run_check"
    assert details["steps"][4]["action_args"]["command"] == "git diff --stat"
    assert all("materialized_edit" in step["result"] for step in details["steps"][1:4])
    assert details["steps"][1]["result"]["materialized_edit"]["target_text"] == "Initial content."
    assert github.pull_requests[0]["title"] == "docs: exercise deterministic task-agent edits"


def test_halted_push_reports_recovery_and_resumes(tmp_path: Path) -> None:
    repo = create_temp_repo(tmp_path)
    provider = FakeProvider(
        plan=build_fake_plan(),
        file_outputs={"README.md": "# Temp Repo\n\nInitial content.\n\n## Recovery\n\nPush retry test.\n"},
    )
    github = FakeGitHubAdapter()
    service = TaskAgentService.from_repo(repo_root=repo, provider=provider, github_adapter=github)
    flaky_git = FlakyPushGitAdapter(repo)
    service.git = flaky_git

    halted = service.run_task(
        goal_input="Refresh the README and prepare a PR.",
        allow_repo_write=True,
        allow_external_write=True,
    )
    halted_details = service.inspect_run(halted.run_id)

    assert halted.status.value == "halted"
    assert halted_details["recovery"]["resumable"] is True
    assert halted_details["recovery"]["next_step_id"] == "push"
    assert halted_details["recovery"]["recommended_allows"] == ["external-write"]
    assert halted_details["steps"][4]["result"]["attempt_count"] == 1
    assert halted_details["steps"][4]["result"]["last_error"] == "simulated push failure"

    resumed = service.resume_task(run_id=halted.run_id, allow_external_write=True)
    resumed_details = service.inspect_run(resumed.run_id)

    assert resumed.status.value == "completed"
    assert resumed_details["steps"][4]["result"]["attempt_count"] == 2
    assert resumed_details["steps"][4]["result"]["previous_errors"] == ["simulated push failure"]
    assert resumed_details["recovery"]["status"] == "completed"


def test_issue_comment_resume_reuses_existing_comment(tmp_path: Path) -> None:
    repo = create_temp_repo(tmp_path)
    provider = FakeProvider(
        plan=build_issue_comment_plan(),
        file_outputs={"README.md": "# Temp Repo\n\nInitial content.\n\n## Recovery\n\nIssue comment retry test.\n"},
    )
    github = FlakyIssueCommentGitHubAdapter()
    service = TaskAgentService.from_repo(repo_root=repo, provider=provider, github_adapter=github)
    service.git = LocalPushGitAdapter(repo)

    halted = service.run_task(
        goal_input="Refresh the README, prepare a PR, and leave an issue comment.",
        allow_repo_write=True,
        allow_external_write=True,
    )
    halted_details = service.inspect_run(halted.run_id)

    assert halted.status.value == "halted"
    assert halted_details["recovery"]["next_step_id"] == "issue-comment"
    assert halted_details["recovery"]["side_effect_risk"] == "medium"
    assert len(github.comments) == 1

    resumed = service.resume_task(run_id=halted.run_id, allow_external_write=True)
    resumed_details = service.inspect_run(resumed.run_id)

    assert resumed.status.value == "completed"
    assert len(github.comments) == 1
    assert resumed_details["steps"][-1]["result"]["reused"] is True
    assert resumed_details["steps"][-1]["result"]["sync_mode"] == "reuse"
    assert resumed_details["steps"][-1]["result"]["attempt_count"] == 2


def test_task_validation_commands_come_from_tracked_config(tmp_path: Path) -> None:
    repo = create_temp_repo(tmp_path, validation_commands=("git diff --stat",))
    service = TaskAgentService.from_repo(repo_root=repo)

    assert service.workspace.run_check("git diff --stat")["returncode"] == 0
    with pytest.raises(ValueError, match="Command not allowed"):
        service.workspace.run_check("git status --short")


def test_api_returns_run_events_and_memory(tmp_path: Path) -> None:
    repo = create_temp_repo(tmp_path)
    provider = FakeProvider(plan=build_fake_plan(), file_outputs={"README.md": "# Temp Repo\n\nTask agent API check.\n"})
    service = TaskAgentService.from_repo(repo_root=repo, provider=provider, github_adapter=FakeGitHubAdapter())
    service.git = LocalPushGitAdapter(repo)
    run = service.run_task(goal_input="Refresh the README and prepare a PR.")

    app.dependency_overrides[get_task_agent_service] = lambda: service
    client = TestClient(app)
    try:
        run_response = client.get(f"/runs/{run.run_id}")
        event_response = client.get(f"/runs/{run.run_id}/events")
        memory_response = client.get(f"/runs/{run.run_id}/memory")
        recovery_response = client.get(f"/runs/{run.run_id}/recovery")
    finally:
        app.dependency_overrides.clear()

    assert run_response.status_code == 200
    assert run_response.json()["run_id"] == run.run_id
    assert event_response.status_code == 200
    assert any(event["kind"] == "run" for event in event_response.json())
    assert memory_response.status_code == 200
    assert recovery_response.status_code == 200
    assert recovery_response.json()["status"] in {"awaiting_approval", "completed"}
    assert any(record["layer"] == "working" for record in memory_response.json())
