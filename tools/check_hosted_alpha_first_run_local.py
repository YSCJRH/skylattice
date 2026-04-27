from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from check_web_preview_state import load_preview_state, validate_preview_state

from skylattice.runtime import TaskAgentService
from skylattice.web import SkylatticeWebConnector
from skylattice.web.config import WebConnectorConfig


REPO_ROOT = Path(__file__).resolve().parents[1]

HOSTED_ENV_KEYS = {
    "DATABASE_URL",
    "GITHUB_ID",
    "GITHUB_SECRET",
    "NEXTAUTH_SECRET",
    "NEXTAUTH_URL",
    "NEXT_PUBLIC_SKYLATTICE_APP_URL",
    "NEXT_PUBLIC_VERCEL_PROJECT_PRODUCTION_URL",
    "SKYLATTICE_CONTROL_PLANE_DATABASE_URL",
    "SKYLATTICE_HOSTED_ALPHA",
    "VERCEL_ENV",
    "VERCEL_PROJECT_PRODUCTION_URL",
    "VERCEL_URL",
}


def _fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def _local_hosted_env() -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if key.upper() not in HOSTED_ENV_KEYS
    }
    env["NEXT_PUBLIC_SKYLATTICE_APP_URL"] = "http://localhost:3000"
    return env


def _run_hosted_alpha_check() -> dict[str, Any]:
    node = shutil.which("node")
    if not node:
        _fail("Unable to locate node on PATH for Hosted Alpha readiness check.")

    completed = subprocess.run(
        [node, "tools/check_hosted_alpha_setup.mjs"],
        cwd=REPO_ROOT,
        env=_local_hosted_env(),
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        _fail(f"Hosted Alpha readiness check did not return JSON: {exc}")

    required_blockers = {
        "NEXT_PUBLIC_SKYLATTICE_APP_URL still points at localhost.",
        "GitHub OAuth env vars are incomplete.",
        "DATABASE_URL or SKYLATTICE_CONTROL_PLANE_DATABASE_URL is missing.",
        "NEXTAUTH_URL is missing for hosted auth callbacks.",
    }
    blockers = set(payload.get("blockers", []))
    missing = sorted(required_blockers - blockers)
    if completed.returncode == 0:
        _fail("Local Hosted Alpha readiness check unexpectedly passed.")
    if payload.get("ready") is True:
        _fail("Local Hosted Alpha readiness reported ready=true.")
    if payload.get("hostedAlpha") is True:
        _fail("Local Hosted Alpha readiness reported hostedAlpha=true.")
    if missing:
        _fail(f"Local Hosted Alpha readiness is missing expected blockers: {missing}")

    return {
        "status": "blocked-as-expected",
        "returncode": completed.returncode,
        "payload": payload,
    }


def _check_preview_state() -> dict[str, int]:
    payload = load_preview_state()
    errors = validate_preview_state(payload)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        raise SystemExit(1)
    return {
        "devices": len(payload["devices"]),
        "pairings": len(payload["pairings"]),
        "commands": len(payload["commands"]),
        "approvals": len(payload["approvals"]),
    }


def _check_unpaired_connector(service: TaskAgentService) -> dict[str, Any]:
    config = WebConnectorConfig(
        repo_root=REPO_ROOT,
        control_plane_url=None,
        device_id=None,
        connector_token=None,
        device_label=None,
        bridge_base_url="http://127.0.0.1:8000",
        config_path=REPO_ROOT / ".local" / "work" / "first-run-proof-loop" / "unpaired-web-control-plane.json",
    )
    connector = SkylatticeWebConnector(repo_root=REPO_ROOT, service=service, config=config)
    status = connector.status_report()
    connector_status = status["connector"]
    if not isinstance(connector_status, dict) or connector_status.get("paired") is not False:
        _fail("Injected local connector config did not report paired=false.")

    try:
        connector.heartbeat()
    except RuntimeError as exc:
        error = str(exc)
    else:
        _fail("Unpaired connector heartbeat unexpectedly succeeded.")

    if "Connector is not paired yet" not in error:
        _fail(f"Unpaired connector heartbeat returned unexpected error: {error}")

    return {
        "status": "blocked-as-expected",
        "connector": connector_status,
        "heartbeat_error": error,
        "doctor_status": status["doctor"]["status"],
    }


def _check_auth_preflight(service: TaskAgentService) -> dict[str, Any]:
    payload = service.auth_preflight_report()
    if payload.get("status") != "ok":
        _fail("Auth preflight did not report status=ok.")
    auth = payload.get("auth", {})
    capabilities = payload.get("capabilities", {})
    return {
        "status": payload["status"],
        "gh_cli_available": bool(isinstance(auth, dict) and auth.get("gh_cli_available")),
        "github_token_env_present": bool(isinstance(auth, dict) and auth.get("github_token_env_present")),
        "openai_key_env_present": bool(isinstance(auth, dict) and auth.get("openai_key_env_present")),
        "planner_available": bool(isinstance(capabilities, dict) and capabilities.get("planner_available")),
        "github_available": bool(isinstance(capabilities, dict) and capabilities.get("github_available")),
    }


def main() -> int:
    service = TaskAgentService.from_repo(repo_root=REPO_ROOT)
    summary = {
        "preview": _check_preview_state(),
        "hosted_alpha_readiness": _run_hosted_alpha_check(),
        "connector": _check_unpaired_connector(service),
        "auth": _check_auth_preflight(service),
    }
    print("Hosted Alpha local first-run proof harness passed.")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
