from __future__ import annotations

import subprocess
from dataclasses import replace
from pathlib import Path

from fastapi.testclient import TestClient

from skylattice.actions import GitAdapter
from skylattice.api import app, get_task_agent_service
from skylattice.runtime import TaskAgentService
from skylattice.radar.models import normalize_evidence_kind


class LocalPushGitAdapter:
    def __init__(self, repo_root: Path) -> None:
        self.delegate = GitAdapter(repo_root)
        self.push_calls: list[dict[str, str]] = []

    def __getattr__(self, name: str):
        return getattr(self.delegate, name)

    def push(self, branch_name: str, remote: str = "origin") -> str:
        self.push_calls.append({"branch_name": branch_name, "remote": remote})
        return branch_name


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _run(command: list[str], cwd: Path) -> str:
    completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=True)
    return completed.stdout


def create_radar_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "radar-repo"
    repo.mkdir()
    _write(
        repo / "configs" / "agent" / "defaults.yaml",
        """
agent:
  id: skylattice
  codename: skylattice
  version: 0.2.0
  owner: local-user
user_model:
  user_id: local-user
  display_name: user
  timezone: UTC
  interaction_style: concise
relationship:
  role: personal evolvable agent
  promises:
    - protect long-term user interests
  escalation_default: ask-before-repo-or-external-write
mission:
  summary: test mission
  constitution:
    - Local-first runtime before remote convenience.
runtime:
  mode: radar-mvp
  freeze_mode: false
  active_plan: null
  memory_home: .local/memory
  remote_ledger: ""
  autonomy_mode: proactive-low-risk
adapters:
  shell: planned
""".strip(),
    )
    _write(repo / ".gitignore", ".local/\n__pycache__/\n.pytest_cache/\n")
    _write(repo / "README.md", "# Radar Repo\n\nInitial content.\n")
    _write(
        repo / "configs" / "policies" / "governance.yaml",
        """
freeze_mode: false
auto_approve:
  - observe
  - local-safe-write
  - external-read
  - radar-experiment-write
  - radar-promote-main
approval_required:
  - repo-write
  - external-write
  - self-modify
local_safe_roots:
  - .local/work
  - .local/logs
  - .local/state
destructive_keywords:
  - delete
  - reset
""".strip(),
    )
    _write(
        repo / "configs" / "radar" / "sources.yaml",
        """
default_window: weekly
topics:
  - agent
  - memory
  - evals
  - github
deep_analysis_limit: 12
experiment_limit: 3
promotion_limit: 1
weekly:
  candidate_limit: 50
  created_days: 30
  active_days: 14
manual:
  candidate_limit: 20
  created_days: 180
  active_days: 45
""".strip(),
    )
    _write(
        repo / "configs" / "radar" / "providers.yaml",
        """
default_provider: github
providers:
  github:
    kind: github
    enabled: true
    live: true
    description: GitHub repository search, repository metadata, and latest release metadata.
  future-second-provider:
    kind: reserved
    enabled: false
    live: false
    description: Reserved slot for the next radar provider contract without enabling a second live source yet.
""".strip(),
    )
    _write(
        repo / "configs" / "radar" / "scoring.yaml",
        """
weights:
  stars: 0.35
  activity: 0.20
  novelty: 0.15
  topicality: 0.15
  release: 0.05
  gap: 0.10
normalization:
  star_reference: 5000
  release_days: 45
thresholds:
  shortlist: 0.45
  experiment: 0.60
  promote: 0.72
capability_gaps:
  - agent
  - memory
  - evals
  - github
""".strip(),
    )
    _write(
        repo / "configs" / "radar" / "promotion.yaml",
        """
base_branch: main
allowed_paths:
  - docs/radar/experiments
  - docs/radar/promotions
  - configs/radar
weekly_promotion_cap: 1
freeze_after_failures: 2
validation_commands:
  - python -m pytest -q
experiment_dir: docs/radar/experiments
promotion_log_dir: docs/radar/promotions
adoption_registry: configs/radar/adoptions.yaml
""".strip(),
    )
    _write(repo / "configs" / "radar" / "adoptions.yaml", "adopted_patterns: []\n")
    _write(
        repo / "configs" / "radar" / "schedule.yaml",
        """
default_schedule: weekly-github
schedules:
  weekly-github:
    enabled: true
    window: weekly
    limit: 20
    target_command: python -m skylattice.cli radar schedule run --schedule weekly-github
    windows_task:
      folder: \\Skylattice
      description: Run Skylattice weekly GitHub radar scan
      schedule_expression: WEEKLY
      trigger_command: New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 9am
""".strip(),
    )
    _write(repo / "tests" / "test_placeholder.py", "def test_placeholder():\n    assert True\n")
    _run(["git", "init", "-b", "main"], repo)
    _run(["git", "config", "user.email", "tests@example.com"], repo)
    _run(["git", "config", "user.name", "Skylattice Tests"], repo)
    _run(["git", "add", "--all"], repo)
    _run(["git", "commit", "-m", "initial"], repo)
    return repo


