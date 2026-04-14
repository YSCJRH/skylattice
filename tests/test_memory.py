from __future__ import annotations

import json
import subprocess
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from fastapi.testclient import TestClient

import skylattice.cli as cli_module
from skylattice.api import app, get_task_agent_service
from skylattice.memory import MemoryLayer, RecordStatus
from skylattice.providers import FakeProvider
from skylattice.runtime import TaskAgentService


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _run(command: list[str], cwd: Path) -> str:
    completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=True)
    return completed.stdout


def create_temp_repo(tmp_path: Path, validation_commands: tuple[str, ...] | None = None) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    commands = validation_commands or (
        "python -m pytest -q",
        "python -m compileall src/skylattice",
        "python -m skylattice.cli doctor",
        "git status --short",
    )

    _write(
        repo / "configs" / "agent" / "defaults.yaml",
        """
agent:
  id: skylattice
  codename: skylattice
  version: 0.2.2
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
        "runner: powershell\n\nallowed_commands:\n" + "".join(f"  - {command}\n" for command in commands),
    )
    _write(repo / ".gitignore", ".local/\n__pycache__/\n.pytest_cache/\n")
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


def test_memory_search_ranks_exact_summary_ahead_of_metadata_only_match(tmp_path: Path) -> None:
    repo = create_temp_repo(tmp_path)
    service = TaskAgentService.from_repo(repo_root=repo)
    service.memory.create(
        layer=MemoryLayer.SEMANTIC,
        summary="Repo tasks workflow for governed documentation changes.",
        metadata={"topic_tags": ["docs"]},
    )
    service.memory.create(
        layer=MemoryLayer.SEMANTIC,
        summary="Documentation workflow",
        metadata={"topic_tags": ["repo", "tasks"]},
    )

    results = service.search_memory(query="repo tasks", layers=(MemoryLayer.SEMANTIC,), limit=5)

    assert results[0]["summary"] == "Repo tasks workflow for governed documentation changes."


def test_memory_search_excludes_stale_records_unless_status_filter_is_provided(tmp_path: Path) -> None:
    repo = create_temp_repo(tmp_path)
    service = TaskAgentService.from_repo(repo_root=repo)
    active = service.memory.create(
        layer=MemoryLayer.PROFILE,
        summary="Profile preference for tone: concise",
        metadata={"profile_key": "tone", "value": "concise"},
    )
    stale = service.memory.create(
        layer=MemoryLayer.PROFILE,
        summary="Profile preference for tone: detailed",
        metadata={"profile_key": "tone", "value": "detailed"},
        status=RecordStatus.TOMBSTONED,
    )

    fresh_only = service.search_memory(query="tone", layers=(MemoryLayer.PROFILE,), limit=5)
    with_stale = service.search_memory(
        query="tone",
        layers=(MemoryLayer.PROFILE,),
        statuses=(RecordStatus.ACTIVE, RecordStatus.TOMBSTONED),
        limit=5,
    )

    assert [item["record_id"] for item in fresh_only] == [active.record_id]
    assert [item["record_id"] for item in with_stale] == [active.record_id, stale.record_id]


def test_profile_memory_review_confirm_supersedes_prior_active_record(tmp_path: Path) -> None:
    repo = create_temp_repo(tmp_path)
    service = TaskAgentService.from_repo(repo_root=repo)

    first = service.propose_profile_memory(key="tone", value="concise", reason="User prefers short answers.")
    confirmed_first = service.confirm_memory_record(first["record_id"])
    second = service.propose_profile_memory(key="tone", value="detailed", reason="User wants more depth now.")
    confirmed_second = service.confirm_memory_record(second["record_id"])

    prior = service.inspect_memory_record(confirmed_first["record_id"])
    current = service.inspect_memory_record(confirmed_second["record_id"])

    assert prior["status"] == "superseded"
    assert current["status"] == "active"
    assert current["supersedes"] == prior["record_id"]


def test_profile_memory_review_reject_tombstones_proposal(tmp_path: Path) -> None:
    repo = create_temp_repo(tmp_path)
    service = TaskAgentService.from_repo(repo_root=repo)

    proposal = service.propose_profile_memory(key="timezone", value="UTC", reason="Operator confirmed timezone.")
    rejected = service.reject_memory_record(proposal["record_id"])

    assert rejected["status"] == "tombstoned"


def test_semantic_compaction_creates_and_confirms_reviewable_proposal(tmp_path: Path) -> None:
    repo = create_temp_repo(tmp_path)
    service = TaskAgentService.from_repo(repo_root=repo)
    source_a = service.memory.create(layer=MemoryLayer.SEMANTIC, summary="Governed repo task pattern for docs.")
    source_b = service.memory.create(layer=MemoryLayer.SEMANTIC, summary="Governed repo task pattern for docs!")

    proposals = service.create_semantic_compaction_proposals()
    confirmed = service.confirm_memory_record(proposals[0]["record_id"])

    assert proposals[0]["status"] == "constrained"
    assert confirmed["status"] == "active"
    assert service.inspect_memory_record(source_a.record_id)["status"] == "superseded"
    assert service.inspect_memory_record(source_b.record_id)["status"] == "superseded"


def test_procedural_dedup_creates_canonical_reviewable_proposal(tmp_path: Path) -> None:
    repo = create_temp_repo(tmp_path)
    service = TaskAgentService.from_repo(repo_root=repo)
    first = service.memory.create(
        layer=MemoryLayer.PROCEDURAL,
        summary="Repo ops workflow with validation before PR creation.",
        metadata={"workflow": "repo-ops-github-triage", "canonical": False},
        confidence=0.8,
    )
    second = service.memory.create(
        layer=MemoryLayer.PROCEDURAL,
        summary="Branch-edit-validate-push-draft-PR workflow.",
        metadata={"workflow": "repo-ops-github-triage", "canonical": False},
        confidence=0.9,
    )

    proposals = service.create_procedural_dedup_proposals()
    confirmed = service.confirm_memory_record(proposals[0]["record_id"])

    assert proposals[0]["status"] == "constrained"
    assert confirmed["status"] == "active"
    assert confirmed["metadata"]["canonical"] is True
    assert service.inspect_memory_record(first.record_id)["status"] == "superseded"
    assert service.inspect_memory_record(second.record_id)["status"] == "superseded"


def test_memory_export_writes_json_under_local_memory_exports(tmp_path: Path) -> None:
    repo = create_temp_repo(tmp_path)
    service = TaskAgentService.from_repo(repo_root=repo)
    service.memory.create(layer=MemoryLayer.EPISODIC, summary="A finished local test run.")

    exported = service.export_memory_records()
    export_path = repo / exported["path"]
    payload = json.loads(export_path.read_text(encoding="utf-8"))

    assert export_path.exists()
    assert ".local/memory/exports/" in exported["path"]
    assert payload["count"] == 1
    assert payload["records"][0]["summary"] == "A finished local test run."


def test_task_planning_receives_ranked_memory_context(tmp_path: Path) -> None:
    repo = create_temp_repo(tmp_path)
    provider = FakeProvider(plan=build_fake_plan())
    service = TaskAgentService.from_repo(repo_root=repo, provider=provider)
    service.memory.create(
        layer=MemoryLayer.PROFILE,
        summary="Profile preference for code review tone: concise",
        metadata={"profile_key": "review-tone", "value": "concise"},
    )
    service.memory.create(
        layer=MemoryLayer.PROCEDURAL,
        summary="Repo ops workflow with draft PR delivery.",
        metadata={"workflow": "repo-ops-github-triage", "canonical": False},
    )
    service.memory.create(
        layer=MemoryLayer.SEMANTIC,
        summary="Governed repo tasks should keep validation commands tracked.",
        metadata={"origin": "task", "topic_tags": ["repo", "validation"]},
    )

    service.run_task(goal_input="Refresh the README with tracked repo task guidance.")
    memory_context = provider.plan_inputs[0]["repo_context"]["memory_context"]

    assert memory_context["profile"][0]["layer"] == "profile"
    assert memory_context["procedural"][0]["layer"] == "procedural"
    assert memory_context["semantic"][0]["layer"] == "semantic"


def test_memory_cli_profile_review_and_search_commands(tmp_path: Path, monkeypatch) -> None:
    repo = create_temp_repo(tmp_path)
    service = TaskAgentService.from_repo(repo_root=repo)
    monkeypatch.setattr(cli_module.TaskAgentService, "from_repo", classmethod(lambda cls: service))

    buffer = StringIO()
    with redirect_stdout(buffer):
        propose_exit = cli_module.main(
            ["memory", "profile", "propose", "--key", "tone", "--value", "concise", "--reason", "User asked for concise answers."]
        )
    proposal = json.loads(buffer.getvalue())

    buffer = StringIO()
    with redirect_stdout(buffer):
        review_exit = cli_module.main(["memory", "review", "confirm", proposal["record_id"]])
    confirmed = json.loads(buffer.getvalue())

    buffer = StringIO()
    with redirect_stdout(buffer):
        search_exit = cli_module.main(["memory", "search", "--query", "concise", "--layer", "profile"])
    search_results = json.loads(buffer.getvalue())

    assert propose_exit == 0
    assert review_exit == 0
    assert search_exit == 0
    assert confirmed["status"] == "active"
    assert search_results[0]["record_id"] == proposal["record_id"]


def test_memory_api_returns_record_and_ranked_search_results(tmp_path: Path) -> None:
    repo = create_temp_repo(tmp_path)
    service = TaskAgentService.from_repo(repo_root=repo)
    record = service.memory.create(
        layer=MemoryLayer.SEMANTIC,
        summary="Local-first governed repo task pattern.",
        metadata={"origin": "task", "topic_tags": ["repo", "task"]},
    )

    app.dependency_overrides[get_task_agent_service] = lambda: service
    client = TestClient(app)
    try:
        record_response = client.get(f"/memory/records/{record.record_id}")
        search_response = client.get("/memory/search", params={"query": "repo task", "layer": "semantic", "limit": 5})
    finally:
        app.dependency_overrides.clear()

    assert record_response.status_code == 200
    assert record_response.json()["record_id"] == record.record_id
    assert search_response.status_code == 200
    assert search_response.json()[0]["record_id"] == record.record_id
