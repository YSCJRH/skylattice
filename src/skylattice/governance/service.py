"""Governance policy loading and approval decisions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from skylattice.storage import LocalPaths, load_yaml, resolve_repo_root


class PermissionTier(StrEnum):
    OBSERVE = "observe"
    LOCAL_SAFE_WRITE = "local-safe-write"
    REPO_WRITE = "repo-write"
    EXTERNAL_READ = "external-read"
    EXTERNAL_WRITE = "external-write"
    RADAR_EXPERIMENT_WRITE = "radar-experiment-write"
    RADAR_PROMOTE_MAIN = "radar-promote-main"
    SELF_MODIFY = "self-modify"


class GovernanceDecision(StrEnum):
    APPROVED = "approved"
    DENIED = "denied"


@dataclass(frozen=True)
class GovernanceRequest:
    tier: PermissionTier
    summary: str
    target_path: str | None = None
    destructive: bool = False
    user_approved: bool = False


@dataclass(frozen=True)
class GovernanceOutcome:
    decision: GovernanceDecision
    reason: str


@dataclass(frozen=True)
class GovernancePolicy:
    freeze_mode: bool
    auto_approve: tuple[PermissionTier, ...]
    approval_required: tuple[PermissionTier, ...]
    local_safe_roots: tuple[str, ...]
    destructive_keywords: tuple[str, ...]


class GovernanceGate:
    def __init__(self, policy: GovernancePolicy, repo_root: Path | None = None) -> None:
        self.policy = policy
        self.repo_root = resolve_repo_root(repo_root)
        self.paths = LocalPaths.from_repo_root(self.repo_root)

    @classmethod
    def from_repo(cls, repo_root: Path | None = None) -> "GovernanceGate":
        raw = load_yaml("configs/policies/governance.yaml", repo_root)
        policy = GovernancePolicy(
            freeze_mode=bool(raw.get("freeze_mode", False)),
            auto_approve=tuple(PermissionTier(item) for item in raw.get("auto_approve", [])),
            approval_required=tuple(PermissionTier(item) for item in raw.get("approval_required", [])),
            local_safe_roots=tuple(str(item) for item in raw.get("local_safe_roots", [])),
            destructive_keywords=tuple(str(item).lower() for item in raw.get("destructive_keywords", [])),
        )
        return cls(policy=policy, repo_root=repo_root)

    def evaluate(self, request: GovernanceRequest) -> GovernanceOutcome:
        lowered = request.summary.lower()
        destructive = request.destructive or any(
            keyword in lowered for keyword in self.policy.destructive_keywords
        )

        if self.policy.freeze_mode and request.tier is not PermissionTier.OBSERVE:
            return GovernanceOutcome(GovernanceDecision.DENIED, "freeze mode is enabled")

        if destructive:
            return GovernanceOutcome(
                GovernanceDecision.DENIED,
                "destructive action requires explicit operator intervention",
            )

        if request.user_approved:
            return GovernanceOutcome(GovernanceDecision.APPROVED, "operator approval present")

        if request.tier in self.policy.auto_approve:
            if request.tier is PermissionTier.LOCAL_SAFE_WRITE and not self._is_allowed_local_target(
                request.target_path
            ):
                return GovernanceOutcome(
                    GovernanceDecision.DENIED,
                    "local-safe-write is limited to approved .local roots",
                )
            return GovernanceOutcome(GovernanceDecision.APPROVED, "tier is auto-approved")

        if request.tier in self.policy.approval_required:
            return GovernanceOutcome(
                GovernanceDecision.DENIED,
                "explicit approval required for this permission tier",
            )

        return GovernanceOutcome(GovernanceDecision.DENIED, "request does not match an allowed policy path")

    def policy_snapshot(self) -> dict[str, object]:
        return {
            "freeze_mode": self.policy.freeze_mode,
            "auto_approve": [tier.value for tier in self.policy.auto_approve],
            "approval_required": [tier.value for tier in self.policy.approval_required],
            "local_safe_roots": list(self.policy.local_safe_roots),
        }

    @property
    def freeze_mode_enabled(self) -> bool:
        return self.policy.freeze_mode

    def paths_within_roots(
        self,
        target_paths: tuple[str, ...] | list[str],
        allowed_roots: tuple[str, ...] | list[str],
    ) -> bool:
        return all(self._is_within_roots(path, allowed_roots) for path in target_paths)

    def _is_allowed_local_target(self, target_path: str | None) -> bool:
        if not target_path:
            return False

        return self._is_within_roots(target_path, self.policy.local_safe_roots)

    def _is_within_roots(self, target_path: str | None, allowed_roots: tuple[str, ...] | list[str]) -> bool:
        if not target_path:
            return False

        target = Path(target_path)
        if not target.is_absolute():
            target = (self.repo_root / target).resolve()
        else:
            target = target.resolve()

        for root in allowed_roots:
            allowed_root = (self.repo_root / root).resolve()
            try:
                target.relative_to(allowed_root)
                return True
            except ValueError:
                continue
        return False
