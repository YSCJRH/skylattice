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


PAIRING_CODE = "LOCAL123"
COMMAND_ID = "cmd-local-memory-search"
PROOF_USER_ID = "github:local-proof"


def _seed_state() -> dict[str, list[dict[str, Any]]]:
    return {
        "devices": [],
        "pairings": [
            {
                "pairingId": "pairing-local-proof",
                "userId": PROOF_USER_ID,
                "pairingCode": PAIRING_CODE,
                "createdAt": "2026-04-27T10:00:00.000Z",
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
                "kind": "memory.search",
                "status": "queued",
                "createdAt": "2026-04-27T10:01:00.000Z",
                "updatedAt": "2026-04-27T10:01:00.000Z",
                "claimedAt": None,
                "payload": {
                    "query": "local connector roundtrip proof",
                    "limit": 3,
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


def _assert_roundtrip_state(state_path: Path) -> dict[str, Any]:
    state = _load_json(state_path)
    devices = state.get("devices", [])
    pairings = state.get("pairings", [])
    commands = state.get("commands", [])
    if len(devices) != 1:
        _fail(f"Expected exactly one paired device, found {len(devices)}.")
    if len(pairings) != 1:
        _fail(f"Expected exactly one pairing challenge, found {len(pairings)}.")
    if len(commands) != 1:
        _fail(f"Expected exactly one command, found {len(commands)}.")

    device = devices[0]
    pairing = pairings[0]
    command = commands[0]
    if not device.get("connectorToken"):
        _fail("Paired device is missing a connector token in the local control-plane state.")
    if device.get("online") is not True:
        _fail("Connector heartbeat did not mark the paired device online.")
    if not device.get("latestAuthSummary"):
        _fail("Connector heartbeat did not record an auth readiness summary.")
    if pairing.get("claimedAt") is None or pairing.get("deviceId") != device.get("deviceId"):
        _fail("Pairing challenge was not claimed by the connector.")
    if pairing.get("connectorToken") != device.get("connectorToken"):
        _fail("Pairing and device connector tokens diverged.")
    if command.get("commandId") != COMMAND_ID:
        _fail("Unexpected command id after roundtrip.")
    if command.get("status") != "succeeded":
        _fail(f"Expected command status succeeded, found {command.get('status')!r}.")
    if command.get("deviceId") != device.get("deviceId"):
        _fail("Claimed command did not lock to the paired device.")
    if command.get("claimedAt") is None:
        _fail("Claimed command is missing claimedAt.")
    result = command.get("result")
    if not isinstance(result, dict) or not isinstance(result.get("records"), list):
        _fail("Recorded memory.search result does not include a records list.")
    if command.get("error") is not None:
        _fail(f"Expected no command error, found {command.get('error')!r}.")

    return {
        "deviceId": device["deviceId"],
        "commandId": command["commandId"],
        "commandStatus": command["status"],
        "resultRecordCount": len(result["records"]),
        "connectorTokenStoredLocally": bool(device.get("connectorToken")),
        "latestAuthSummary": device.get("latestAuthSummary"),
    }


def main() -> int:
    node = resolve_node()
    next_cli = next_cli_path()
    port = find_free_port(3191)
    workspace_dir = REPO_ROOT / ".local" / "work" / "connector-roundtrip"
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
            device_label="Local proof connector",
        )
        if pair_payload.get("status") != "ok":
            _fail("Connector pairing did not return status ok.")
        poll_payload = connector.poll_once()
        if poll_payload.get("status") != "ok":
            _fail(f"Connector poll_once did not complete successfully: {poll_payload}")
        if (poll_payload.get("command") or {}).get("commandId") != COMMAND_ID:
            _fail("Connector did not claim the seeded command.")
        if (poll_payload.get("recorded") or {}).get("status") != "succeeded":
            _fail("Control plane did not record the command result as succeeded.")
        state_summary = _assert_roundtrip_state(state_path)
    finally:
        stop_process_tree(process, port)
        next_env_guard.restore()

    payload = {
        "status": "ok",
        "scope": "local connector HTTP roundtrip",
        "liveHostedAlpha": "not exercised",
        "controlPlaneUrl": control_plane_url,
        "connectorConfigPath": connector_config_path.relative_to(REPO_ROOT).as_posix(),
        "statePath": state_path.relative_to(REPO_ROOT).as_posix(),
        "roundtrip": {
            "pairingClaimed": True,
            "heartbeatRecorded": True,
            "commandClaimed": True,
            "localExecution": "memory.search",
            "resultRecorded": True,
        },
        "state": state_summary,
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
