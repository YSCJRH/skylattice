from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

PROOF_STEPS = [
    ("first-run", "tools/check_hosted_alpha_first_run_local.py"),
    ("cockpit-ui", "tools/check_web_control_cockpit_ui.py"),
    ("connector-roundtrip", "tools/check_web_connector_roundtrip_local.py"),
    ("connector-recovery", "tools/check_web_connector_recovery_local.py"),
]


def run_step(name: str, script: str) -> dict[str, object]:
    print(f"=== web local proof: {name} ===", flush=True)
    completed = subprocess.run(
        [sys.executable, script],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if completed.stdout:
        print(completed.stdout, end="" if completed.stdout.endswith("\n") else "\n")
    if completed.stderr:
        print(completed.stderr, file=sys.stderr, end="" if completed.stderr.endswith("\n") else "\n")
    return {
        "name": name,
        "script": script,
        "returncode": completed.returncode,
        "status": "ok" if completed.returncode == 0 else "failed",
    }


def main() -> int:
    results = [run_step(name, script) for name, script in PROOF_STEPS]
    failures = [result for result in results if result["returncode"] != 0]
    payload = {
        "status": "failed" if failures else "ok",
        "scope": "local Hosted Alpha proof suite",
        "liveHostedAlpha": "not exercised",
        "steps": results,
    }
    print(json.dumps(payload, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
