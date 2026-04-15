"""Constrained planner for the CLI-first task agent."""

from __future__ import annotations

from typing import Any

from skylattice.providers import LLMProvider


SUPPORTED_EDIT_MODES = (
    "rewrite",
    "replace_text",
    "insert_after",
    "append_text",
    "create_file",
    "copy_file",
    "move_file",
    "delete_file",
)


class TaskPlanner:
    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    def create_plan(
        self,
        *,
        goal: str,
        repo_context: dict[str, Any],
        allowed_validation_commands: tuple[str, ...],
    ) -> dict[str, Any]:
        plan = self.provider.generate_plan(
            goal=goal,
            repo_context=repo_context,
            allowed_validation_commands=allowed_validation_commands,
        )
        allowed_values = set(allowed_validation_commands)
        validation_catalog = repo_context.get("validation_catalog", [])
        if isinstance(validation_catalog, list):
            for entry in validation_catalog:
                if isinstance(entry, dict):
                    allowed_values.add(str(entry.get("id", "")))
                    allowed_values.add(str(entry.get("command", "")))
        operations = plan.get("file_operations")
        if not operations:
            raise RuntimeError("Planner did not return any file operations")
        for operation in operations:
            if not isinstance(operation, dict):
                raise RuntimeError("Planner returned an invalid file operation payload")
            mode = str(operation.get("mode", "rewrite"))
            if mode not in SUPPORTED_EDIT_MODES:
                raise RuntimeError(f"Planner returned unsupported edit mode: {mode}")
            if not str(operation.get("path", "")).strip():
                raise RuntimeError("Planner returned a file operation without a path")
            if not str(operation.get("instructions", "")).strip():
                raise RuntimeError("Planner returned a file operation without instructions")
            if mode in {"copy_file", "move_file"} and not str(operation.get("source_path", "")).strip():
                raise RuntimeError(f"Planner returned {mode} without a source_path")
            operation["mode"] = mode
            operation["create_if_missing"] = bool(operation.get("create_if_missing", mode == "create_file"))

        for command in plan.get("validation_commands", []):
            if str(command) not in allowed_values:
                raise RuntimeError(f"Planner returned a validation command outside tracked policy: {command}")
        return plan
