"""Direct OpenAI Responses API provider."""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class OpenAIProvider:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        api_base: str = "https://api.openai.com/v1/responses",
    ) -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model or os.environ.get("SKYLATTICE_OPENAI_MODEL", "gpt-5")
        self.api_base = api_base
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is required for OpenAIProvider")

    def generate_plan(self, *, goal: str, repo_context: dict[str, Any]) -> dict[str, Any]:
        prompt = (
            "Create a constrained task plan for a single-user local-first repo agent.\n"
            "Goal:\n"
            f"{goal}\n\n"
            "Repository context:\n"
            f"{json.dumps(repo_context, indent=2)}\n\n"
            "The plan must stay within repo maintenance, docs, ADR, or small code-change work.\n"
            "Allowed validation commands: python -m pytest -q, python -m compileall src tests, git status --short.\n"
            "Return one branch name, one or more file operations, zero or more validation commands,\n"
            "one commit message, one draft pull request payload, and an optional issue comment payload."
        )
        schema = {
            "type": "json_schema",
            "name": "task_plan",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "branch_name": {"type": "string"},
                    "file_operations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "path": {"type": "string"},
                                "create_if_missing": {"type": "boolean"},
                                "instructions": {"type": "string"},
                            },
                            "required": ["path", "create_if_missing", "instructions"],
                            "additionalProperties": False,
                        },
                    },
                    "validation_commands": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "commit_message": {"type": "string"},
                    "pull_request": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "body": {"type": "string"},
                            "base_branch": {"type": "string"},
                        },
                        "required": ["title", "body", "base_branch"],
                        "additionalProperties": False,
                    },
                    "issue_comment": {
                        "type": "object",
                        "properties": {
                            "issue_number": {"type": "integer"},
                            "body": {"type": "string"},
                        },
                        "required": ["issue_number", "body"],
                        "additionalProperties": False,
                    },
                },
                "required": [
                    "summary",
                    "branch_name",
                    "file_operations",
                    "validation_commands",
                    "commit_message",
                    "pull_request"
                ],
                "additionalProperties": False,
            },
        }
        return self._request_json(prompt=prompt, schema=schema)

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
        prompt = (
            "Rewrite the target file for a constrained repository task.\n"
            f"Goal:\n{goal}\n\n"
            f"Plan summary:\n{plan_summary}\n\n"
            f"Target path: {path}\n"
            f"Instructions: {instructions}\n\n"
            "Repository context:\n"
            f"{json.dumps(repo_context, indent=2)}\n\n"
            "Current content follows. Return the full replacement file content only.\n\n"
            f"{current_content}"
        )
        schema = {
            "type": "json_schema",
            "name": "file_rewrite",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {"content": {"type": "string"}},
                "required": ["content"],
                "additionalProperties": False,
            },
        }
        return str(self._request_json(prompt=prompt, schema=schema)["content"])

    def _request_json(self, *, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "instructions": "You are Skylattice's constrained execution planner. Be precise and keep changes small.",
            "input": prompt,
            "text": {"format": schema},
        }
        body = json.dumps(payload).encode("utf-8")
        request = Request(
            self.api_base,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=60) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI request failed: {exc.code} {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"OpenAI request failed: {exc.reason}") from exc

        output_text = raw.get("output_text")
        if not output_text:
            raise RuntimeError(f"OpenAI response did not include output_text: {raw}")
        data = json.loads(output_text)
        if not isinstance(data, dict):
            raise RuntimeError("OpenAI structured output was not an object")
        return data
