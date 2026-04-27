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
CHINESE_EXPECTATIONS = {
    "docs/zh/index.md": "???? AI Agent ???",
    "docs/zh/what-is-skylattice.md": "??? Skylattice",
    "docs/zh/quickstart.md": "5 ???????",
    "docs/zh/app-preview.md": "Skylattice App Preview",
    "docs/zh/comparison.md": "???????? Agent ??",
    "docs/zh/faq.md": "Skylattice ??????",
    "docs/zh/proof.md": "??????? Skylattice ???????",
    "docs/zh/use-cases.md": "????",
    "docs/zh/releases/v0-4-1.md": "\u5f53\u524d\u7a33\u5b9a\u7248\u672c",
    "docs/zh/releases/v0-4-0.md": "\u5f53\u524d\u7a33\u5b9a\u7248\u672c",
    "docs/zh/releases/v0-3-1.md": "\u5f53\u524d\u7a33\u5b9a\u7248\u672c",
    "docs/zh/releases/v0-3-0.md": "\u5f53\u524d\u7a33\u5b9a\u7248\u672c",
    "docs/zh/releases/v0-2-2.md": "\u5f53\u524d\u7a33\u5b9a\u7248\u672c",
}
def _tracked_files() -> list[str]:
    completed = subprocess.run(["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True, check=True)
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
    assert payload["default_profile"] == "baseline"
    assert [item["id"] for item in payload["commands"]] == [
        "pytest",
        "compileall",
        "doctor",
        "git-status",
    ]
    assert payload["profiles"]["baseline"] == [
        "pytest",
        "compileall",
        "doctor",
        "git-status",
    ]


def test_radar_schedule_config_defines_windows_first_baseline() -> None:
    payload = yaml.safe_load((REPO_ROOT / "configs" / "radar" / "schedule.yaml").read_text(encoding="utf-8"))
    assert payload["default_schedule"] == "weekly-github"
    assert payload["schedules"]["weekly-github"]["enabled"] is True
    assert payload["schedules"]["weekly-github"]["window"] == "weekly"
    assert payload["schedules"]["weekly-github"]["windows_task"]["folder"] == "\\Skylattice"
    assert payload["schedules"]["weekly-github"]["windows_task"]["trigger_command"] == "New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 9am"


def test_radar_provider_config_reports_gitlab_as_second_live_provider() -> None:
    payload = yaml.safe_load((REPO_ROOT / "configs" / "radar" / "providers.yaml").read_text(encoding="utf-8"))
    assert payload["default_provider"] == "github"
    assert payload["providers"]["github"]["enabled"] is True
    assert payload["providers"]["github"]["kind"] == "github"
    assert payload["providers"]["gitlab"]["enabled"] is True
    assert payload["providers"]["gitlab"]["kind"] == "gitlab"


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
        "tools/run_authenticated_smoke.py",
        "tools/run_web_preview.py",
        "tools/check_web_preview_state.py",
        "tools/check_hosted_alpha_setup.mjs",
        "tools/bootstrap_hosted_alpha_db.mjs",
        "tools/check_hosted_alpha_first_run_local.py",
        "tools/check_web_control_cockpit_ui.py",
        "package.json",
        "apps/web/README.md",
        "apps/web/.env.example",
        "apps/web/package.json",
        "apps/web/sql/hosted-alpha-bootstrap.sql",
        "apps/web/app/page.tsx",
        "apps/web/app/dashboard/page.tsx",
        "apps/web/lib/control-plane/store.ts",
        "apps/web/lib/control-plane/schema.ts",
        "apps/web/app/api/control-plane/commands/route.ts",
        "tests/test_actions_gitlab.py",
        "tests/test_web_bridge.py",
        "tools/upload_github_social_preview.py",
        "mkdocs.yml",
        "CITATION.cff",
        "CHANGELOG.md",
        "docs/index.md",
        "docs/what-is-skylattice.md",
        "docs/quickstart.md",
        "docs/app-preview.md",
        "docs/web-control-plane.md",
        "docs/overview.md",
        "docs/use-cases.md",
        "docs/comparison.md",
        "docs/faq.md",
        "docs/proof.md",
        "docs/radar-scheduling.md",
        "docs/ops/hosted-alpha-runbook.md",
        "docs/ops/radar-weekly-validation-template.md",
        "docs/ai-distribution-ops.md",
        "docs/ai-search-benchmark.md",
        "docs/memory-model.md",
        "docs/outreach/authority-program.md",
        "docs/outreach/posting-runbook.md",
        "docs/outreach/directory-blurbs.md",
        "docs/outreach/launch-en.md",
        "docs/outreach/launch-zh.md",
        "docs/outreach/category-post.md",
        "docs/outreach/distribution-targets.md",
        "docs/outreach/community-posts.md",
        "docs/releases/v0.4.1-stable.md",
        "docs/releases/v0-4-1.md",
        "docs/releases/v0.4.0-stable.md",
        "docs/releases/v0-4-0.md",
        "docs/releases/v0.3.1-stable.md",
        "docs/releases/v0-3-1.md",
        "docs/releases/v0.3.0-stable.md",
        "docs/releases/v0-3-0.md",
        "docs/releases/v0.2.2-stable.md",
        "docs/releases/v0-2-2.md",
        "docs/releases/v0.2.1-stable.md",
        "docs/releases/v0-2-1.md",
        "docs/releases/v0.2.0-public-preview.md",
        "docs/releases/v0-2-0.md",
        "docs/robots.txt",
        "docs/sitemap.xml",
        "docs/llms.txt",
        "docs/llms-full.txt",
        "docs/assets/doctor-snapshot.svg",
        "docs/assets/task-run-snapshot.svg",
        "docs/assets/runtime-architecture.svg",
        "docs/assets/app-preview-snapshot.svg",
        "docs/assets/cover-hero.svg",
        "docs/assets/social-preview.svg",
        "docs/assets/social-preview.png",
        "docs/assets/terminal-demo.svg",
        "docs/zh/index.md",
        "docs/zh/what-is-skylattice.md",
        "docs/zh/quickstart.md",
        "docs/zh/app-preview.md",
        "docs/zh/use-cases.md",
        "docs/zh/comparison.md",
        "docs/zh/faq.md",
        "docs/zh/proof.md",
        "docs/zh/releases/v0-4-1.md",
        "docs/zh/releases/v0-4-0.md",
        "docs/zh/releases/v0-3-1.md",
        "docs/zh/releases/v0-3-0.md",
        "docs/zh/releases/v0-2-2.md",
        "docs/zh/releases/v0-2-1.md",
        "docs/zh/releases/v0-2-0.md",
        "docs/tasks/discoverability-optimization-30-day.md",
        "docs/tasks/memory-review-retrieval.md",
        "docs/tasks/phase-4-recovery-hardening.md",
        "docs/tasks/phase-4-validation-envelope.md",
        "docs/tasks/phase-4-repo-primitives.md",
        "docs/tasks/phase-4-github-sync-context.md",
        "docs/tasks/phase-4-destructive-repo-ops.md",
        "docs/tasks/phase-4-github-collaboration-sync.md",
        "docs/tasks/phase-4-closeout-phase-5-entry.md",
        "docs/tasks/phase-5-schedule-operator-runbook.md",
        "docs/tasks/phase-5-provider-contract.md",
        "docs/tasks/phase-5-identity-contract.md",
        "docs/tasks/phase-5-scheduled-provenance.md",
        "docs/tasks/phase-5-adoption-identity.md",
        "docs/tasks/phase-5-evidence-taxonomy.md",
        "docs/tasks/phase-5-schedule-validation-report.md",
        "docs/tasks/phase-5-validation-record-template.md",
        "docs/tasks/gitlab-second-live-provider.md",
        "docs/tasks/web-product-upgrade.md",
        "docs/tasks/hosted-alpha-production-readiness.md",
        "docs/adrs/0005-review-driven-memory-operations.md",
        "docs/adrs/0006-resume-safe-external-sync.md",
        "docs/adrs/0007-tracked-validation-envelope.md",
        "docs/adrs/0008-non-destructive-repo-ops.md",
        "docs/adrs/0009-github-sync-context-and-preflight.md",
        "docs/adrs/0010-explicit-destructive-repo-approval.md",
        "docs/adrs/0011-github-collaboration-sync-hardening.md",
        "docs/adrs/0012-local-scheduler-and-radar-source-abstraction.md",
        "docs/adrs/0013-tracked-radar-provider-contract.md",
        "docs/adrs/0014-provider-neutral-radar-identity.md",
        "docs/adrs/0015-provider-neutral-adoption-matching.md",
        "docs/adrs/0016-normalized-radar-evidence-taxonomy.md",
        "docs/adrs/0017-gitlab-second-live-provider.md",
        "docs/adrs/0018-hosted-web-control-plane-and-local-bridge.md",
        "configs/radar/providers.yaml",
        "configs/radar/schedule.yaml",
        "evals/ai-search/_template.md",
        "evals/ai-search/2026-04-09-baseline.md",
        "examples/redacted/doctor-output.json",
        "examples/redacted/task-run-sample.md",
        "examples/redacted/task-run-sample.json",
        "examples/redacted/radar-sample.md",
        "examples/redacted/radar-run-sample.json",
        "examples/redacted/web-app-preview-state.json",
    ]
    assert all((REPO_ROOT / relative_path).exists() for relative_path in required)


def test_ci_and_review_templates_cover_web_preview_proof_validation() -> None:
    ci = _read_text(".github/workflows/ci.yml")
    pr_template = _read_text(".github/PULL_REQUEST_TEMPLATE.md")
    workflow_doc = _read_text("docs/github-workflow.md")
    assert "npm run web:preview:check" in ci
    assert "npm run web:preview:check" in pr_template
    assert "npm run web:preview:check" in workflow_doc


def test_theme_override_localizes_navigation_for_zh_pages() -> None:
    override = _read_text("overrides/main.html")
    for phrase in [
        "window.location.pathname",
        "translations = new Map",
        "What Is Skylattice?",
        "Quick Start",
        "App Preview",
        "Release",
        "System Docs",
    ]:
        assert phrase in override

def test_public_positioning_surfaces_are_present() -> None:
    readme = _read_text("README.md")
    pyproject = _read_text("pyproject.toml")
    for phrase in [
        "Why Star Skylattice",
        "Visual Proof",
        "5-Minute No-Credential Quick Start",
        "Token-Enabled Workflow",
        "Sample Outputs",
        "Public Site",
        "Web Control Plane",
        "skylattice memory ...",
        "skylattice radar schedule ...",
        "docs and AI-friendly landing pages",
        "latest stable release",
        "stable non-pre-release public baseline",
        "python -m mkdocs build --strict",
        "homepageUrl",
        "docs/assets/cover-hero.svg",
        "provider-neutral radar candidate and evidence identity surfaces",
        "GitLab available as a second live radar provider",
        "scheduled radar runs now record `trigger_mode` and `schedule_id`",
        "adoption matching and scoring boosts now prefer provider-neutral source identity",
        "normalized radar evidence taxonomy now uses provider-neutral kind names",
        "radar schedule validate",
        ".local/radar/validations/",
        "tracked note template plus a suggested record path",
        "run_authenticated_smoke.py",
        "read-only authenticated smoke",
        "same-repo hosted web app foundation",
        "Hosted Alpha deployment contract",
        "npm run web:preview",
        "npm run web:preview:check",
        "npm run web:first-run:local",
        "npm run web:cockpit:check",
        "authenticated local bridge endpoints under `/bridge/v1`",
        "`skylattice web status`, `web pair`, and `web connector ...`",
    ]:
        assert phrase in readme
    assert '"web:preview": "python tools/run_web_preview.py dev"' in _read_text("package.json")
    assert '"web:preview:build": "python tools/run_web_preview.py build"' in _read_text("package.json")
    assert '"web:preview:start": "python tools/run_web_preview.py start"' in _read_text("package.json")
    assert '"web:preview:check": "python tools/check_web_preview_state.py"' in _read_text("package.json")
    assert '"web:hosted-alpha:check": "node tools/check_hosted_alpha_setup.mjs"' in _read_text("package.json")
    assert '"web:hosted-alpha:bootstrap": "node tools/bootstrap_hosted_alpha_db.mjs"' in _read_text("package.json")
    assert '"web:first-run:local": "python tools/check_hosted_alpha_first_run_local.py"' in _read_text("package.json")
    assert '"web:cockpit:check": "python tools/check_web_control_cockpit_ui.py"' in _read_text("package.json")
    assert 'version = "0.4.1"' in pyproject
    assert "Local-first AI agent runtime for persistent memory, governed repo tasks, and Git-native self-improvement." in pyproject
    assert 'Homepage = "https://yscjrh.github.io/skylattice/"' in pyproject
    assert 'Documentation = "https://yscjrh.github.io/skylattice/"' in pyproject
    assert "playwright>=1.52,<2.0" in pyproject


def test_runtime_architecture_svg_wraps_long_labels() -> None:
    svg = _read_text("docs/assets/runtime-architecture.svg")
    for unwrapped_phrase in [
        "discovery, experiment, promotion",
        "approval tiers, freeze mode, policy gates",
        "events, runs, layered SQLite-backed memory",
        "docs, prompts, configs, ADRs, CI, examples",
        "audit, collaboration, CI, radar discovery",
        "planning and edit materialization when enabled",
        "Private runtime state lives under .local/. Reviewable behavior stays in tracked files. GitHub helps audit and collaborate, but it is not the runtime truth.",
    ]:
        assert unwrapped_phrase not in svg
    assert svg.count("<tspan") >= 10


def test_public_site_metadata_is_tracked() -> None:
    mkdocs_config = yaml.safe_load(_read_text("mkdocs.yml"))
    citation = yaml.safe_load(_read_text("CITATION.cff"))
    pyproject = _read_text("pyproject.toml")
    assert mkdocs_config["site_url"] == "https://yscjrh.github.io/skylattice/"
    assert mkdocs_config["repo_url"] == "https://github.com/YSCJRH/skylattice"
    assert mkdocs_config["extra"]["social_image"] == "assets/social-preview.png"
    assert citation["title"] == "Skylattice"
    assert citation["version"] == "0.4.1"
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
    assert "https://yscjrh.github.io/skylattice/releases/v0-4-1/" in llms
    assert "https://yscjrh.github.io/skylattice/zh/releases/v0-4-1/" in llms_full
    assert "https://github.com/YSCJRH/skylattice" in llms


def test_sitemap_declares_core_pages_and_language_alternates() -> None:
    sitemap = _read_text("docs/sitemap.xml")
    for loc in [
        "https://yscjrh.github.io/skylattice/",
        "https://yscjrh.github.io/skylattice/what-is-skylattice/",
        "https://yscjrh.github.io/skylattice/quickstart/",
        "https://yscjrh.github.io/skylattice/app-preview/",
        "https://yscjrh.github.io/skylattice/web-control-plane/",
        "https://yscjrh.github.io/skylattice/use-cases/",
        "https://yscjrh.github.io/skylattice/comparison/",
        "https://yscjrh.github.io/skylattice/faq/",
        "https://yscjrh.github.io/skylattice/proof/",
        "https://yscjrh.github.io/skylattice/releases/v0-4-1/",
        "https://yscjrh.github.io/skylattice/releases/v0-4-0/",
        "https://yscjrh.github.io/skylattice/releases/v0-3-1/",
        "https://yscjrh.github.io/skylattice/releases/v0-3-0/",
        "https://yscjrh.github.io/skylattice/releases/v0-2-2/",
        "https://yscjrh.github.io/skylattice/releases/v0-2-1/",
        "https://yscjrh.github.io/skylattice/releases/v0-2-0/",
    ]:
        assert f"<loc>{loc}</loc>" in sitemap
    assert 'hreflang="zh-CN"' in sitemap
    assert 'https://yscjrh.github.io/skylattice/zh/' in sitemap
    assert 'https://yscjrh.github.io/skylattice/zh/releases/v0-4-1/' in sitemap


def test_ai_distribution_docs_cover_weekly_review_loop_and_manual_ops() -> None:
    ops = _read_text("docs/ai-distribution-ops.md")
    benchmark = _read_text("docs/ai-search-benchmark.md")
    baseline = _read_text("evals/ai-search/2026-04-09-baseline.md")
    for phrase in ["homepageUrl", "social preview", "tools/upload_github_social_preview.py", "Google Search Console", "Bing Webmaster Tools", "Agent A", "Agent B", "Agent C", "Agent D", ".local/discoverability/", "evals/ai-search/"]:
        assert phrase in ops
    assert "v0.4.1" in ops
    for phrase in ["English Query Cluster", "Chinese Query Cluster", "Day 0", "Day 7", "Day 14", "Day 30", "isolated agents", "evals/ai-search/"]:
        assert phrase in benchmark
    assert "English non-brand discoverability: `3/10`" in baseline
    assert "Chinese non-brand discoverability: `2/10`" in baseline


def test_release_story_points_at_stable_surface() -> None:
    combined = "\n".join(
        _read_text(path)
        for path in [
            "docs/index.md",
            "docs/what-is-skylattice.md",
            "docs/quickstart.md",
            "docs/faq.md",
            "docs/proof.md",
            "docs/overview.md",
            "README.md",
        ]
    )
    assert "v0.4.1 Stable" in combined
    assert "stable non-pre-release" in combined or "stable release" in combined


def test_post_release_docs_do_not_keep_stale_release_todo_text() -> None:
    combined = "\n".join(
        _read_text(path)
        for path in [
            "README.md",
            "docs/releases/v0.4.1-stable.md",
            "docs/releases/v0-4-1.md",
            "docs/releases/v0.4.0-stable.md",
            "docs/releases/v0-4-0.md",
            "docs/releases/v0.3.1-stable.md",
            "docs/releases/v0-3-1.md",
            "docs/releases/v0.3.0-stable.md",
            "docs/releases/v0-3-0.md",
            "docs/releases/v0.2.2-stable.md",
            "docs/releases/v0-2-2.md",
            "docs/releases/v0.2.1-stable.md",
            "docs/releases/v0.2.0-public-preview.md",
            "docs/releases/v0-2-2.md",
            "docs/releases/v0-2-1.md",
            "docs/releases/v0-2-0.md",
            "docs/overview.md",
            "CHANGELOG.md",
        ]
    )
    stale_phrases = [
        "once these changes are published to GitHub",
        "once the repo changes are published to the remote",
        "apply the repository description and topics above in GitHub settings",
        "publish this release text as the first GitHub release body",
        "not a published GitHub release yet",
        "The next public version should add a non-pre-release tag",
    ]
    assert not any(phrase in combined for phrase in stale_phrases)


def test_chinese_public_pages_are_readable_and_query_aligned() -> None:
    for relative_path, phrase in CHINESE_EXPECTATIONS.items():
        text = _read_text(relative_path)
        assert phrase in text


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
    tracked_local = subprocess.run(["git", "ls-files", ".local"], cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.strip()
    tracked_files = _tracked_files()
    assert tracked_local == ""
    assert not any(path.startswith(".local/") for path in tracked_files)
    assert not any(path.endswith((".db", ".sqlite", ".sqlite3", ".log")) for path in tracked_files)
