from __future__ import annotations

import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from skylattice.cli import main


class FakeWebService:
    def __init__(self) -> None:
        self.repo_root = Path(".")


def test_web_status_command_outputs_connector_report(monkeypatch) -> None:
    monkeypatch.setattr("skylattice.cli.TaskAgentService.from_repo", lambda: FakeWebService())
    monkeypatch.setattr(
        "skylattice.cli.SkylatticeWebConnector.status_report",
        lambda self: {"status": "ok", "connector": {"paired": False}, "bridge": {"bridge_key_env_present": False}},
    )

    buffer = StringIO()
    with redirect_stdout(buffer):
        exit_code = main(["web", "status"])

    payload = json.loads(buffer.getvalue())
    assert exit_code == 0
    assert payload["status"] == "ok"
    assert payload["connector"]["paired"] is False


def test_web_pair_command_calls_connector_pair(monkeypatch) -> None:
    monkeypatch.setattr("skylattice.cli.TaskAgentService.from_repo", lambda: FakeWebService())
    monkeypatch.setattr(
        "skylattice.cli.SkylatticeWebConnector.pair",
        lambda self, *, control_plane_url, pairing_code, device_label, bridge_base_url=None: {
            "status": "ok",
            "pairing": {
                "control_plane_url": control_plane_url,
                "device_id": "device-1",
                "device_label": device_label,
                "connector_token_present": True,
            },
            "bridge_base_url": bridge_base_url,
            "pairing_code": pairing_code,
        },
    )

    buffer = StringIO()
    with redirect_stdout(buffer):
        exit_code = main(
            [
                "web",
                "pair",
                "--control-plane-url",
                "http://localhost:3000",
                "--code",
                "PAIRME12",
                "--device-label",
                "Primary workstation",
            ]
        )

    payload = json.loads(buffer.getvalue())
    assert exit_code == 0
    assert payload["status"] == "ok"
    assert payload["pairing"]["device_id"] == "device-1"
    assert payload["pairing_code"] == "PAIRME12"


def test_web_connector_heartbeat_command_outputs_payload(monkeypatch) -> None:
    monkeypatch.setattr("skylattice.cli.TaskAgentService.from_repo", lambda: FakeWebService())
    monkeypatch.setattr(
        "skylattice.cli.SkylatticeWebConnector.heartbeat",
        lambda self: {"status": "ok", "device": {"device_id": "device-1", "online": True}},
    )

    buffer = StringIO()
    with redirect_stdout(buffer):
        exit_code = main(["web", "connector", "heartbeat"])

    payload = json.loads(buffer.getvalue())
    assert exit_code == 0
    assert payload["status"] == "ok"
    assert payload["device"]["online"] is True


def test_web_connector_once_command_outputs_dispatch_result(monkeypatch) -> None:
    monkeypatch.setattr("skylattice.cli.TaskAgentService.from_repo", lambda: FakeWebService())
    monkeypatch.setattr(
        "skylattice.cli.SkylatticeWebConnector.poll_once",
        lambda self: {
            "status": "ok",
            "command": {"commandId": "cmd-1", "kind": "memory.search"},
            "result": {"records": []},
        },
    )

    buffer = StringIO()
    with redirect_stdout(buffer):
        exit_code = main(["web", "connector", "once"])

    payload = json.loads(buffer.getvalue())
    assert exit_code == 0
    assert payload["status"] == "ok"
    assert payload["command"]["commandId"] == "cmd-1"