class FakeRadarSource:
    @property
    def provider(self) -> str:
        return "github"

    def discover(self, *, run_id: str, topics, created_days: int, active_days: int, limit: int):
        from skylattice.radar import RadarCandidate, RadarDecision, RadarEvidence

        candidate = RadarCandidate(
            candidate_id="cand-seed",
            run_id=run_id,
            repo_slug="example/radar-kit",
            repo_name="radar-kit",
            html_url="https://github.com/example/radar-kit",
            description="A repo that demonstrates radar-worthy agent patterns.",
            source_provider=self.provider,
            source_kind="repository",
            source_handle="example/radar-kit",
            source_url="https://github.com/example/radar-kit",
            display_name="radar-kit",
            topics=("agent", "memory", "evals", "github"),
            stars=9000,
            forks=300,
            watchers=120,
            created_at_remote="2026-04-01T00:00:00Z",
            pushed_at_remote="2026-04-07T00:00:00Z",
            latest_release_at="2026-04-06T00:00:00Z",
            score=0.0,
            score_breakdown={},
            decision=RadarDecision.OBSERVE,
            reason="seed candidate",
            metadata={"source_provider": self.provider},
        )
        evidence = [
            RadarEvidence(
                evidence_id="evidence-seed",
                run_id=run_id,
                candidate_id=candidate.candidate_id,
                provider=self.provider,
                provider_object_type="repository",
                provider_object_id="example/radar-kit",
                provider_url="https://github.com/example/radar-kit",
                evidence_kind="search-result",
                source="fake-radar-source",
                summary="Seeded candidate for radar testing.",
                payload={"topics": list(topics), "limit": limit, "created_days": created_days, "active_days": active_days},
            )
        ]
        return [candidate], evidence

    def enrich_candidate(self, candidate):
        from skylattice.radar import RadarEvidence

        enriched = replace(
            candidate,
            description="A reusable open-source pattern library for memory, evals, and GitHub-aware agents.",
            topics=("agent", "memory", "evals", "developer-tools", "github"),
            latest_release_at="2026-04-07T00:00:00Z",
        )
        evidence = [
            RadarEvidence(
                evidence_id="evidence-enriched",
                run_id=candidate.run_id,
                candidate_id=candidate.candidate_id,
                provider=self.provider,
                provider_object_type="repository",
                provider_object_id="example/radar-kit",
                provider_url="https://github.com/example/radar-kit",
                evidence_kind="repository",
                source="fake-radar-source/enrich",
                summary="Enriched repository metadata for radar testing.",
                payload={"topics": list(enriched.topics)},
            )
        ]
        return enriched, evidence


