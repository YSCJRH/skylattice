"""Provider interfaces for plan and content generation."""

from __future__ import annotations

from typing import Any, Protocol


class LLMProvider(Protocol):
    def generate_plan(
        self,
        *,
        goal: str,
        repo_context: dict[str, Any],
        allowed_validation_commands: tuple[str, ...],
    ) -> dict[str, Any]:
        ...

    def rewrite_file(
        self,
        *,
        goal: str,
        path: str,
        current_content: str,
        instructions: str,
        plan_summary: str,
        repo_context: dict[str, Any],
    ) -> str:
        ...

    def materialize_edit(
        self,
        *,
        goal: str,
        path: str,
        mode: str,
        current_content: str,
        instructions: str,
        plan_summary: str,
        repo_context: dict[str, Any],
    ) -> dict[str, Any]:
        ...
