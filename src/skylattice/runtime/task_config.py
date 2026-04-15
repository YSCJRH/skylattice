"""Tracked configuration loading for task-agent execution."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from skylattice.storage import load_yaml, resolve_repo_root


DEFAULT_ALLOWED_COMMANDS = (
    "python -m pytest -q",
    "python -m compileall src/skylattice",
    "python -m skylattice.cli doctor",
    "git status --short",
)


@dataclass(frozen=True)
class ValidationCommandSpec:
    id: str
    command: str
    description: str = ""
    expected_returncode: int = 0
    stdout_contains: tuple[str, ...] = ()
    stderr_contains: tuple[str, ...] = ()


@dataclass(frozen=True)
class TaskValidationPolicy:
    runner: str
    commands: tuple[ValidationCommandSpec, ...]
    profiles: dict[str, tuple[str, ...]]
    default_profile: str
    config_path: Path

    @property
    def allowed_commands(self) -> tuple[str, ...]:
        return tuple(spec.command for spec in self.commands)

    @property
    def command_ids(self) -> tuple[str, ...]:
        return tuple(spec.id for spec in self.commands)

    @property
    def allowed_refs(self) -> tuple[str, ...]:
        values = list(self.command_ids) + list(self.allowed_commands)
        return tuple(dict.fromkeys(values))

    def resolve_command(self, value: str) -> ValidationCommandSpec:
        normalized = value.strip()
        for spec in self.commands:
            if normalized in {spec.id, spec.command}:
                return spec
        raise ValueError(f"Validation command is outside tracked policy: {value}")

    def command_catalog(self) -> list[dict[str, object]]:
        return [
            {
                "id": spec.id,
                "command": spec.command,
                "description": spec.description,
                "expected_returncode": spec.expected_returncode,
                "stdout_contains": list(spec.stdout_contains),
                "stderr_contains": list(spec.stderr_contains),
            }
            for spec in self.commands
        ]

    def profile_command_ids(self, profile_name: str | None = None) -> tuple[str, ...]:
        name = profile_name or self.default_profile
        values = self.profiles.get(name)
        if values is None:
            raise KeyError(f"Unknown validation profile: {name}")
        return values


def load_task_validation_policy(repo_root: Path | None = None) -> TaskValidationPolicy:
    root = resolve_repo_root(repo_root)
    raw = load_yaml("configs/task/validation.yaml", root)
    commands = _load_command_specs(raw)
    profiles = _load_profiles(raw, commands)
    default_profile = str(raw.get("default_profile", "baseline")).strip() or "baseline"
    if default_profile not in profiles:
        profiles = {**profiles, default_profile: tuple(spec.id for spec in commands)}
    return TaskValidationPolicy(
        runner=str(raw.get("runner", "powershell")),
        commands=commands,
        profiles=profiles,
        default_profile=default_profile,
        config_path=root / "configs" / "task" / "validation.yaml",
    )


def _load_command_specs(raw: dict[str, Any]) -> tuple[ValidationCommandSpec, ...]:
    command_items = raw.get("commands")
    if isinstance(command_items, list) and command_items:
        specs = tuple(_parse_command_spec(item, index) for index, item in enumerate(command_items, start=1))
        if specs:
            return specs

    allowed = tuple(str(item) for item in raw.get("allowed_commands", DEFAULT_ALLOWED_COMMANDS))
    if not allowed:
        allowed = DEFAULT_ALLOWED_COMMANDS
    return tuple(
        ValidationCommandSpec(
            id=_legacy_command_id(command, index),
            command=command,
        )
        for index, command in enumerate(allowed, start=1)
    )


def _parse_command_spec(item: object, index: int) -> ValidationCommandSpec:
    if not isinstance(item, dict):
        raise ValueError("Validation command entries must be objects.")
    command = str(item.get("command", "")).strip()
    if not command:
        raise ValueError("Validation command entries require a non-empty command.")
    spec_id = str(item.get("id", "")).strip() or _legacy_command_id(command, index)
    return ValidationCommandSpec(
        id=spec_id,
        command=command,
        description=str(item.get("description", "")).strip(),
        expected_returncode=int(item.get("expected_returncode", 0)),
        stdout_contains=_coerce_string_tuple(item.get("stdout_contains")),
        stderr_contains=_coerce_string_tuple(item.get("stderr_contains")),
    )


def _load_profiles(
    raw: dict[str, Any],
    commands: tuple[ValidationCommandSpec, ...],
) -> dict[str, tuple[str, ...]]:
    known_ids = {spec.id for spec in commands}
    raw_profiles = raw.get("profiles")
    if isinstance(raw_profiles, dict) and raw_profiles:
        profiles: dict[str, tuple[str, ...]] = {}
        for name, values in raw_profiles.items():
            entries = tuple(str(item).strip() for item in values or [] if str(item).strip())
            unknown = [value for value in entries if value not in known_ids]
            if unknown:
                raise ValueError(f"Validation profile {name} references unknown command ids: {', '.join(unknown)}")
            profiles[str(name)] = entries
        return profiles
    return {"baseline": tuple(spec.id for spec in commands)}


def _coerce_string_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value if str(item).strip())
    return ()


def _legacy_command_id(command: str, index: int) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", command.lower()).strip("-")
    slug = re.sub(r"-+", "-", slug)
    return slug[:48] or f"validation-{index}"