def test_radar_scan_promotes_candidate_and_updates_registry(tmp_path: Path) -> None:
    repo = create_radar_repo(tmp_path)
    service = TaskAgentService.from_repo(repo_root=repo, radar_source=FakeRadarSource())
    fake_git = LocalPushGitAdapter(repo)
    service.git = fake_git
    service.radar.git = fake_git

    run = service.scan_radar(window="weekly", limit=5)
    details = service.inspect_radar_run(run.run_id)
    adoptions = (repo / "configs" / "radar" / "adoptions.yaml").read_text(encoding="utf-8")

    assert run.status.value == "completed"
    assert details["run"]["status"] == "completed"
    assert details["candidates"][0]["decision"] == "promote"
    assert details["candidates"][0]["metadata"]["source_provider"] == "github"
    assert details["candidates"][0]["source_provider"] == "github"
    assert details["candidates"][0]["source_kind"] == "repository"
    assert details["candidates"][0]["source_handle"] == "example/radar-kit"
    assert details["candidates"][0]["source_url"] == "https://github.com/example/radar-kit"
    assert details["candidates"][0]["display_name"] == "radar-kit"
    assert details["candidates"][0]["identity"]["provider"] == "github"
    assert details["candidates"][0]["identity"]["handle"] == "example/radar-kit"
    assert details["candidates"][0]["identity"]["url"] == "https://github.com/example/radar-kit"
    assert any(record["layer"] == "semantic" for record in details["memory"])
    assert any(record["layer"] == "procedural" for record in details["memory"])
    assert all(item["provider"] == "github" for item in details["evidence"])
    assert details["evidence"][0]["provider_object_type"] == "repository"
    assert details["evidence"][0]["provider_object_id"] == "example/radar-kit"
    assert details["evidence"][0]["provider_url"] == "https://github.com/example/radar-kit"
    assert details["evidence"][0]["evidence_kind"] == "discovery-hit"
    assert any(promotion["status"] == "promoted" for promotion in details["promotions"])
    assert "example/radar-kit" in adoptions
    assert "source_provider: github" in adoptions
    assert "source_handle: example/radar-kit" in adoptions
    assert "source_url: https://github.com/example/radar-kit" in adoptions
    assert fake_git.push_calls[-1]["branch_name"] == "main"
    assert _run(["git", "branch", "--show-current"], repo).strip() == "main"


def test_radar_rollback_reverts_promotion(tmp_path: Path) -> None:
    repo = create_radar_repo(tmp_path)
    service = TaskAgentService.from_repo(repo_root=repo, radar_source=FakeRadarSource())
    fake_git = LocalPushGitAdapter(repo)
    service.git = fake_git
    service.radar.git = fake_git

    run = service.scan_radar(window="manual", limit=3)
    promotion_id = service.inspect_radar_run(run.run_id)["promotions"][0]["promotion_id"]
    rolled_back = service.rollback_radar_promotion(promotion_id)

    adoptions = (repo / "configs" / "radar" / "adoptions.yaml").read_text(encoding="utf-8")
    assert rolled_back.status.value == "rolled-back"
    assert adoptions.strip() == "adopted_patterns: []"
    assert fake_git.push_calls[-1]["branch_name"] == "main"


def test_radar_api_endpoints(tmp_path: Path) -> None:
    repo = create_radar_repo(tmp_path)
    service = TaskAgentService.from_repo(repo_root=repo, radar_source=FakeRadarSource())
    fake_git = LocalPushGitAdapter(repo)
    service.git = fake_git
    service.radar.git = fake_git
    radar_run = service.scan_radar(window="manual", limit=2)
    radar_candidate = service.inspect_radar_run(radar_run.run_id)["candidates"][0]["candidate_id"]
    radar_promotion = service.inspect_radar_run(radar_run.run_id)["promotions"][0]["promotion_id"]

    app.dependency_overrides[get_task_agent_service] = lambda: service
    client = TestClient(app)
    try:
        radar_run_response = client.get(f"/radar/runs/{radar_run.run_id}")
        radar_candidate_response = client.get(f"/radar/candidates/{radar_candidate}")
        radar_promotion_response = client.get(f"/radar/promotions/{radar_promotion}")
        radar_digest_response = client.get("/radar/digest/latest")
    finally:
        app.dependency_overrides.clear()

    assert radar_run_response.status_code == 200
    assert radar_run_response.json()["run_id"] == radar_run.run_id
    assert radar_candidate_response.status_code == 200
    assert radar_candidate_response.json()["candidate_id"] == radar_candidate
    assert radar_promotion_response.status_code == 200
    assert radar_promotion_response.json()["promotion_id"] == radar_promotion
    assert radar_digest_response.status_code == 200
    assert radar_digest_response.json()["run_id"] == radar_run.run_id


