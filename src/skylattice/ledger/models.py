"""Audit event models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class EventKind(StrEnum):
    APPROVAL = "approval"
    ACTION = "action"
    MEMORY = "memory"
    EVALUATION = "evaluation"
    EVOLUTION = "evolution"
    RUN = "run"


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    kind: EventKind
    summary: str
    actor: str
    artifact_refs: tuple[str, ...] = ()
    reversible: bool = True
    run_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: str | None = None
