"""Interfaces for bounded self-improvement."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CandidateKind(StrEnum):
    MEMORY = "memory"
    STRATEGY = "strategy"
    SKILL = "skill"
    ROUTING = "routing"
    PLAYBOOK = "playbook"
    PROMPT_POLICY = "prompt-policy"


class PromotionDecision(StrEnum):
    PROMOTE = "promote"
    HOLD = "hold"
    ROLLBACK = "rollback"


@dataclass(frozen=True)
class EvolutionCandidate:
    candidate_id: str
    kind: CandidateKind
    summary: str
    artifact_refs: tuple[str, ...]
    rollback_ref: str
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class SandboxRun:
    run_id: str
    candidate_id: str
    scenario: str
    passed: bool
    notes: str


@dataclass(frozen=True)
class EvaluationReport:
    candidate_id: str
    decision: PromotionDecision
    rationale: str
    evidence_refs: tuple[str, ...]
    follow_ups: tuple[str, ...] = ()