def test_radar_schedule_show_render_and_run_use_tracked_schedule(tmp_path: Path) -> None:
    repo = create_radar_repo(tmp_path)
    service = TaskAgentService.from_repo(repo_root=repo, radar_source=FakeRadarSource())
    fake_git = LocalPushGitAdapter(repo)
    service.git = fake_git
    service.radar.git = fake_git

    schedule = service.radar.show_schedule()
    rendered = service.radar.render_schedule(target="windows-task")
    run = service.radar.run_schedule()
    inspected = service.inspect_radar_run(run.run_id)
    snapshot = service.radar.state_snapshot()

    assert schedule["default_schedule"] == "weekly-github"
    assert schedule["selected_schedule"] == "weekly-github"
    assert schedule["schedules"]["weekly-github"]["window"] == "weekly"
    assert rendered["target"] == "windows-task"
    assert rendered["schedule"]["schedule_id"] == "weekly-github"
    assert "radar schedule run --schedule weekly-github" in rendered["command"]
    assert rendered["working_directory"] == str(repo.resolve())
    assert rendered["windows_task"]["registration_mode"] == "scheduled"
    assert rendered["windows_task"]["trigger_command"] == "New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 9am"
    assert rendered["windows_task"]["action"]["execute"] == "powershell.exe"
    assert "EncodedCommand" in rendered["windows_task"]["action"]["arguments"]
    assert "Set-Location -LiteralPath" in rendered["windows_task"]["action"]["script"]
    assert str(repo.resolve()) in rendered["windows_task"]["action"]["script"]
    assert "Register-ScheduledTask" in rendered["windows_task"]["register_command"]
    assert "New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 9am" in rendered["windows_task"]["register_command"]
    assert "Get-ScheduledTask" in rendered["windows_task"]["inspect_command"]
    assert "Start-ScheduledTask" in rendered["windows_task"]["run_now_command"]
    assert "Unregister-ScheduledTask" in rendered["windows_task"]["unregister_command"]
    assert run.window.value == "weekly"
    assert run.limit == 20
    assert run.trigger_mode == "scheduled"
    assert run.schedule_id == "weekly-github"
    assert inspected["run"]["trigger_mode"] == "scheduled"
    assert inspected["run"]["schedule_id"] == "weekly-github"
    assert inspected["run"]["digest"]["trigger_mode"] == "scheduled"
    assert inspected["run"]["digest"]["schedule_id"] == "weekly-github"
    assert snapshot["latest_run_id"] == run.run_id
    assert snapshot["latest_trigger_mode"] == "scheduled"
    assert snapshot["latest_schedule_id"] == "weekly-github"


def test_direct_radar_scan_records_direct_trigger_mode(tmp_path: Path) -> None:
    repo = create_radar_repo(tmp_path)
    service = TaskAgentService.from_repo(repo_root=repo, radar_source=FakeRadarSource())
    fake_git = LocalPushGitAdapter(repo)
    service.git = fake_git
    service.radar.git = fake_git

    run = service.scan_radar(window="manual", limit=2)
    inspected = service.inspect_radar_run(run.run_id)
    snapshot = service.radar.state_snapshot()

    assert run.trigger_mode == "direct"
    assert run.schedule_id is None
    assert inspected["run"]["trigger_mode"] == "direct"
    assert inspected["run"]["schedule_id"] is None
    assert inspected["run"]["digest"]["trigger_mode"] == "direct"
    assert inspected["run"]["digest"]["schedule_id"] is None
    assert snapshot["latest_run_id"] == run.run_id
    assert snapshot["latest_trigger_mode"] == "direct"
    assert snapshot["latest_schedule_id"] is None


