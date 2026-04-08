from __future__ import annotations

import json
import subprocess
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from skylattice.actions import GitAdapter
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
        payload = {
            "number": 1,
            "html_url": "https://github.com/example/skylattice/pull/1",
            "head_branch": head_branch,
            "base_branch": base_branch,
            "title": title,
            "body": body,
        }
        self.pull_requests.append(payload)
        return payload

    def add_issue_comment(self, *, issue_number: int, body: str) -> dict[str, object]:
        payload = {
            "issue_number": issue_number,
            "body": body,
            "html_url": f"https://github.com/example/skylattice/issues/{issue_number}#issuecomment-1",
        }
        self.comments.append(payload)
        return payload


class LocalPushGitAdapter:
    def __init__(self, repo_root: Path) -> None:
        self.delegate = GitAdapter(repo_root)
        self.push_calls: list[dict[str, str]] = []

    def __getattr__(self, name: str):
        return getattr(self.delegate, name)

    def push(self, branch_name: str, remote: str = "origin") -> str:
        self.push_calls.append({"branch_name": branch_name, "remote": remote})
        return branch_name


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _run(command: list[str], cwd: Path) -> str:
    completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=True)
    return completed.stdout


def create_temp_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()

    _write(
        repo / "configs" / "agent" / "defaults.yaml",
        """
agent:
  id: skylattice
  codename: skylattice
  version: 0.1.0
  owner: primary-user
user_model:
  user_id: primary-user
  display_name: owner
  timezone: Asia/Shanghai
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
  remote_ledger: github.com/example/skylattice
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


def test_health_and_doctor_reports() -> None:
    report = build_doctor_report()
    client = TestClient(app)

    health = client.get("/health")
    kernel = client.get("/kernel/summary")

    assert report["status"] == "ok"
    assert health.status_code == 200
    assert kernel.status_code == 200
    assert kernel.json()["agent"]["agent_id"] == "skylattice"


def test_doctor_command_outputs_runtime_json() -> None:
    buffer = StringIO()
    with redirect_stdout(buffer):
        exit_code = main(["doctor"])

    payload = json.loads(buffer.getvalue())
    assert exit_code == 0
    assert payload["runtime"]["db_path"].endswith("skylattice.sqlite3")


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
    provider = FakeProvider(plan=build_fake_plan(), file_outputs={"README.md": "# Temp Repo\n\nInitial content.\n\n## Task Agent MVP\n\nThis repo now has an executable task-agent MVP.\n"})
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
    assert any(record["layer"] == "episodic" for record in details["memory"])
    assert any(record["layer"] == "procedural" for record in details["memory"])
    assert any(record["layer"] == "working" and record["status"] == "tombstoned" for record in details["memory"])


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
    finally:
        app.dependency_overrides.clear()

    assert run_response.status_code == 200
    assert run_response.json()["run_id"] == run.run_id
    assert event_response.status_code == 200
    assert any(event["kind"] == "run" for event in event_response.json())
    assert memory_response.status_code == 200
    assert any(record["layer"] == "working" for record in memory_response.json())