"""Kernel data models for agent identity and runtime state."""

from __future__ import annotations

from dataclasses import dataclass

from skylattice.storage import LocalPaths


@dataclass(frozen=True)
class AgentIdentity:
    agent_id: str
    codename: str
    version: str
    owner: str


@dataclass(frozen=True)
class UserIdentityModel:
    user_id: str
    display_name: str
    timezone: str
    interaction_style: str


@dataclass(frozen=True)
class RelationshipModel:
    role: str
    promises: tuple[str, ...]
    escalation_default: str


@dataclass(frozen=True)
class BoundaryRule:
    name: str
    intent: str
    enforcement: str


@dataclass(frozen=True)
class MissionProfile:
    summary: str
    constitution: tuple[str, ...]
    boundaries: tuple[BoundaryRule, ...]


@dataclass(frozen=True)
class RuntimeSnapshot:
    mode: str
    freeze_mode: bool
    active_plan: str | None
    memory_home: str
    remote_ledger: str
    autonomy_mode: str


@dataclass(frozen=True)
class KernelConfig:
    agent: AgentIdentity
    user: UserIdentityModel
    relationship: RelationshipModel
    mission: MissionProfile
    runtime: RuntimeSnapshot
    adapters: dict[str, str]
    paths: LocalPaths

    def to_summary(self) -> dict[str, object]:
        return {
            "agent": {
                "agent_id": self.agent.agent_id,
                "codename": self.agent.codename,
                "version": self.agent.version,
                "owner": self.agent.owner,
            },
            "user": {
                "user_id": self.user.user_id,
                "display_name": self.user.display_name,
                "timezone": self.user.timezone,
                "interaction_style": self.user.interaction_style,
            },
            "relationship": {
                "role": self.relationship.role,
                "promises": list(self.relationship.promises),
                "escalation_default": self.relationship.escalation_default,
            },
            "mission": {
                "summary": self.mission.summary,
                "constitution": list(self.mission.constitution),
                "boundaries": [
                    {
                        "name": boundary.name,
                        "intent": boundary.intent,
                        "enforcement": boundary.enforcement,
                    }
                    for boundary in self.mission.boundaries
                ],
            },
            "runtime": {
                "mode": self.runtime.mode,
                "freeze_mode": self.runtime.freeze_mode,
                "active_plan": self.runtime.active_plan,
                "memory_home": self.runtime.memory_home,
                "remote_ledger": self.runtime.remote_ledger,
                "autonomy_mode": self.runtime.autonomy_mode,
            },
            "adapters": dict(self.adapters),
            "paths": self.paths.to_dict(),
        }
