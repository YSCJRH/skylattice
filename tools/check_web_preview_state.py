from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PREVIEW_STATE_PATH = REPO_ROOT / "examples" / "redacted" / "web-app-preview-state.json"
GUEST_USER_ID = "guest@skylattice.local"


def load_preview_state(path: Path = PREVIEW_STATE_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_preview_state(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    required_keys = ("devices", "pairings", "commands", "approvals")
    for key in required_keys:
        if key not in payload:
            errors.append(f"Missing top-level key: {key}")
        elif not isinstance(payload[key], list):
            errors.append(f"Top-level key {key} must be a list.")

    if errors:
        return errors

    devices = payload["devices"]
    pairings = payload["pairings"]
    commands = payload["commands"]
    approvals = payload["approvals"]

    if not devices:
        errors.append("Preview state must include at least one device.")
    if not pairings:
        errors.append("Preview state must include at least one pairing.")
    if not commands:
        errors.append("Preview state must include at least one command.")
    if not approvals:
        errors.append("Preview state must include at least one approval.")

    device_ids = {item.get("deviceId") for item in devices if isinstance(item, dict)}
    command_kinds = {item.get("kind") for item in commands if isinstance(item, dict)}

    if not any(isinstance(item, dict) and item.get("online") is True for item in devices):
        errors.append("Preview state should include at least one online device.")

    for collection_name, items in (
        ("devices", devices),
        ("pairings", pairings),
        ("commands", commands),
        ("approvals", approvals),
    ):
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"{collection_name}[{index}] must be an object.")
                continue
            user_id = item.get("userId")
            if user_id != GUEST_USER_ID:
                errors.append(f"{collection_name}[{index}] has unexpected userId {user_id!r}.")

    for index, pairing in enumerate(pairings):
        if not isinstance(pairing, dict):
            continue
        claimed_at = pairing.get("claimedAt")
        device_id = pairing.get("deviceId")
        if claimed_at and device_id not in device_ids:
            errors.append(f"pairings[{index}] references unknown deviceId {device_id!r}.")
        if claimed_at is None and device_id is not None:
            errors.append(f"pairings[{index}] is pending but still references a deviceId.")

    for index, command in enumerate(commands):
        if not isinstance(command, dict):
            continue
        device_id = command.get("deviceId")
        if device_id is not None and device_id not in device_ids:
            errors.append(f"commands[{index}] references unknown deviceId {device_id!r}.")
        result = command.get("result")
        if isinstance(result, dict):
            output_path = result.get("output_path")
            if output_path is not None and (not isinstance(output_path, str) or not output_path.startswith(".local/")):
                errors.append(f"commands[{index}] has a non-local preview output_path {output_path!r}.")

    expected_command_kinds = {"task.run", "radar.scan", "memory.search"}
    missing_kinds = sorted(kind for kind in expected_command_kinds if kind not in command_kinds)
    if missing_kinds:
        errors.append(f"Preview state is missing representative command kinds: {missing_kinds}.")

    if not any(isinstance(item, dict) and item.get("status") == "pending" for item in approvals):
        errors.append("Preview state should include at least one pending approval.")

    return errors


def main() -> int:
    payload = load_preview_state()
    errors = validate_preview_state(payload)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("web-app-preview-state.json is structurally valid.")
    print(
        json.dumps(
            {
                "devices": len(payload["devices"]),
                "pairings": len(payload["pairings"]),
                "commands": len(payload["commands"]),
                "approvals": len(payload["approvals"]),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
