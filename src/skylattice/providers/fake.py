"""Testing provider doubles."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FakeProvider:
    plan: dict[str, Any]
    file_outputs: dict[str, str] = field(default_factory=dict)

    def generate_plan(self, *, goal: str, repo_context: dict[str, Any]) -> dict[str, Any]:
        return dict(self.plan)

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
        if path in self.file_outputs:
            return self.file_outputs[path]
        if current_content:
            return current_content + "\n" + instructions + "\n"
        return instructions + "\n"
