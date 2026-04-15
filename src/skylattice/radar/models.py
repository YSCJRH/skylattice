"""Technology radar models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class RadarWindow(StrEnum):
    WEEKLY = "weekly"
    MANUAL = "manual"


class RadarRunStatus(StrEnum):
    CREATED = "created"
    SCANNING = "scanning"
    ANALYZING = "analyzing"
    EXPERIMENTING = "experimenting"
    PROMOTING = "promoting"
    COMPLETED = "completed"
    FAILED = "failed"
    FROZEN = "frozen"


class RadarCandidateStatus(StrEnum):
    DISCOVERED = "discovered"
    SHORTLISTED = "shortlisted"
    EXPERIMENTED = "experimented"
    PROMOTED = "promoted"
    REJECTED = "rejected"
    REPLAYED = "replayed"


class RadarExperimentStatus(StrEnum):
    PLANNED = "planned"
    RUNNING = "running"
    VERIFIED = "verified"
    SKIPPED = "skipped"
    PROMOTED = "promoted"
    FAILED = "failed"


class RadarPromotionStatus(StrEnum):
    PENDING = "pending"
    PROMOTED = "promoted"
    ROLLED_BACK = "rolled-back"
    SKIPPED = "skipped"
    FROZEN = "frozen"
    FAILED = "failed"


class RadarDecision(StrEnum):
    OBSERVE = "observe"
    EXPERIMENT = "experiment"
    PROMOTE = "promote"
    REJECT = "reject"
    FREEZE = "freeze"


class RadarEvidenceKind(StrEnum):
    DISCOVERY_HIT = "discovery-hit"
    OBJECT_METADATA = "object-metadata"
    RELEASE_METADATA = "release-metadata"


LEGACY_EVIDENCE_KIND_MAP = {
    "search-result": RadarEvidenceKind.DISCOVERY_HIT.value,
    "repository": RadarEvidenceKind.OBJECT_METADATA.value,
    "release": RadarEvidenceKind.RELEASE_METADATA.value,
}


def normalize_evidence_kind(value: str) -> str:
    key = value.strip().lower()
    return LEGACY_EVIDENCE_KIND_MAP.get(key, key)


@dataclass(frozen=True)
class RadarRun:
    run_id: str
    window: RadarWindow
    status: RadarRunStatus
    limit: int
    trigger_mode: str = "direct"
    schedule_id: str | None = None
    summary: str = ""
    digest: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(frozen=True)
class RadarCandidate:
    candidate_id: str
    run_id: str
    repo_slug: str
    repo_name: str
    html_url: str
    description: str
    source_provider: str = "github"
    source_kind: str = "repository"
    source_handle: str = ""
    source_url: str = ""
    display_name: str = ""
    topics: tuple[str, ...] = ()
    stars: int = 0
    forks: int = 0
    watchers: int = 0
    created_at_remote: str | None = None
    pushed_at_remote: str | None = None
    latest_release_at: str | None = None
    score: float = 0.0
    score_breakdown: dict[str, float] = field(default_factory=dict)
    decision: RadarDecision = RadarDecision.OBSERVE
    status: RadarCandidateStatus = RadarCandidateStatus.DISCOVERED
    reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str | None = None
    updated_at: str | None = None

    @property
    def identity_handle(self) -> str:
        return self.source_handle or self.repo_slug

    @property
    def identity_url(self) -> str:
        return self.source_url or self.html_url

    @property
    def identity_name(self) -> str:
        return self.display_name or self.repo_name or self.identity_handle


@dataclass(frozen=True)
class RadarEvidence:
    evidence_id: str
    run_id: str
    candidate_id: str
    provider: str
    evidence_kind: str
    source: str
    summary: str
    provider_object_type: str = ""
    provider_object_id: str = ""
    provider_url: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: str | None = None


@dataclass(frozen=True)
class RadarExperiment:
    experiment_id: str
    run_id: str
    candidate_id: str
    branch_name: str
    hypothesis: str
    artifact_path: str
    validation_command: str
    status: RadarExperimentStatus = RadarExperimentStatus.PLANNED
    recommended: bool = False
    source_commit: str | None = None
    experiment_commit: str | None = None
    notes: dict[str, Any] = field(default_factory=dict)
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(frozen=True)
class RadarPromotion:
    promotion_id: str
    run_id: str
    candidate_id: str
    experiment_id: str
    status: RadarPromotionStatus
    source_branch: str
    base_commit: str
    experiment_commit: str
    main_commit: str | None = None
    rollback_target: str | None = None
    pushed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(frozen=True)
class RadarState:
    freeze_mode: bool = False
    consecutive_failures: int = 0
    last_failure_at: str | None = None
