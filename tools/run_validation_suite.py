from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from skylattice.runtime import load_task_validation_policy  # noqa: E402


def main() -> int:
    policy = load_task_validation_policy(REPO_ROOT)
    for command in policy.allowed_commands:
        print(f"> {command}")
        completed = subprocess.run(
            [policy.runner, "-Command", command],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.stdout:
            print(completed.stdout, end="")
        if completed.stderr:
            print(completed.stderr, end="", file=sys.stderr)
        if completed.returncode != 0:
            return completed.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
