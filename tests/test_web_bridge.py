from __future__ import annotations

import subprocess
from pathlib import Path

from fastapi.testclient import TestClient

from skylattice.api import app, get_task_agent_service
from skylattice.providers import FakeProvider
from skylattice.runtime import TaskAgentService
from skylattice.web import SkylatticeWebConnector


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
  version: 0.4.0
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
        """
runner: powershell
default_profile: baseline
commands:
  - id: git-status
    command: git status --short
    expected_returncode: 0
profiles:
  baseline:
    - git-status
""".strip(),
    )
    _write(repo / ".gitignore", ".local/\n__pycache__/\n.pytest_cache/\n")
    _write(repo / "README.md", "# Temp Repo\n\nInitial content.\n")

    _run(["git", "init", "-b", "main"], repo)
    _run(["git", "config", "user.email", "tests@example.com"], repo)
    _run(["git", "config", "user.name", "Skylattice Tests"], repo)
    _run(["git", "add", "--all"], repo)
    _run(["git", "commit", "-m", "initial"], repo)
    return repo


def _auth_headers() -> dict[str, str]:
    return {"x-skylattice-bridge-key": "bridge-secret"}


def build_fake_plan() -> dict[str, object]:
    return {
        "summary": "Refresh README and open a draft PR.",
        "branch_name": "web-bridge-refresh",
        "file_operations": [
            {
                "path": "README.md",
                "mode": "rewrite",
                "create_if_missing": False,
                "instructions": "Add one short section describing the hosted web control plane.",
            }
        ],
        "validation_commands": ["git status --short"],
        "commit_message": "docs: refresh README for web control plane",
        "pull_request": {
            "title": "docs: refresh README for web control plane",
            "body": "This updates README.md to mention the hosted web control plane.",
            "base_branch": "main",
        },
    }


