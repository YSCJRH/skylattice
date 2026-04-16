from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from skylattice.actions import GitHubAdapter  # noqa: E402
from skylattice.providers import OpenAIProvider  # noqa: E402


def run_selected_smokes(*, provider: str) -> dict[str, object]:
    selected = ("github", "openai") if provider == "all" else (provider,)
    results: dict[str, object] = {}
    for item in selected:
        if item == "github":
            results["github"] = GitHubAdapter().smoke_check()
        elif item == "openai":
            results["openai"] = OpenAIProvider(repo_root=REPO_ROOT).smoke_check()
        else:
            raise ValueError(f"Unsupported provider: {item}")
    return {
        "status": "ok",
        "selected": list(selected),
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run read-only authenticated smoke checks for Skylattice adapters.")
    parser.add_argument("--provider", choices=["github", "openai", "all"], default="all")
    args = parser.parse_args()
    try:
        payload = run_selected_smokes(provider=args.provider)
    except (RuntimeError, ValueError) as exc:
        json.dump({"status": "error", "error": str(exc), "selected": [args.provider]}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 1
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
