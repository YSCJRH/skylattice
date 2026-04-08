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
class RadarConfig:
    sources: RadarSourceConfig
    scoring: RadarScoringConfig
    promotion: RadarPromotionConfig


@dataclass(frozen=True)
class AdoptionRecord:
    repo_slug: str
    tags: tuple[str, ...]
    preference_boost: float
    rationale: str
    promoted_at: str | None = None


def load_radar_config(repo_root: Path | None = None) -> RadarConfig:
    root = resolve_repo_root(repo_root)
    raw_sources = load_yaml("configs/radar/sources.yaml", root)
    raw_scoring = load_yaml("configs/radar/scoring.yaml", root)
    raw_promotion = load_yaml("configs/radar/promotion.yaml", root)

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
