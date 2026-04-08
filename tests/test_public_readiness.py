from __future__ import annotations

import re
import subprocess
from pathlib import Path

import yaml

from skylattice.storage import LocalPaths

REPO_ROOT = Path(__file__).resolve().parents[1]

BANNED_TEXT_PATTERNS = {
    "windows_d_drive": re.compile("D:" + re.escape("\\")),
    "windows_user_home": re.compile(r"C:\\Users\\"),
    "mac_user_home": re.compile("/" + "Users" + "/"),
    "linux_user_home": re.compile("/" + "home" + "/"),
    "sandbox_host": re.compile("Codex" + "Sandbox" + "Online"),
}
SECRET_PATTERNS = {
    "openai_key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "github_pat": re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    "github_classic_pat": re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    "google_api_key": re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b"),
    "bearer_literal": re.compile(r"Bearer [A-Za-z0-9._-]{20,}"),
}
BINARY_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf"}


def _tracked_files() -> list[str]:
    completed = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in completed.stdout.splitlines() if line]


def _read_text(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8", errors="ignore")


def test_tracked_defaults_are_public_safe() -> None:
    payload = yaml.safe_load((REPO_ROOT / "configs" / "agent" / "defaults.yaml").read_text(encoding="utf-8"))

    assert payload["agent"]["owner"] == "local-user"
    assert payload["user_model"]["user_id"] == "local-user"
    assert payload["user_model"]["display_name"] == "user"
    assert payload["user_model"]["timezone"] == "UTC"
    assert payload["runtime"]["remote_ledger"] == ""


def test_local_path_summary_is_relative() -> None:
    paths = LocalPaths.from_repo_root(REPO_ROOT).to_dict()

    assert paths["repo_root"] == "."
    assert paths["state_root"] == ".local/state"
    assert paths["overrides_root"] == ".local/overrides"


def test_publishable_tree_has_no_local_paths_or_host_fingerprints() -> None:
    violations: list[str] = []

    for relative_path in _tracked_files():
        if Path(relative_path).suffix.lower() in BINARY_SUFFIXES:
            continue
        text = _read_text(relative_path)
        for label, pattern in BANNED_TEXT_PATTERNS.items():
            if pattern.search(text):
                violations.append(f"{relative_path}: {label}")

    assert not violations, "Unexpected local path or host fingerprint found:\n" + "\n".join(violations)


def test_publishable_tree_has_no_secret_literals() -> None:
    violations: list[str] = []

    for relative_path in _tracked_files():
        if Path(relative_path).suffix.lower() in BINARY_SUFFIXES:
            continue
        text = _read_text(relative_path)
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                violations.append(f"{relative_path}: {label}")

    assert not violations, "Unexpected secret-like literal found:\n" + "\n".join(violations)


def test_git_does_not_track_local_runtime_artifacts() -> None:
    tracked_local = subprocess.run(
        ["git", "ls-files", ".local"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    tracked_files = _tracked_files()

    assert tracked_local == ""
    assert not any(path.startswith(".local/") for path in tracked_files)
    assert not any(path.endswith((".db", ".sqlite", ".sqlite3", ".log")) for path in tracked_files)