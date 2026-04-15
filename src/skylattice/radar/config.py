"""Tracked configuration loading for the technology radar."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from skylattice.storage import load_yaml, resolve_repo_root


@dataclass(frozen=True)
class RadarWindowConfig:
    candidate_limit: int
    created_days: int
    active_days: int


@dataclass(frozen=True)
class RadarSourceConfig:
    default_window: str
    topics: tuple[str, ...]
    deep_analysis_limit: int
    experiment_limit: int
    promotion_limit: int
    weekly: RadarWindowConfig
    manual: RadarWindowConfig


@dataclass(frozen=True)
class RadarScoringConfig:
    weights: dict[str, float]
    star_reference: int
    release_days: int
    thresholds: dict[str, float]
    capability_gaps: tuple[str, ...]


@dataclass(frozen=True)
class RadarPromotionConfig:
    base_branch: str
    allowed_paths: tuple[str, ...]
    weekly_promotion_cap: int
    freeze_after_failures: int
    validation_commands: tuple[str, ...]
    experiment_dir: str
    promotion_log_dir: str
    adoption_registry: str


@dataclass(frozen=True)
class RadarWindowsTaskConfig:
    folder: str
    description: str
    schedule_expression: str
    trigger_command: str | None = None


@dataclass(frozen=True)
class RadarScheduleEntry:
    schedule_id: str
    enabled: bool
    window: str
    limit: int | None
    target_command: str
    windows_task: RadarWindowsTaskConfig


@dataclass(frozen=True)
class RadarScheduleConfig:
    default_schedule: str
    schedules: dict[str, RadarScheduleEntry]

    def get(self, schedule_id: str | None = None) -> RadarScheduleEntry:
        effective = schedule_id or self.default_schedule
        try:
            return self.schedules[effective]
        except KeyError as exc:
            raise KeyError(f"Unknown radar schedule: {effective}") from exc


@dataclass(frozen=True)
class RadarProviderEntry:
    provider_id: str
    kind: str
    enabled: bool
    live: bool
    description: str


@dataclass(frozen=True)
class RadarProviderConfig:
    default_provider: str
    providers: dict[str, RadarProviderEntry]

    def get(self, provider_id: str | None = None) -> RadarProviderEntry:
        effective = provider_id or self.default_provider
        try:
            return self.providers[effective]
        except KeyError as exc:
            raise KeyError(f"Unknown radar provider: {effective}") from exc

    def enabled_provider_ids(self) -> tuple[str, ...]:
        return tuple(key for key, item in self.providers.items() if item.enabled)


@dataclass(frozen=True)
class RadarConfig:
    sources: RadarSourceConfig
    scoring: RadarScoringConfig
    promotion: RadarPromotionConfig
    schedule: RadarScheduleConfig
    providers: RadarProviderConfig


@dataclass(frozen=True)
class AdoptionRecord:
    repo_slug: str
    tags: tuple[str, ...]
    preference_boost: float
    rationale: str
    source_provider: str = ""
    source_kind: str = ""
    source_handle: str = ""
    source_url: str = ""
    promoted_at: str | None = None


def load_radar_config(repo_root: Path | None = None) -> RadarConfig:
    root = resolve_repo_root(repo_root)
    raw_sources = load_yaml("configs/radar/sources.yaml", root)
    raw_scoring = load_yaml("configs/radar/scoring.yaml", root)
    raw_promotion = load_yaml("configs/radar/promotion.yaml", root)
    raw_schedule = load_yaml("configs/radar/schedule.yaml", root)
    raw_providers = load_yaml("configs/radar/providers.yaml", root)

    return RadarConfig(
        sources=RadarSourceConfig(
            default_window=str(raw_sources.get("default_window", "weekly")),
            topics=tuple(str(item) for item in raw_sources.get("topics", [])),
            deep_analysis_limit=int(raw_sources.get("deep_analysis_limit", 12)),
            experiment_limit=int(raw_sources.get("experiment_limit", 3)),
            promotion_limit=int(raw_sources.get("promotion_limit", 1)),
            weekly=_window_config(raw_sources.get("weekly", {}), candidate_limit=50, created_days=30, active_days=14),
            manual=_window_config(raw_sources.get("manual", {}), candidate_limit=20, created_days=180, active_days=45),
        ),
        scoring=RadarScoringConfig(
            weights={str(key): float(value) for key, value in dict(raw_scoring.get("weights", {})).items()},
            star_reference=int(raw_scoring.get("normalization", {}).get("star_reference", 5000)),
            release_days=int(raw_scoring.get("normalization", {}).get("release_days", 45)),
            thresholds={str(key): float(value) for key, value in dict(raw_scoring.get("thresholds", {})).items()},
            capability_gaps=tuple(str(item) for item in raw_scoring.get("capability_gaps", [])),
        ),
        promotion=RadarPromotionConfig(
            base_branch=str(raw_promotion.get("base_branch", "main")),
            allowed_paths=tuple(str(item) for item in raw_promotion.get("allowed_paths", [])),
            weekly_promotion_cap=int(raw_promotion.get("weekly_promotion_cap", 1)),
            freeze_after_failures=int(raw_promotion.get("freeze_after_failures", 2)),
            validation_commands=tuple(str(item) for item in raw_promotion.get("validation_commands", ["python -m pytest -q"])),
            experiment_dir=str(raw_promotion.get("experiment_dir", "docs/radar/experiments")),
            promotion_log_dir=str(raw_promotion.get("promotion_log_dir", "docs/radar/promotions")),
            adoption_registry=str(raw_promotion.get("adoption_registry", "configs/radar/adoptions.yaml")),
        ),
        schedule=_load_schedule_config(raw_schedule),
        providers=_load_provider_config(raw_providers),
    )


def load_adoption_records(repo_root: Path | None = None) -> tuple[AdoptionRecord, ...]:
    root = resolve_repo_root(repo_root)
    raw = load_yaml("configs/radar/adoptions.yaml", root)
    records: list[AdoptionRecord] = []
    for item in raw.get("adopted_patterns", []):
        if not isinstance(item, dict):
            continue
        records.append(
            AdoptionRecord(
                repo_slug=str(item.get("repo_slug", "")),
                source_provider=str(item.get("source_provider", "")),
                source_kind=str(item.get("source_kind", "")),
                source_handle=str(item.get("source_handle", "")),
                source_url=str(item.get("source_url", "")),
                tags=tuple(str(tag) for tag in item.get("tags", [])),
                preference_boost=float(item.get("preference_boost", 0.0)),
                rationale=str(item.get("rationale", "")),
                promoted_at=str(item.get("promoted_at")) if item.get("promoted_at") else None,
            )
        )
    return tuple(records)


def _window_config(raw: object, *, candidate_limit: int, created_days: int, active_days: int) -> RadarWindowConfig:
    mapping = raw if isinstance(raw, dict) else {}
    return RadarWindowConfig(
        candidate_limit=int(mapping.get("candidate_limit", candidate_limit)),
        created_days=int(mapping.get("created_days", created_days)),
        active_days=int(mapping.get("active_days", active_days)),
    )


def _load_schedule_config(raw: dict[str, object]) -> RadarScheduleConfig:
    schedules_raw = raw.get("schedules", {})
    schedules_map = schedules_raw if isinstance(schedules_raw, dict) else {}
    schedules: dict[str, RadarScheduleEntry] = {}
    for schedule_id, item in schedules_map.items():
        if not isinstance(item, dict):
            continue
        windows_task_raw = item.get("windows_task", {})
        windows_task = windows_task_raw if isinstance(windows_task_raw, dict) else {}
        limit_value = item.get("limit")
        schedules[str(schedule_id)] = RadarScheduleEntry(
            schedule_id=str(schedule_id),
            enabled=bool(item.get("enabled", True)),
            window=str(item.get("window", "weekly")),
            limit=int(limit_value) if limit_value is not None else None,
            target_command=str(
                item.get(
                    "target_command",
                    f"python -m skylattice.cli radar schedule run --schedule {schedule_id}",
                )
            ),
            windows_task=RadarWindowsTaskConfig(
                folder=str(windows_task.get("folder", "\\Skylattice")),
                description=str(windows_task.get("description", "Run Skylattice radar scan")),
                schedule_expression=str(windows_task.get("schedule_expression", "WEEKLY")),
                trigger_command=str(windows_task.get("trigger_command")) if windows_task.get("trigger_command") else None,
            ),
        )
    if not schedules:
        schedules["weekly-github"] = RadarScheduleEntry(
            schedule_id="weekly-github",
            enabled=True,
            window="weekly",
            limit=20,
            target_command="python -m skylattice.cli radar schedule run --schedule weekly-github",
            windows_task=RadarWindowsTaskConfig(
                folder="\\Skylattice",
                description="Run Skylattice weekly GitHub radar scan",
                schedule_expression="WEEKLY",
                trigger_command="New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 9am",
            ),
        )
    default_schedule = str(raw.get("default_schedule", next(iter(schedules))))
    return RadarScheduleConfig(default_schedule=default_schedule, schedules=schedules)


def _load_provider_config(raw: dict[str, object]) -> RadarProviderConfig:
    providers_raw = raw.get("providers", {})
    providers_map = providers_raw if isinstance(providers_raw, dict) else {}
    providers: dict[str, RadarProviderEntry] = {}
    for provider_id, item in providers_map.items():
        if not isinstance(item, dict):
            continue
        providers[str(provider_id)] = RadarProviderEntry(
            provider_id=str(provider_id),
            kind=str(item.get("kind", provider_id)),
            enabled=bool(item.get("enabled", False)),
            live=bool(item.get("live", False)),
            description=str(item.get("description", "")),
        )
    if not providers:
        providers["github"] = RadarProviderEntry(
            provider_id="github",
            kind="github",
            enabled=True,
            live=True,
            description="GitHub repository search, repository metadata, and latest release metadata.",
        )
    default_provider = str(raw.get("default_provider", next(iter(providers))))
    return RadarProviderConfig(default_provider=default_provider, providers=providers)
