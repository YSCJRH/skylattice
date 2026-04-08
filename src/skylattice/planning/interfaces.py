"""Planner and executor boundary models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class PlanOrigin(StrEnum):
    USER_REQUESTED = "user-requested"
    AGENT_PROPOSED = "agent-proposed"
    BACKGROUND_MAINTENANCE = "background-maintenance"


class StepStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    VERIFIED = "verified"
    BLOCKED = "blocked"
    FAILED = "failed"
    STOPPED = "stopped"


@dataclass(frozen=True)
class GoalSpec:
    goal_id: str
    origin: PlanOrigin
    summary: str
    success_criteria: tuple[str, ...]


@dataclass(frozen=True)
class VerificationSpec:
    checks: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    fallback: str


@dataclass(frozen=True)
class PlanStep:
    step_id: str
    summary: str
    required_tier: str
    verification: VerificationSpec | None = None
    status: StepStatus = StepStatus.PENDING


@dataclass(frozen=True)
class PlanSpec:
    goal: GoalSpec
    steps: tuple[PlanStep, ...]
    retry_budget: int = 2
    fallback_policy: str = "escalate to operator"
