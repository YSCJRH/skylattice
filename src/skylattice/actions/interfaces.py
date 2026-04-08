"""Core action layer interfaces."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Mapping, Protocol


class ApprovalRequirement(StrEnum):
    AUTO = "auto"
    OPERATOR = "operator"
    FORBIDDEN = "forbidden"


class ActionScope(StrEnum):
    LOCAL_SHELL = "local-shell"
    CODING = "coding"
    GIT = "git"
    GITHUB = "github"
    BROWSER = "browser"
    FUTURE = "future-adapter"


@dataclass(frozen=True)
class ActionRequest:
    action_id: str
    scope: ActionScope
    intent: str
    arguments: Mapping[str, object] = field(default_factory=dict)
    approval_requirement: ApprovalRequirement = ApprovalRequirement.OPERATOR
    reversible: bool = True


@dataclass(frozen=True)
class ActionResult:
    action_id: str
    success: bool
    summary: str
    artifact_refs: tuple[str, ...] = ()
    needs_follow_up: bool = False


class ActionAdapter(Protocol):
    scope: ActionScope

    def execute(self, request: ActionRequest) -> ActionResult:
        ...