def test_bridge_status_requires_auth_and_reports_pairing_state(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = create_temp_repo(tmp_path)
    service = TaskAgentService.from_repo(
        repo_root=repo,
        provider=FakeProvider(
            plan=build_fake_plan(),
            file_outputs={"README.md": "# Temp Repo\n\nHosted web control plane.\n"},
        ),
    )
    monkeypatch.setenv("SKYLATTICE_WEB_BRIDGE_KEY", "bridge-secret")

    app.dependency_overrides[get_task_agent_service] = lambda: service
    client = TestClient(app)
    try:
        blocked = client.get("/bridge/v1/status")
        allowed = client.get("/bridge/v1/status", headers=_auth_headers())
    finally:
        app.dependency_overrides.clear()

    assert blocked.status_code == 401
    assert allowed.status_code == 200
    payload = allowed.json()
    assert payload["bridge"]["bridge_key_env_present"] is True
    assert payload["connector"]["paired"] is False
    assert payload["doctor"]["status"] == "ok"


def test_bridge_task_and_memory_routes_execute_with_shared_runtime(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = create_temp_repo(tmp_path)
    service = TaskAgentService.from_repo(
        repo_root=repo,
        provider=FakeProvider(
            plan=build_fake_plan(),
            file_outputs={"README.md": "# Temp Repo\n\nHosted web control plane.\n"},
        ),
    )
    monkeypatch.setenv("SKYLATTICE_WEB_BRIDGE_KEY", "bridge-secret")

    app.dependency_overrides[get_task_agent_service] = lambda: service
    client = TestClient(app)
    try:
        memory_response = client.post(
            "/bridge/v1/memory/profile/proposals",
            headers=_auth_headers(),
            json={
                "key": "operator_style",
                "value": "concise, architecture-first",
                "reason": "Match hosted control-plane defaults.",
            },
        )
        record_id = memory_response.json()["record_id"]
        confirm_response = client.post(
            "/bridge/v1/memory/review/confirm",
            headers=_auth_headers(),
            json={"record_id": record_id},
        )
        task_response = client.post(
            "/bridge/v1/task/runs",
            headers=_auth_headers(),
            json={
                "goal": "Refresh the README and prepare a draft PR.",
                "allow_repo_write": True,
            },
        )
        inspect_response = client.get(
            f"/bridge/v1/task/runs/{task_response.json()['run']['run_id']}",
            headers=_auth_headers(),
        )
        events_response = client.get(
            f"/bridge/v1/task/runs/{task_response.json()['run']['run_id']}/events",
            headers=_auth_headers(),
        )
        memory_run_response = client.get(
            f"/bridge/v1/task/runs/{task_response.json()['run']['run_id']}/memory",
            headers=_auth_headers(),
        )
        recovery_response = client.get(
            f"/bridge/v1/task/runs/{task_response.json()['run']['run_id']}/recovery",
            headers=_auth_headers(),
        )
    finally:
        app.dependency_overrides.clear()

    assert memory_response.status_code == 200
    assert confirm_response.status_code == 200
    assert confirm_response.json()["status"] == "active"
    assert task_response.status_code == 200
    assert task_response.json()["run"]["run_id"].startswith("run-")
    assert inspect_response.status_code == 200
    assert inspect_response.json()["run"]["run_id"] == task_response.json()["run"]["run_id"]
    assert events_response.status_code == 200
    assert isinstance(events_response.json(), list)
    assert memory_run_response.status_code == 200
    assert isinstance(memory_run_response.json(), list)
    assert recovery_response.status_code == 200
    assert "guidance" in recovery_response.json()
    assert isinstance(recovery_response.json()["guidance"], list)


def test_bridge_doctor_and_radar_inspection_routes_are_available(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = create_temp_repo(tmp_path)
    service = TaskAgentService.from_repo(
        repo_root=repo,
        provider=FakeProvider(
            plan=build_fake_plan(),
            file_outputs={"README.md": "# Temp Repo\n\nHosted web control plane.\n"},
        ),
    )
    monkeypatch.setenv("SKYLATTICE_WEB_BRIDGE_KEY", "bridge-secret")

    app.dependency_overrides[get_task_agent_service] = lambda: service
    client = TestClient(app)
    try:
        doctor_response = client.get("/bridge/v1/doctor", headers=_auth_headers())
        auth_response = client.get("/bridge/v1/auth-preflight", headers=_auth_headers())
        digest_response = client.get("/bridge/v1/radar/digest/latest", headers=_auth_headers())
        schedule_response = client.get("/bridge/v1/radar/schedule", headers=_auth_headers())
        render_response = client.get("/bridge/v1/radar/schedule/render", headers=_auth_headers())
    finally:
        app.dependency_overrides.clear()

    assert doctor_response.status_code == 200
    assert doctor_response.json()["status"] == "ok"
    assert auth_response.status_code == 200
    assert auth_response.json()["status"] == "ok"
    assert digest_response.status_code == 200
    assert isinstance(digest_response.json(), dict)
    assert schedule_response.status_code == 200
    assert schedule_response.json()["default_schedule"] == "weekly-github"
    assert render_response.status_code == 200
    assert render_response.json()["target"] == "windows-task"


def test_web_connector_pair_and_poll_once_dispatches_commands(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = create_temp_repo(tmp_path)
    service = TaskAgentService.from_repo(
        repo_root=repo,
        provider=FakeProvider(
            plan=build_fake_plan(),
            file_outputs={"README.md": "# Temp Repo\n\nHosted web control plane.\n"},
        ),
    )
    connector = SkylatticeWebConnector(repo_root=repo, service=service)

    pair_calls: list[tuple[str, str]] = []

    def fake_pair_request(url: str, *, method: str, payload=None, connector_token=None):
        pair_calls.append((url, method))
        return {
            "deviceId": "device-1",
            "label": "Primary workstation",
            "connectorToken": "token-1",
        }

    monkeypatch.setattr(connector, "_request_json", fake_pair_request)
    pair_payload = connector.pair(
        control_plane_url="http://example.test:3000",
        pairing_code="PAIRME12",
        device_label="Primary workstation",
    )

    assert pair_payload["status"] == "ok"
    assert connector.config.status_payload()["paired"] is True
    assert (repo / ".local" / "overrides" / "web-control-plane.json").exists()

    def fake_poll_request(url: str, *, method: str, payload=None, connector_token=None):
        if url.endswith("/devices/heartbeat"):
            return {"device": {"deviceId": "device-1", "online": True}}
        if url.endswith("/commands/next"):
            return {
                "command": {
                    "commandId": "cmd-1",
                    "kind": "memory.profile.propose",
                    "payload": {
                        "key": "operator_style",
                        "value": "web-first but governed",
                        "reason": "Created from hosted app.",
                    },
                }
            }
        if url.endswith("/commands/cmd-1/result"):
            return {"command": {"commandId": "cmd-1", "status": "succeeded"}}
        raise AssertionError(f"Unexpected connector request: {url}")

    monkeypatch.setattr(connector, "_request_json", fake_poll_request)
    poll_payload = connector.poll_once()

    assert poll_payload["status"] == "ok"
    assert poll_payload["command"]["commandId"] == "cmd-1"
    assert poll_payload["recorded"]["status"] == "succeeded"
    assert service.list_memory_review_queue(limit=10)
