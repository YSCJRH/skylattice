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
from skylattice.runtime import TaskAgentService, load_task_validation_policy


class FakeGitHubRepoRef:
    slug = "example/skylattice"


class FakeGitHubAdapter:
    def __init__(self) -> None:
        self.repo = FakeGitHubRepoRef()
        self.pull_requests: list[dict[str, object]] = []
        self.comments: list[dict[str, object]] = []
        self.issues: dict[int, dict[str, object]] = {
            7: {
                "number": 7,
                "title": "Tracked issue for tests",
                "state": "open",
                "html_url": "https://github.com/example/skylattice/issues/7",
            }
        }

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

    def get_issue(self, issue_number: int) -> dict[str, object]:
        payload = self.issues.get(issue_number)
        if payload is None:
            raise RuntimeError(f"Unknown issue: {issue_number}")
        return dict(payload)

    def list_issues(self, *, state: str = "open", per_page: int = 10) -> list[dict[str, object]]:
        issues = [dict(payload) for payload in self.issues.values() if str(payload.get("state", "")).lower() == state.lower()]
        return issues[:per_page]

    def list_pull_requests(self, *, state: str = "open", per_page: int = 10) -> list[dict[str, object]]:
        pulls = [dict(payload) for payload in self.pull_requests if str(payload.get("state", state)).lower() == state.lower()]
        return pulls[:per_page]

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


class ClosedIssueGitHubAdapter(FakeGitHubAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.issues[7] = {
            "number": 7,
            "title": "Closed tracked issue for tests",
            "state": "closed",
            "html_url": "https://github.com/example/skylattice/issues/7",
        }


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _run(command: list[str], cwd: Path) -> str:
    completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=True)
    return completed.stdout


def create_temp_repo(
    tmp_path: Path,
    validation_commands: tuple[str, ...] | None = None,
    validation_yaml: str | None = None,
) -> Path:
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
    if validation_yaml is not None:
        _write(repo / "configs" / "task" / "validation.yaml", validation_yaml.strip() + "\n")
    else:
        _write(
            repo / "configs" / "task" / "validation.yaml",
            "runner: powershell\n\nallowed_commands:\n"
            + "".join(f"  - {command}\n" for command in commands),
        )
    _write(repo / "README.md", "# Temp Repo\n\nInitial content.\n")
    _write(repo / "docs" / "tasks" / "_template.md", "# Task Brief Template\n\n## Intent\n\n- describe the goal\n")

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


def build_validation_id_plan(validation_ref: str) -> dict[str, object]:
    plan = build_fake_plan()
    plan["validation_commands"] = [validation_ref]
    return plan


def build_repo_primitives_plan(validation_ref: str) -> dict[str, object]:
    return {
        "summary": "Create a note and scaffold a task brief from the tracked template.",
        "branch_name": "repo-primitives",
        "file_operations": [
            {
                "path": "docs/notes.md",
                "mode": "create_file",
                "create_if_missing": True,
                "instructions": "Create a short tracked note describing the new repo primitives.",
            },
            {
                "path": "docs/tasks/new-brief.md",
                "mode": "copy_file",
                "source_path": "docs/tasks/_template.md",
                "create_if_missing": False,
                "instructions": "Copy the tracked task brief template to a new brief path.",
            },
        ],
        "validation_commands": [validation_ref],
        "commit_message": "docs: add note and task brief scaffold",
        "pull_request": {
            "title": "docs: add note and task brief scaffold",
            "body": "This exercises create_file and copy_file task operations.",
            "base_branch": "main",
        },
    }


