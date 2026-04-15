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

    def generate_plan(
        self,
        *,
        goal: str,
        repo_context: dict[str, Any],
        allowed_validation_commands: tuple[str, ...],
    ) -> dict[str, Any]:
        command_list = ", ".join(allowed_validation_commands)
        prompt = (
            "Create a constrained task plan for a single-user local-first repo agent.\n"
            "Goal:\n"
            f"{goal}\n\n"
            "Repository context:\n"
            f"{json.dumps(repo_context, indent=2)}\n\n"
            "Use memory_context when it helps clarify standing preferences, reusable workflows, or durable semantic context.\n"
            "Use github_context when it is available to keep pull request and issue-comment plans aligned with recent open collaboration state.\n"
            "The plan must stay within repo maintenance, docs, ADR, or small code-change work.\n"
            "Supported file operation modes: rewrite, replace_text, insert_after, append_text, create_file, copy_file, move_file, delete_file.\n"
            "Prefer replace_text, insert_after, or append_text over rewrite when a deterministic local edit is enough.\n"
            "Prefer create_file for new tracked text files and copy_file when starting from an existing tracked-safe template.\n"
            "Use move_file or delete_file only when the goal explicitly requires destructive tracked-file lifecycle changes.\n"
            "Destructive repo ops require separate destructive-repo-write approval, so prefer non-destructive edits when they are sufficient.\n"
            f"Allowed validation refs: {command_list}.\n"
            "Use validation_catalog from the repository context as the source of truth.\n"
            "Prefer returning validation command ids instead of raw commands when possible.\n"
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
                                "mode": {
                                    "type": "string",
                                    "enum": [
                                        "rewrite",
                                        "replace_text",
                                        "insert_after",
                                        "append_text",
                                        "create_file",
                                        "copy_file",
                                        "move_file",
                                        "delete_file",
                                    ],
                                },
                                "create_if_missing": {"type": "boolean"},
                                "source_path": {"type": "string"},
                                "instructions": {"type": "string"},
                            },
                            "required": ["path", "mode", "create_if_missing", "instructions"],
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
                    "pull_request",
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
        prompt = (
            "Convert high-level edit instructions into a deterministic text-edit payload.\n"
            f"Goal:\n{goal}\n\n"
            f"Plan summary:\n{plan_summary}\n\n"
            f"Target path: {path}\n"
            f"Edit mode: {mode}\n"
            f"Instructions: {instructions}\n\n"
            "Repository context:\n"
            f"{json.dumps(repo_context, indent=2)}\n\n"
            "Current content follows. Return only the structured payload for this edit mode.\n\n"
            f"{current_content}"
        )
        return self._request_json(prompt=prompt, schema=self._edit_schema(mode))

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

    @staticmethod
    def _edit_schema(mode: str) -> dict[str, Any]:
        if mode == "replace_text":
            return {
                "type": "json_schema",
                "name": "replace_text_edit",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "mode": {"type": "string", "enum": ["replace_text"]},
                        "target_text": {"type": "string"},
                        "replacement_text": {"type": "string"},
                        "expected_occurrences": {"type": "integer", "minimum": 1},
                    },
                    "required": ["mode", "target_text", "replacement_text", "expected_occurrences"],
                    "additionalProperties": False,
                },
            }
        if mode == "insert_after":
            return {
                "type": "json_schema",
                "name": "insert_after_edit",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "mode": {"type": "string", "enum": ["insert_after"]},
                        "anchor_text": {"type": "string"},
                        "insert_text": {"type": "string"},
                        "expected_occurrences": {"type": "integer", "minimum": 1},
                    },
                    "required": ["mode", "anchor_text", "insert_text", "expected_occurrences"],
                    "additionalProperties": False,
                },
            }
        if mode == "append_text":
            return {
                "type": "json_schema",
                "name": "append_text_edit",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "mode": {"type": "string", "enum": ["append_text"]},
                        "append_text": {"type": "string"},
                    },
                    "required": ["mode", "append_text"],
                    "additionalProperties": False,
                },
            }
        raise ValueError(f"Unsupported edit mode for materialization: {mode}")
