"""Core interfaces for the layered memory system."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol


class MemoryLayer(StrEnum):
    PROFILE = "profile"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    WORKING = "working"


class RecordStatus(StrEnum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    CONSTRAINED = "constrained"
    TOMBSTONED = "tombstoned"


class ConflictStrategy(StrEnum):
    SUPERSEDE = "supersede"
    TOMBSTONE = "tombstone"
    APPEND_ONLY = "append-only"


class RetrievalSort(StrEnum):
    RELEVANCE = "relevance"
    RECENT = "recent"


@dataclass(frozen=True)
class MemoryRecord:
    record_id: str
    layer: MemoryLayer
    summary: str
    source_refs: tuple[str, ...] = ()
    confidence: float = 1.0
    status: RecordStatus = RecordStatus.ACTIVE
    metadata: dict[str, Any] = field(default_factory=dict)
    run_id: str | None = None
    supersedes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(frozen=True)
class RetrievalRequest:
    layers: tuple[MemoryLayer, ...]
    query: str
    limit: int = 5
    include_stale: bool = False
    metadata_filters: tuple[tuple[str, str], ...] = ()
    statuses: tuple[RecordStatus, ...] = ()
    sort_by: RetrievalSort = RetrievalSort.RELEVANCE


@dataclass(frozen=True)
class CompactionPolicy:
    decay_window: str
    compaction_trigger: str
    conflict_strategy: ConflictStrategy
    rollback_mechanism: str


class MemoryStore(Protocol):
    def write(self, record: MemoryRecord) -> None:
        ...

    def rollback(self, record_id: str) -> None:
        ...


class MemoryIndex(Protocol):
    def retrieve(self, request: RetrievalRequest) -> list[MemoryRecord]:
        ...