def test_radar_schedule_validate_writes_local_report(tmp_path: Path) -> None:
    repo = create_radar_repo(tmp_path)
    service = TaskAgentService.from_repo(repo_root=repo, radar_source=FakeRadarSource())
    fake_git = LocalPushGitAdapter(repo)
    service.git = fake_git
    service.radar.git = fake_git

    run = service.radar.run_schedule()
    report = service.radar.validate_schedule_run(schedule_id="weekly-github", run_id=run.run_id)
    report_path = repo / report["output_path"]

    assert report["valid"] is True
    assert report["run"]["run_id"] == run.run_id
    assert report["run"]["trigger_mode"] == "scheduled"
    assert report["run"]["schedule_id"] == "weekly-github"
    assert report["checks"]["status_completed"] is True
    assert report["checks"]["trigger_mode_matches"] is True
    assert report["checks"]["schedule_id_matches"] is True
    assert report["checks"]["window_matches"] is True
    assert report["checks"]["limit_matches"] is True
    assert report_path.exists()
    assert ".local/radar/validations/" in report["output_path"].replace("\\", "/")
    assert report["tracked_record_template"] == "docs/ops/radar-weekly-validation-template.md"
    assert report["suggested_record_path"].startswith("docs/ops/radar-validations/")
    assert report["suggested_record_path"].endswith("-weekly-github.md")


def test_radar_state_snapshot_reports_tracked_provider_contract(tmp_path: Path) -> None:
    repo = create_radar_repo(tmp_path)
    service = TaskAgentService.from_repo(repo_root=repo, radar_source=FakeRadarSource())

    snapshot = service.radar.state_snapshot()

    assert snapshot["default_provider"] == "github"
    assert snapshot["enabled_providers"] == ["github"]
    assert snapshot["source_provider"] == "github"
    assert snapshot["source_available"] is True


def test_radar_service_respects_disabled_default_provider(tmp_path: Path) -> None:
    repo = create_radar_repo(tmp_path)
    _write(
        repo / "configs" / "radar" / "providers.yaml",
        """
default_provider: future-second-provider
providers:
  github:
    kind: github
    enabled: true
    live: true
    description: GitHub repository search, repository metadata, and latest release metadata.
  future-second-provider:
    kind: reserved
    enabled: false
    live: false
    description: Reserved slot for the next radar provider contract without enabling a second live source yet.
""".strip(),
    )

    service = TaskAgentService.from_repo(repo_root=repo)
    snapshot = service.radar.state_snapshot()

    assert snapshot["default_provider"] == "future-second-provider"
    assert snapshot["enabled_providers"] == ["github"]
    assert snapshot["source_provider"] is None
    assert snapshot["source_available"] is False


def test_radar_scoring_prefers_provider_neutral_adoption_identity(tmp_path: Path) -> None:
    repo = create_radar_repo(tmp_path)
    _write(
        repo / "configs" / "radar" / "adoptions.yaml",
        """
adopted_patterns:
  - repo_slug: legacy/placeholder
    source_provider: github
    source_kind: repository
    source_handle: example/radar-kit
    source_url: https://github.com/example/radar-kit
    tags:
      - agent
      - memory
    preference_boost: 0.12
    rationale: direct identity match should win even when repo_slug differs
""".strip(),
    )
    from skylattice.radar import RadarScorer, load_adoption_records, load_radar_config

    candidate = FakeRadarSource().discover(
        run_id="radar-test",
        topics=("agent", "memory"),
        created_days=30,
        active_days=14,
        limit=1,
    )[0][0]
    scorer = RadarScorer(
        load_radar_config(repo).scoring,
        adoption_records=load_adoption_records(repo),
    )

    score = scorer.score(candidate, active_days=14, created_days=30)

    assert score.breakdown["adoption_boost"] == 0.12


def test_legacy_evidence_kinds_are_normalized_on_read(tmp_path: Path) -> None:
    repo = create_radar_repo(tmp_path)
    service = TaskAgentService.from_repo(repo_root=repo, radar_source=FakeRadarSource())
    fake_git = LocalPushGitAdapter(repo)
    service.git = fake_git
    service.radar.git = fake_git

    run = service.scan_radar(window="manual", limit=2)
    details = service.inspect_radar_run(run.run_id)
    kinds = {item["evidence_kind"] for item in details["evidence"]}

    assert "discovery-hit" in kinds
    assert "object-metadata" in kinds
    assert all(normalize_evidence_kind(kind) == kind for kind in kinds)


