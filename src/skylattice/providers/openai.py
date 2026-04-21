"""Direct OpenAI Responses API provider."""

from __future__ import annotations

import json
import os
from typing import Any
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class OpenAIProvider:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        api_base: str = "https://api.openai.com/v1/responses",
        repo_root: Path | None = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model or os.environ.get("SKYLATTICE_OPENAI_MODEL", "gpt-5")
        self.api_base = api_base
        self.repo_root = (repo_root or Path(__file__).resolve().parents[3]).resolve()
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
        prompt = self._render_prompt_template(
            "task-plan-input.md",
            replacements={
                "GOAL": goal,
                "REPO_CONTEXT_JSON": json.dumps(repo_context, indent=2),
                "ALLOWED_VALIDATION_REFS": command_list,
            },
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
        return self._request_json(
            prompt=prompt,
            schema=schema,
            instructions=self._compose_instructions(
                "core-mission.md",
                "planner.md",
            ),
        )

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
        prompt = self._render_prompt_template(
            "file-rewrite-input.md",
            replacements={
                "GOAL": goal,
                "PLAN_SUMMARY": plan_summary,
                "TARGET_PATH": path,
                "INSTRUCTIONS": instructions,
                "REPO_CONTEXT_JSON": json.dumps(repo_context, indent=2),
                "CURRENT_CONTENT": current_content,
            },
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
        return str(
            self._request_json(
                prompt=prompt,
                schema=schema,
                instructions=self._compose_instructions(
                    "core-mission.md",
                    "editor.md",
                ),
            )["content"]
        )

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
        prompt = self._render_prompt_template(
            "edit-materialization-input.md",
            replacements={
                "GOAL": goal,
                "PLAN_SUMMARY": plan_summary,
                "TARGET_PATH": path,
                "EDIT_MODE": mode,
                "INSTRUCTIONS": instructions,
                "REPO_CONTEXT_JSON": json.dumps(repo_context, indent=2),
                "CURRENT_CONTENT": current_content,
            },
        )
        return self._request_json(
            prompt=prompt,
            schema=self._edit_schema(mode),
            instructions=self._compose_instructions(
                "core-mission.md",
                "editor.md",
            ),
        )

    def smoke_check(self) -> dict[str, Any]:
        schema = {
            "type": "json_schema",
            "name": "openai_smoke_check",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                },
                "required": ["status"],
                "additionalProperties": False,
            },
        }
        response = self._request_json(
            prompt=self._render_prompt_template(
                "connectivity-smoke-input.md",
                replacements={},
            ),
            schema=schema,
            instructions=self._compose_instructions(
                "connectivity-smoke.md",
            ),
        )
        if response.get("status") != "ok":
            raise RuntimeError(f"Unexpected OpenAI smoke response: {response}")
        return {
            "provider": "openai",
            "status": "ok",
            "model": self.model,
        }

    def _request_json(self, *, prompt: str, schema: dict[str, Any], instructions: str) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "instructions": instructions,
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

    def _compose_instructions(self, *prompt_files: str) -> str:
        return "\n\n".join(self._load_required_prompt_file(name) for name in prompt_files).strip()

    def _render_prompt_template(
        self,
        template_file: str,
        *,
        replacements: dict[str, str],
    ) -> str:
        content = self._load_required_prompt_file(template_file)
        rendered = content
        for key, value in replacements.items():
            rendered = rendered.replace(f"{{{{{key}}}}}", value)
        return rendered

    def _load_required_prompt_file(self, relative_name: str) -> str:
        content = self._load_prompt_file(relative_name)
        if not content:
            raise RuntimeError(f"Required prompt file is missing or empty: prompts/system/{relative_name}")
        return content

    def _load_prompt_file(self, relative_name: str) -> str:
        path = self.repo_root / "prompts" / "system" / relative_name
        if not path.exists():
            return ""
        content = path.read_text(encoding="utf-8").strip()
        return content

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
