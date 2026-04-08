"""Kernel loading and summary helpers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from skylattice.storage import LocalPaths, deep_merge, load_yaml, load_yaml_path

from .models import (
    AgentIdentity,
    BoundaryRule,
    KernelConfig,
    MissionProfile,
    RelationshipModel,
    RuntimeSnapshot,
    UserIdentityModel,
)


def _mapping(raw: dict[str, Any], key: str) -> dict[str, Any]:
    value = raw.get(key, {})
    return value if isinstance(value, dict) else {}


def _env_overlay() -> dict[str, Any]:
    overlay: dict[str, Any] = {}
    mapping = {
        "SKYLATTICE_AGENT_ID": ("agent", "id"),
        "SKYLATTICE_AGENT_VERSION": ("agent", "version"),
        "SKYLATTICE_AGENT_OWNER": ("agent", "owner"),
        "SKYLATTICE_USER_ID": ("user_model", "user_id"),
        "SKYLATTICE_USER_DISPLAY_NAME": ("user_model", "display_name"),
        "SKYLATTICE_USER_TIMEZONE": ("user_model", "timezone"),
        "SKYLATTICE_RUNTIME_MODE": ("runtime", "mode"),
        "SKYLATTICE_AUTONOMY_MODE": ("runtime", "autonomy_mode"),
        "SKYLATTICE_GITHUB_REPOSITORY": ("runtime", "remote_ledger"),
    }
    for env_name, path in mapping.items():
        value = os.environ.get(env_name)
        if not value:
            continue
        branch = overlay
        for key in path[:-1]:
            branch = branch.setdefault(key, {})
        branch[path[-1]] = value

    freeze_mode = os.environ.get("SKYLATTICE_FREEZE_MODE")
    if freeze_mode is not None:
        overlay.setdefault("runtime", {})["freeze_mode"] = freeze_mode.lower() in {"1", "true", "yes"}
    return overlay


def load_kernel_raw(repo_root: Path | None = None) -> dict[str, Any]:
    repo_path = (repo_root or Path(__file__).resolve().parents[3]).resolve()
    tracked = load_yaml("configs/agent/defaults.yaml", repo_path)
    overrides = load_yaml_path(repo_path / ".local" / "overrides" / "agent.yaml")
    return deep_merge(deep_merge(tracked, overrides), _env_overlay())


def load_kernel_config(repo_root: Path | None = None) -> KernelConfig:
    repo_path = (repo_root or Path(__file__).resolve().parents[3]).resolve()
    raw = load_kernel_raw(repo_path)
    paths = LocalPaths.from_repo_root(repo_path)

    agent_raw = _mapping(raw, "agent")
    user_raw = _mapping(raw, "user_model")
    relationship_raw = _mapping(raw, "relationship")
    mission_raw = _mapping(raw, "mission")
    runtime_raw = _mapping(raw, "runtime")
    adapters_raw = _mapping(raw, "adapters")

    boundaries = []
    for item in mission_raw.get("boundaries", []):
        if not isinstance(item, dict):
            continue
        boundaries.append(
            BoundaryRule(
                name=str(item.get("name", "unnamed-boundary")),
                intent=str(item.get("intent", "")),
                enforcement=str(item.get("enforcement", "")),
            )
        )

    return KernelConfig(
        agent=AgentIdentity(
            agent_id=str(agent_raw.get("id", "skylattice")),
            codename=str(agent_raw.get("codename", "skylattice")),
            version=str(agent_raw.get("version", "0.1.0")),
            owner=str(agent_raw.get("owner", "local-user")),
        ),
        user=UserIdentityModel(
            user_id=str(user_raw.get("user_id", "local-user")),
            display_name=str(user_raw.get("display_name", "user")),
            timezone=str(user_raw.get("timezone", "UTC")),
            interaction_style=str(user_raw.get("interaction_style", "concise")),
        ),
        relationship=RelationshipModel(
            role=str(relationship_raw.get("role", "personal evolvable agent")),
            promises=tuple(str(item) for item in relationship_raw.get("promises", [])),
            escalation_default=str(
                relationship_raw.get("escalation_default", "ask-before-repo-or-external-write")
            ),
        ),
        mission=MissionProfile(
            summary=str(mission_raw.get("summary", "")),
            constitution=tuple(str(item) for item in mission_raw.get("constitution", [])),
            boundaries=tuple(boundaries),
        ),
        runtime=RuntimeSnapshot(
            mode=str(runtime_raw.get("mode", "bootstrap")),
            freeze_mode=bool(runtime_raw.get("freeze_mode", False)),
            active_plan=runtime_raw.get("active_plan"),
            memory_home=str(runtime_raw.get("memory_home", str(paths.memory_root))),
            remote_ledger=str(runtime_raw.get("remote_ledger", "")),
            autonomy_mode=str(runtime_raw.get("autonomy_mode", "proactive-low-risk")),
        ),
        adapters={str(key): str(value) for key, value in adapters_raw.items()},
        paths=paths,
    )


def build_kernel_summary(repo_root: Path | None = None) -> dict[str, object]:
    return load_kernel_config(repo_root).to_summary()
