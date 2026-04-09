"""Tracked configuration loading for task-agent execution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from skylattice.storage import load_yaml, resolve_repo_root


DEFAULT_ALLOWED_COMMANDS = (
    "python -m pytest -q",
    "python -m compileall src/skylattice",
    "python -m skylattice.cli doctor",
    "git status --short",
)


@dataclass(frozen=True)
class TaskValidationPolicy:
    runner: str
    allowed_commands: tuple[str, ...]
    config_path: Path


def load_task_validation_policy(repo_root: Path | None = None) -> TaskValidationPolicy:
    root = resolve_repo_root(repo_root)
    raw = load_yaml("configs/task/validation.yaml", root)
    allowed = tuple(str(item) for item in raw.get("allowed_commands", DEFAULT_ALLOWED_COMMANDS))
    if not allowed:
        allowed = DEFAULT_ALLOWED_COMMANDS
    return TaskValidationPolicy(
        runner=str(raw.get("runner", "powershell")),
        allowed_commands=allowed,
        config_path=root / "configs" / "task" / "validation.yaml",
    )