def build_destructive_repo_plan(validation_ref: str) -> dict[str, object]:
    return {
        "summary": "Clean up tracked docs by deleting obsolete content and moving a file to a better path.",
        "branch_name": "destructive-repo-ops",
        "file_operations": [
            {
                "path": "docs/obsolete.md",
                "mode": "delete_file",
                "create_if_missing": False,
                "instructions": "Delete the obsolete tracked doc now that it is replaced elsewhere.",
            },
            {
                "path": "docs/renamed.md",
                "mode": "move_file",
                "source_path": "docs/rename-me.md",
                "create_if_missing": False,
                "instructions": "Move the tracked doc to its canonical destination path.",
            },
        ],
        "validation_commands": [validation_ref],
        "commit_message": "docs: clean up tracked docs",
        "pull_request": {
            "title": "docs: clean up tracked docs",
            "body": "This exercises destructive tracked repo ops with explicit approval.",
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


def test_task_validation_policy_loads_richer_schema(tmp_path: Path) -> None:
    repo = create_temp_repo(
        tmp_path,
        validation_yaml="""
runner: powershell
default_profile: docs
commands:
  - id: hello
    command: python -c "print('validation-ok')"
    description: Print a stable marker.
    expected_returncode: 0
    stdout_contains:
      - validation-ok
  - id: git-status
    command: git status --short
    expected_returncode: 0
profiles:
  docs:
    - hello
    - git-status
""",
    )

    policy = load_task_validation_policy(repo)

    assert policy.default_profile == "docs"
    assert policy.command_ids == ("hello", "git-status")
    assert policy.profile_command_ids() == ("hello", "git-status")
    assert policy.resolve_command("hello").command == 'python -c "print(\'validation-ok\')"'
    assert policy.resolve_command("git status --short").id == "git-status"


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

    destructive_denied = gate.evaluate(
        GovernanceRequest(
            tier=PermissionTier.REPO_WRITE,
            summary="delete tracked README",
            destructive=True,
            user_approved=True,
        )
    )
    destructive_approved = gate.evaluate(
        GovernanceRequest(
            tier=PermissionTier.REPO_WRITE,
            summary="delete tracked README",
            destructive=True,
            user_approved=True,
            destructive_approved=True,
        )
    )

    assert destructive_denied.decision is GovernanceDecision.DENIED
    assert "destructive-repo-write" in destructive_denied.reason
    assert destructive_approved.decision is GovernanceDecision.APPROVED


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
    created = workspace.create_file("docs/created.md", "# Created\n")
    copied = workspace.copy_file("docs/created.md", "docs/copied.md")
    assert created == "docs/created.md"
    assert copied == "docs/copied.md"
    assert (repo / "docs" / "copied.md").read_text(encoding="utf-8") == "# Created\n"
    with pytest.raises(ValueError, match="File already exists"):
        workspace.create_file("docs/created.md", "# Exists\n")
    with pytest.raises(ValueError, match="Destination already exists"):
        workspace.copy_file("docs/created.md", "docs/copied.md")
    _write(repo / "docs" / "delete-me.md", "# Delete me\n")
    _write(repo / "docs" / "move-me.md", "# Move me\n")
    deleted = workspace.delete_file("docs/delete-me.md")
    moved = workspace.move_file("docs/move-me.md", "docs/moved.md")
    assert deleted == "docs/delete-me.md"
    assert moved == "docs/moved.md"
    assert not (repo / "docs" / "delete-me.md").exists()
    assert not (repo / "docs" / "move-me.md").exists()
    assert (repo / "docs" / "moved.md").read_text(encoding="utf-8") == "# Move me\n"
    with pytest.raises(ValueError, match="Destination already exists"):
        workspace.move_file("docs/copied.md", "docs/moved.md")


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
    assert details["steps"][4]["action_name"] == "workspace.run_validation"
    assert details["steps"][4]["action_args"]["command"] == "git diff --stat"
    assert details["steps"][4]["action_args"]["command_id"] == "git-diff-stat"
    assert all("materialized_edit" in step["result"] for step in details["steps"][1:4])
    assert details["steps"][1]["result"]["materialized_edit"]["target_text"] == "Initial content."
    assert github.pull_requests[0]["title"] == "docs: exercise deterministic task-agent edits"


def test_task_run_accepts_validation_ids_and_records_validation_metadata(tmp_path: Path) -> None:
    repo = create_temp_repo(
        tmp_path,
        validation_yaml="""
runner: powershell
default_profile: baseline
commands:
  - id: marker-check
    command: python -c "print('validation-ok')"
    expected_returncode: 0
    stdout_contains:
      - validation-ok
profiles:
  baseline:
    - marker-check
""",
    )
    provider = FakeProvider(
        plan=build_validation_id_plan("marker-check"),
        file_outputs={"README.md": "# Temp Repo\n\nValidation id path.\n"},
    )
    service = TaskAgentService.from_repo(repo_root=repo, provider=provider, github_adapter=FakeGitHubAdapter())
    service.git = LocalPushGitAdapter(repo)

    completed = service.run_task(
        goal_input="Refresh the README and run the tracked marker validation.",
        allow_repo_write=True,
        allow_external_write=True,
    )
    details = service.inspect_run(completed.run_id)

    assert completed.status.value == "completed"
    assert details["steps"][2]["action_name"] == "workspace.run_validation"
    assert details["steps"][2]["action_args"]["command_id"] == "marker-check"
    assert details["steps"][2]["result"]["validation_id"] == "marker-check"
    assert provider.plan_inputs[0]["allowed_validation_commands"] == ["marker-check", 'python -c "print(\'validation-ok\')"']


def test_task_planner_receives_bounded_github_context_when_available(tmp_path: Path) -> None:
    repo = create_temp_repo(tmp_path)
    github = FakeGitHubAdapter()
    provider = FakeProvider(
        plan=build_fake_plan(),
        file_outputs={"README.md": "# Temp Repo\n\nGitHub context path.\n"},
    )
    service = TaskAgentService.from_repo(repo_root=repo, provider=provider, github_adapter=github)
    service.git = LocalPushGitAdapter(repo)

    service.run_task(
        goal_input="Refresh the README and prepare a PR.",
        allow_repo_write=True,
        allow_external_write=True,
    )

    github_context = provider.plan_inputs[0]["repo_context"]["github_context"]
    assert github_context["available"] is True
    assert github_context["repository"] == "example/skylattice"
    assert github_context["open_issues"][0]["number"] == 7
    assert "open_pull_requests" in github_context


def test_task_run_supports_create_file_and_copy_file_primitives(tmp_path: Path) -> None:
    repo = create_temp_repo(
        tmp_path,
        validation_yaml="""
runner: powershell
default_profile: baseline
commands:
  - id: git-diff-stat
    command: git diff --stat
    expected_returncode: 0
profiles:
  baseline:
    - git-diff-stat
""",
    )
    provider = FakeProvider(
        plan=build_repo_primitives_plan("git-diff-stat"),
        file_outputs={"docs/notes.md": "# Repo Primitives\n\nCreate-file path.\n"},
    )
    service = TaskAgentService.from_repo(repo_root=repo, provider=provider, github_adapter=FakeGitHubAdapter())
    service.git = LocalPushGitAdapter(repo)

    completed = service.run_task(
        goal_input="Create a note and scaffold a new task brief.",
        allow_repo_write=True,
        allow_external_write=True,
    )
    details = service.inspect_run(completed.run_id)

    assert completed.status.value == "completed"
    assert (repo / "docs" / "notes.md").read_text(encoding="utf-8").startswith("# Repo Primitives")
    assert (repo / "docs" / "tasks" / "new-brief.md").read_text(encoding="utf-8") == (
        repo / "docs" / "tasks" / "_template.md"
    ).read_text(encoding="utf-8")
    assert details["steps"][1]["action_name"] == "workspace.create_file"
    assert details["steps"][1]["result"]["materialized_edit"]["mode"] == "create_file"
    assert details["steps"][2]["action_name"] == "workspace.copy_file"
    assert details["steps"][2]["result"]["materialized_edit"]["mode"] == "copy_file"
    assert details["steps"][2]["result"]["source_path"] == "docs/tasks/_template.md"


def test_validation_step_fails_when_expected_stdout_is_missing(tmp_path: Path) -> None:
    repo = create_temp_repo(
        tmp_path,
        validation_yaml="""
runner: powershell
default_profile: baseline
commands:
  - id: marker-check
    command: python -c "print('wrong-output')"
    expected_returncode: 0
    stdout_contains:
      - validation-ok
profiles:
  baseline:
    - marker-check
""",
    )
    provider = FakeProvider(
        plan=build_validation_id_plan("marker-check"),
        file_outputs={"README.md": "# Temp Repo\n\nValidation failure path.\n"},
    )
    service = TaskAgentService.from_repo(repo_root=repo, provider=provider, github_adapter=FakeGitHubAdapter())
    service.git = LocalPushGitAdapter(repo)

    failed = service.run_task(
        goal_input="Refresh the README and run the tracked marker validation.",
        allow_repo_write=True,
        allow_external_write=True,
    )
    details = service.inspect_run(failed.run_id)

    assert failed.status.value == "failed"
    assert details["steps"][2]["status"] == "failed"
    assert "stdout missing expected text" in details["steps"][2]["result"]["last_error"]


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


def test_issue_comment_preflight_rejects_closed_issue(tmp_path: Path) -> None:
    repo = create_temp_repo(tmp_path)
    provider = FakeProvider(
        plan=build_issue_comment_plan(),
        file_outputs={"README.md": "# Temp Repo\n\nClosed issue preflight path.\n"},
    )
    github = ClosedIssueGitHubAdapter()
    service = TaskAgentService.from_repo(repo_root=repo, provider=provider, github_adapter=github)
    service.git = LocalPushGitAdapter(repo)

    failed = service.run_task(
        goal_input="Refresh the README, prepare a PR, and leave an issue comment.",
        allow_repo_write=True,
        allow_external_write=True,
    )
    details = service.inspect_run(failed.run_id)

    assert failed.status.value == "failed"
    assert details["steps"][-2]["action_name"] == "github.inspect_issue"
    assert details["steps"][-2]["status"] == "failed"
    assert "GitHub issue is not open" in details["steps"][-2]["result"]["last_error"]
    assert details["steps"][-1]["status"] == "planned"
    assert len(github.comments) == 0


def test_task_validation_commands_come_from_tracked_config(tmp_path: Path) -> None:
    repo = create_temp_repo(tmp_path, validation_commands=("git diff --stat",))
    service = TaskAgentService.from_repo(repo_root=repo)

    assert service.workspace.run_check("git diff --stat")["returncode"] == 0
    with pytest.raises(ValueError, match="Command not allowed"):
        service.workspace.run_check("git status --short")


def test_destructive_repo_steps_require_separate_approval_and_resume(tmp_path: Path) -> None:
    repo = create_temp_repo(tmp_path, validation_commands=("git status --short",))
    _write(repo / "docs" / "obsolete.md", "# Obsolete\n")
    _write(repo / "docs" / "rename-me.md", "# Rename me\n")
    provider = FakeProvider(plan=build_destructive_repo_plan("git status --short"))
    service = TaskAgentService.from_repo(repo_root=repo, provider=provider, github_adapter=FakeGitHubAdapter())
    service.git = LocalPushGitAdapter(repo)

    blocked = service.run_task(
        goal_input="Clean up tracked docs with explicit destructive approval.",
        allow_repo_write=True,
        allow_external_write=True,
    )
    blocked_details = service.inspect_run(blocked.run_id)

    assert blocked.status.value == "waiting_approval"
    assert blocked_details["recovery"]["next_step_id"] == "edit-1"
    assert blocked_details["recovery"]["destructive"] is True
    assert PermissionTier.DESTRUCTIVE_REPO_WRITE.value in blocked_details["recovery"]["recommended_allows"]
    assert blocked_details["steps"][1]["action_name"] == "workspace.delete_file"
    assert blocked_details["steps"][1]["status"] == "blocked"
    assert (repo / "docs" / "obsolete.md").exists()
    assert (repo / "docs" / "rename-me.md").exists()

    resumed = service.resume_task(
        run_id=blocked.run_id,
        allow_destructive_repo_write=True,
    )
    resumed_details = service.inspect_run(resumed.run_id)

    assert resumed.status.value == "completed"
    assert resumed_details["recovery"]["status"] == "completed"
    assert not (repo / "docs" / "obsolete.md").exists()
    assert not (repo / "docs" / "rename-me.md").exists()
    assert (repo / "docs" / "renamed.md").read_text(encoding="utf-8") == "# Rename me\n"


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
