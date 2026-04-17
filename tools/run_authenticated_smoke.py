from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from skylattice.actions import GitHubAdapter  # noqa: E402
from skylattice.kernel import load_kernel_config  # noqa: E402
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


def _build_smoke_remediation(*, provider: str) -> list[str]:
    remediation: list[str] = ["Run `python -m skylattice.cli doctor auth` for a read-only capability report."]
    if provider in {"github", "all"}:
        kernel = load_kernel_config(REPO_ROOT)
        diagnostics = GitHubAdapter.inspect_local_auth(repo_root=REPO_ROOT)
        if diagnostics["gh_auth_logged_in"]:
            remediation.append(
                "If you want Skylattice to use the current `gh` login state, run "
                "`python -m skylattice.cli doctor github-bridge --format env` and export the printed vars explicitly."
            )
        if not str(os.environ.get("SKYLATTICE_GITHUB_REPOSITORY", "")).strip() and not str(kernel.runtime.remote_ledger).strip():
            detected = str(diagnostics.get("repo_hint_origin_detected") or "").strip()
            if detected:
                remediation.append(
                    f"`origin` suggests `{detected}`, but Skylattice will not adopt it automatically. Export SKYLATTICE_GITHUB_REPOSITORY explicitly."
                )
            else:
                remediation.append("Set SKYLATTICE_GITHUB_REPOSITORY explicitly before GitHub-backed smoke checks.")
    if provider in {"openai", "all"} and not str(os.environ.get("OPENAI_API_KEY", "")).strip():
        remediation.append("Set OPENAI_API_KEY explicitly before OpenAI smoke checks.")
    return remediation


def main() -> int:
    parser = argparse.ArgumentParser(description="Run read-only authenticated smoke checks for Skylattice adapters.")
    parser.add_argument("--provider", choices=["github", "openai", "all"], default="all")
    args = parser.parse_args()
    try:
        payload = run_selected_smokes(provider=args.provider)
    except (RuntimeError, ValueError) as exc:
        error_payload = {"status": "error", "error": str(exc), "selected": [args.provider]}
        remediation = _build_smoke_remediation(provider=args.provider)
        if remediation:
            error_payload["remediation"] = remediation
        json.dump(error_payload, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 1
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
