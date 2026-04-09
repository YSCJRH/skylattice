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


def test_task_validation_config_defines_windows_baseline() -> None:
    payload = yaml.safe_load((REPO_ROOT / "configs" / "task" / "validation.yaml").read_text(encoding="utf-8"))

    assert payload["runner"] == "powershell"
    assert payload["allowed_commands"] == [
        "python -m pytest -q",
        "python -m compileall src/skylattice",
        "python -m skylattice.cli doctor",
        "git status --short",
    ]


def test_public_engineering_baseline_files_exist() -> None:
    required = [
        ".github/workflows/ci.yml",
        ".github/workflows/pages.yml",
        ".github/PULL_REQUEST_TEMPLATE.md",
        ".github/ISSUE_TEMPLATE/bug_report.md",
        ".github/ISSUE_TEMPLATE/feature_request.md",
        ".github/ISSUE_TEMPLATE/early_feedback.md",
        ".github/ISSUE_TEMPLATE/config.yml",
        "tools/run_validation_suite.py",
        "mkdocs.yml",
        "CITATION.cff",
        "CHANGELOG.md",
        "docs/index.md",
        "docs/what-is-skylattice.md",
        "docs/quickstart.md",
        "docs/overview.md",
        "docs/use-cases.md",
        "docs/comparison.md",
        "docs/faq.md",
        "docs/proof.md",
        "docs/ai-distribution-ops.md",
        "docs/ai-search-benchmark.md",
        "docs/releases/v0.2.0-public-preview.md",
        "docs/releases/v0-2-0.md",
        "docs/robots.txt",
        "docs/sitemap.xml",
        "docs/llms.txt",
        "docs/llms-full.txt",
        "docs/assets/doctor-snapshot.svg",
        "docs/assets/task-run-snapshot.svg",
        "docs/assets/runtime-architecture.svg",
        "docs/assets/social-preview.svg",
        "docs/assets/social-preview.png",
        "docs/assets/terminal-demo.svg",
        "docs/zh/index.md",
        "docs/zh/what-is-skylattice.md",
        "docs/zh/quickstart.md",
        "docs/zh/use-cases.md",
        "docs/zh/comparison.md",
        "docs/zh/faq.md",
        "docs/zh/proof.md",
        "docs/zh/releases/v0-2-0.md",
        "examples/redacted/doctor-output.json",
        "examples/redacted/task-run-sample.md",
        "examples/redacted/task-run-sample.json",
        "examples/redacted/radar-sample.md",
        "examples/redacted/radar-run-sample.json",
    ]

    assert all((REPO_ROOT / relative_path).exists() for relative_path in required)


def test_public_positioning_surfaces_are_present() -> None:
    readme = _read_text("README.md")
    pyproject = _read_text("pyproject.toml")

    for phrase in [
        "Why Star Skylattice",
        "5-Minute No-Credential Quick Start",
        "Token-Enabled Workflow",
        "Sample Outputs",
        "Public Site",
        "docs and AI-friendly landing pages",
        "python -m mkdocs build --strict",
        "homepageUrl",
    ]:
        assert phrase in readme

    assert "Local-first AI agent runtime for persistent memory, governed repo tasks, and Git-native self-improvement." in pyproject
    assert 'Homepage = "https://yscjrh.github.io/skylattice/"' in pyproject
    assert 'Documentation = "https://yscjrh.github.io/skylattice/"' in pyproject


def test_public_site_metadata_is_tracked() -> None:
    mkdocs_config = yaml.safe_load(_read_text("mkdocs.yml"))
    citation = yaml.safe_load(_read_text("CITATION.cff"))
    pyproject = _read_text("pyproject.toml")

    assert mkdocs_config["site_url"] == "https://yscjrh.github.io/skylattice/"
    assert mkdocs_config["repo_url"] == "https://github.com/YSCJRH/skylattice"
    assert mkdocs_config["extra"]["social_image"] == "assets/social-preview.png"
    assert citation["title"] == "Skylattice"
    assert citation["version"] == "0.2.0"
    assert citation["url"] == "https://yscjrh.github.io/skylattice/"
    assert "mkdocs>=1.6,<2.0" in pyproject
    assert "mkdocs-material>=9.6,<10.0" in pyproject


def test_ai_discovery_files_allow_public_crawlers() -> None:
    robots = _read_text("docs/robots.txt")
    llms = _read_text("docs/llms.txt")
    llms_full = _read_text("docs/llms-full.txt")

    assert "User-agent: *" in robots
    assert "User-agent: OAI-SearchBot" in robots
    assert "User-agent: GPTBot" in robots
    assert "Allow: /" in robots
    assert "Sitemap: https://yscjrh.github.io/skylattice/sitemap.xml" in robots
    assert "https://yscjrh.github.io/skylattice/faq/" in llms
    assert "https://yscjrh.github.io/skylattice/zh/faq/" in llms_full
    assert "https://github.com/YSCJRH/skylattice" in llms


def test_sitemap_declares_core_pages_and_language_alternates() -> None:
    sitemap = _read_text("docs/sitemap.xml")

    for loc in [
        "https://yscjrh.github.io/skylattice/",
        "https://yscjrh.github.io/skylattice/what-is-skylattice/",
        "https://yscjrh.github.io/skylattice/quickstart/",
        "https://yscjrh.github.io/skylattice/use-cases/",
        "https://yscjrh.github.io/skylattice/comparison/",
        "https://yscjrh.github.io/skylattice/faq/",
        "https://yscjrh.github.io/skylattice/proof/",
        "https://yscjrh.github.io/skylattice/releases/v0-2-0/",
    ]:
        assert f"<loc>{loc}</loc>" in sitemap

    assert 'hreflang="zh-CN"' in sitemap
    assert 'https://yscjrh.github.io/skylattice/zh/' in sitemap
    assert 'https://yscjrh.github.io/skylattice/zh/releases/v0-2-0/' in sitemap


def test_ai_distribution_docs_cover_benchmark_and_manual_ops() -> None:
    ops = _read_text("docs/ai-distribution-ops.md")
    benchmark = _read_text("docs/ai-search-benchmark.md")

    assert "homepageUrl" in ops
    assert "social preview" in ops
    assert "Google Search Console" in ops
    assert "Bing Webmaster Tools" in ops
    assert "ChatGPT Search" in benchmark
    assert "Perplexity" in benchmark
    assert "Gemini" in benchmark
    assert "Claude Web" in benchmark
    assert "Day 0" in benchmark and "Day 14" in benchmark and "Day 30" in benchmark


def test_post_release_docs_do_not_keep_pre_release_todo_text() -> None:
    readme = _read_text("README.md")
    release_notes = _read_text("docs/releases/v0.2.0-public-preview.md")
    overview = _read_text("docs/overview.md")
    changelog = _read_text("CHANGELOG.md")

    stale_phrases = [
        "once these changes are published to GitHub",
        "once the repo changes are published to the remote",
        "apply the repository description and topics above in GitHub settings",
        "publish this release text as the first GitHub release body",
        "not a published GitHub release yet",
    ]

    combined = "\n".join([readme, release_notes, overview, changelog])
    assert not any(phrase in combined for phrase in stale_phrases)


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
