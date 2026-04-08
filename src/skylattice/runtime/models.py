"""Runtime models for executable task runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from skylattice.governance import PermissionTier


class RunStatus(StrEnum):
    CREATED = "created"
    PLANNED = "planned"
    WAITING_APPROVAL = "waiting_approval"
    RUNNING = "running"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    HALTED = "halted"


class RunStepStatus(StrEnum):
    PLANNED = "planned"
    RUNNING = "running"
    VERIFIED = "verified"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class ApprovalGrant:
    tier: PermissionTier
    granted: bool
    actor: str = "operator"
    created_at: str | None = None


@dataclass(frozen=True)
class RunStep:
    run_id: str
    step_index: int
    step_id: str
    summary: str
    required_tier: PermissionTier
    action_name: str
    action_args: dict[str, Any]
    verification: dict[str, Any]
    status: RunStepStatus = RunStepStatus.PLANNED
    result: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TaskRun:
    run_id: str
    goal: str
    goal_source: str
    status: RunStatus
    runtime_snapshot: dict[str, Any]
    plan_summary: str = ""
    plan: dict[str, Any] = field(default_factory=dict)
    branch_name: str | None = None
    current_step: int = 0
    approvals: tuple[ApprovalGrant, ...] = ()
    error: str | None = None
    result: dict[str, Any] = field(default_factory=dict)
    created_at: str | None = None
    updated_at: str | None = None

    def approval_map(self) -> dict[PermissionTier, ApprovalGrant]:
        return {grant.tier: grant for grant in self.approvals if grant.granted}
