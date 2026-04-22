from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def resolve_npm() -> str:
    candidates = ("npm", "npm.cmd") if os.name == "nt" else ("npm",)
    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    raise FileNotFoundError("Unable to locate npm on PATH for the web preview helper.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Skylattice web app in read-only demo preview mode.",
    )
    parser.add_argument(
        "mode",
        choices=("dev", "build", "start"),
        help="Which apps/web npm script to run with preview mode enabled.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    env = os.environ.copy()
    env["NEXT_PUBLIC_SKYLATTICE_DEMO_PREVIEW"] = "1"

    command = [resolve_npm(), "run", args.mode, "--workspace", "apps/web"]
    completed = subprocess.run(command, cwd=REPO_ROOT, env=env)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
