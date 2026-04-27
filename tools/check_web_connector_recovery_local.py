from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from check_web_control_cockpit_ui import (
    REPO_ROOT,
    NextEnvGuard,
    base_env,
    fetch_when_ready,
    find_free_port,
    next_cli_path,
    resolve_node,
    start_next_dev,
    stop_process_tree,
)
from skylattice.runtime import TaskAgentService
from skylattice.web import SkylatticeWebConnector
from skylattice.web.config import WebConnectorConfig


PAIRING_CODE = "FAIL1234"
COMMAND_ID = "cmd-local-recovery-proof"
MISSING_RECORD_ID = "missing-review-record"
PROOF_USER_ID = "github:local-proof"


def _seed_state() -> dict[str, list[dict[str, Any]]]:
    return {
        "devices": [],
        "pairings": [
            {
                "pairingId": "pairing-local-recovery-proof",
                "userId": PROOF_USER_ID,
                "pairingCode": PAIRING_CODE,
                "createdAt": "2026-04-27T11:00:00.000Z",
                "expiresAt": "2099-01-01T00:00:00.000Z",
                "claimedAt": None,
                "deviceId": None,
                "deviceLabel": None,
                "connectorToken": None,
            }
        ],
        "commands": [
            {
                "commandId": COMMAND_ID,
                "userId": PROOF_USER_ID,
                "deviceId": None,
                "kind": "memory.review.confirm",
                "status": "queued",
                "createdAt": "2026-04-27T11:01:00.000Z",
                "updatedAt": "2026-04-27T11:01:00.000Z",
                "claimedAt": None,
                "payload": {
                    "recordId": MISSING_RECORD_ID,
                },
                "result": None,
                "error": None,
            }
        ],
        "approvals": [],
    }


def _fail(message: str) -> None:
    raise RuntimeError(message)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_recovery_state(state_path: Path) -> dict[str, Any]:
    state = _load_json(state_path)
    devices = state.get("devices", [])
    commands = state.get("commands", [])
    approvals = state.get("approvals", [])
    if len(devices) != 1:
        _fail(f"Expected exactly one paired device, found {len(devices)}.")
    if len(commands) != 1:
        _fail(f"Expected exactly one command, found {len(commands)}.")
    if len(approvals) != 1:
        _fail(f"Expected exactly one approval reminder, found {len(approvals)}.")

    device = devices[0]
    command = commands[0]
    approval = approvals[0]
    if command.get("commandId") != COMMAND_ID:
        _fail("Unexpected command id after recovery proof.")
    if command.get("status") != "failed":
        _fail(f"Expected command status failed, found {command.get('status')!r}.")
    if command.get("deviceId") != device.get("deviceId"):
        _fail("Failed command did not lock to the paired device.")
    if command.get("claimedAt") is None:
        _fail("Failed command is missing claimedAt.")
    if command.get("result") is not None:
        _fail("Failed command unexpectedly recorded a result payload.")
    error = str(command.get("error") or "")
    if MISSING_RECORD_ID not in error:
        _fail(f"Failed command error does not mention {MISSING_RECORD_ID!r}: {error!r}.")
    expected_summary = f"Review failed memory.review.confirm command {COMMAND_ID}"
    if approval.get("summary") != expected_summary:
        _fail(f"Unexpected approval summary: {approval.get('summary')!r}.")
    if approval.get("status") != "pending":
        _fail(f"Expected pending approval reminder, found {approval.get('status')!r}.")
    if approval.get("requiredFlags") != ["repo-write", "external-write"]:
        _fail(f"Unexpected approval required flags: {approval.get('requiredFlags')!r}.")
    if approval.get("userId") != PROOF_USER_ID:
        _fail("Approval reminder was not recorded for the proof user.")

    return {
        "deviceId": device["deviceId"],
        "commandId": command["commandId"],
        "commandStatus": command["status"],
        "error": error,
        "approvalStatus": approval["status"],
        "approvalSummary": approval["summary"],
        "approvalRequiredFlags": approval["requiredFlags"],
        "connectorTokenStoredLocally": bool(device.get("connectorToken")),
    }


def main() -> int:
    node = resolve_node()
    next_cli = next_cli_path()
    port = find_free_port(3201)
    workspace_dir = REPO_ROOT / ".local" / "work" / "connector-recovery"
    workspace_dir.mkdir(parents=True, exist_ok=True)
    state_path = workspace_dir / "control-plane-state.json"
    connector_config_path = workspace_dir / "connector-config.json"
    state_path.write_text(json.dumps(_seed_state(), indent=2) + "\n", encoding="utf-8")
    if connector_config_path.exists():
        connector_config_path.unlink()

    env = base_env(port, state_path)
    next_env_guard = NextEnvGuard()
    process = start_next_dev(node, next_cli, port, env)
    try:
        fetch_when_ready(process, port, "/")
        control_plane_url = f"http://127.0.0.1:{port}"
        service = TaskAgentService.from_repo(repo_root=REPO_ROOT)
        connector = SkylatticeWebConnector(
            repo_root=REPO_ROOT,
            service=service,
            config=WebConnectorConfig(
                repo_root=REPO_ROOT,
                control_plane_url=None,
                device_id=None,
                connector_token=None,
                device_label=None,
                bridge_base_url="http://127.0.0.1:8000",
                config_path=connector_config_path,
            ),
        )
        pair_payload = connector.pair(
            control_plane_url=control_plane_url,
            pairing_code=PAIRING_CODE,
            device_label="Local recovery proof connector",
        )
        if pair_payload.get("status") != "ok":
            _fail("Connector pairing did not return status ok.")
        poll_payload = connector.poll_once()
        if poll_payload.get("status") != "failed":
            _fail(f"Connector poll_once did not report the expected failed status: {poll_payload}")
        if (poll_payload.get("command") or {}).get("commandId") != COMMAND_ID:
            _fail("Connector did not claim the seeded recovery command.")
        if MISSING_RECORD_ID not in str(poll_payload.get("error") or ""):
            _fail(f"Connector error did not mention {MISSING_RECORD_ID!r}.")
        if (poll_payload.get("recorded") or {}).get("status") != "failed":
            _fail("Control plane did not record the command result as failed.")
        state_summary = _assert_recovery_state(state_path)
    finally:
        stop_process_tree(process, port)
        next_env_guard.restore()

    payload = {
        "status": "ok",
        "scope": "local connector recovery roundtrip",
        "liveHostedAlpha": "not exercised",
        "controlPlaneUrl": control_plane_url,
        "connectorConfigPath": connector_config_path.relative_to(REPO_ROOT).as_posix(),
        "statePath": state_path.relative_to(REPO_ROOT).as_posix(),
        "roundtrip": {
            "pairingClaimed": True,
            "heartbeatRecorded": True,
            "commandClaimed": True,
            "localExecution": "memory.review.confirm",
            "resultRecorded": "failed",
            "approvalPressureRecorded": True,
        },
        "state": state_summary,
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
