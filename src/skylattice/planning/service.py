"""Constrained planner for the CLI-first task agent."""

from __future__ import annotations

from typing import Any

from skylattice.providers import LLMProvider


class TaskPlanner:
    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    def create_plan(self, *, goal: str, repo_context: dict[str, Any]) -> dict[str, Any]:
        plan = self.provider.generate_plan(goal=goal, repo_context=repo_context)
        if not plan.get("file_operations"):
            raise RuntimeError("Planner did not return any file operations")
        return plan
