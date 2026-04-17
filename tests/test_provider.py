from __future__ import annotations

from pathlib import Path

from skylattice.providers.openai import OpenAIProvider


def test_openai_provider_loads_tracked_prompt_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    prompts = repo / "prompts" / "system"
    prompts.mkdir(parents=True)
    (prompts / "core-mission.md").write_text("# Core Mission\n\nProtect the user.\n", encoding="utf-8")
    (prompts / "planner.md").write_text("# Planner Prompt\n\nKeep changes small.\n", encoding="utf-8")
    (prompts / "editor.md").write_text("# Editor Prompt\n\nReturn only exact edits.\n", encoding="utf-8")

    provider = OpenAIProvider(api_key="test-key", repo_root=repo)

    instructions = provider._compose_instructions(
        "core-mission.md",
        "planner.md",
        "editor.md",
        fallback="fallback instructions",
    )

    assert "# Core Mission" in instructions
    assert "Protect the user." in instructions
    assert "# Planner Prompt" in instructions
    assert "Keep changes small." in instructions
    assert "# Editor Prompt" in instructions
    assert "Return only exact edits." in instructions


def test_openai_provider_falls_back_when_tracked_prompt_file_is_missing(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    provider = OpenAIProvider(api_key="test-key", repo_root=repo)

    instructions = provider._compose_instructions(
        "core-mission.md",
        fallback="fallback instructions",
    )

    assert instructions == "fallback instructions"


def test_openai_provider_generate_plan_uses_tracked_instructions(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    prompts = repo / "prompts" / "system"
    prompts.mkdir(parents=True)
    (prompts / "core-mission.md").write_text("# Core Mission\n\nProtect the user.\n", encoding="utf-8")
    (prompts / "planner.md").write_text("# Planner Prompt\n\nKeep changes small.\n", encoding="utf-8")
    (prompts / "task-plan-input.md").write_text(
        "# Task Plan Input\n\nGoal:\n{{GOAL}}\n\nAllowed validation refs: {{ALLOWED_VALIDATION_REFS}}\n",
        encoding="utf-8",
    )

    provider = OpenAIProvider(api_key="test-key", repo_root=repo)
    captured: dict[str, object] = {}

    def fake_request_json(*, prompt: str, schema: dict[str, object], instructions: str) -> dict[str, object]:
        captured["prompt"] = prompt
        captured["schema"] = schema
        captured["instructions"] = instructions
        return {
            "summary": "test summary",
            "branch_name": "test-branch",
            "file_operations": [
                {
                    "path": "README.md",
                    "mode": "append_text",
                    "create_if_missing": False,
                    "instructions": "Append a short note.",
                }
            ],
            "validation_commands": [],
            "commit_message": "docs: test",
            "pull_request": {
                "title": "docs: test",
                "body": "body",
                "base_branch": "main",
            },
        }

    provider._request_json = fake_request_json  # type: ignore[method-assign]

    plan = provider.generate_plan(
        goal="Update the README.",
        repo_context={"validation_catalog": []},
        allowed_validation_commands=("pytest",),
    )

    assert plan["branch_name"] == "test-branch"
    assert "# Core Mission" in str(captured["instructions"])
    assert "# Planner Prompt" in str(captured["instructions"])
    assert "# Task Plan Input" in str(captured["prompt"])
    assert "Update the README." in str(captured["prompt"])
    assert "pytest" in str(captured["prompt"])


def test_openai_provider_rewrite_file_uses_tracked_editor_and_prompt_templates(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    prompts = repo / "prompts" / "system"
    prompts.mkdir(parents=True)
    (prompts / "core-mission.md").write_text("# Core Mission\n\nProtect the user.\n", encoding="utf-8")
    (prompts / "editor.md").write_text("# Editor Prompt\n\nReturn exact file content.\n", encoding="utf-8")
    (prompts / "file-rewrite-input.md").write_text(
        "# File Rewrite Input\n\nTarget path: {{TARGET_PATH}}\n\n{{CURRENT_CONTENT}}\n",
        encoding="utf-8",
    )

    provider = OpenAIProvider(api_key="test-key", repo_root=repo)
    captured: dict[str, object] = {}

    def fake_request_json(*, prompt: str, schema: dict[str, object], instructions: str) -> dict[str, object]:
        captured["prompt"] = prompt
        captured["instructions"] = instructions
        return {"content": "updated content"}

    provider._request_json = fake_request_json  # type: ignore[method-assign]

    result = provider.rewrite_file(
        goal="Refresh the README.",
        path="README.md",
        current_content="old content",
        instructions="Replace the intro.",
        plan_summary="Refresh the intro section.",
        repo_context={},
    )

    assert result == "updated content"
    assert "# Editor Prompt" in str(captured["instructions"])
    assert "# File Rewrite Input" in str(captured["prompt"])
    assert "README.md" in str(captured["prompt"])
    assert "old content" in str(captured["prompt"])


def test_openai_provider_materialize_edit_uses_tracked_editor_and_prompt_templates(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    prompts = repo / "prompts" / "system"
    prompts.mkdir(parents=True)
    (prompts / "core-mission.md").write_text("# Core Mission\n\nProtect the user.\n", encoding="utf-8")
    (prompts / "editor.md").write_text("# Editor Prompt\n\nReturn exact structured payloads.\n", encoding="utf-8")
    (prompts / "edit-materialization-input.md").write_text(
        "# Edit Materialization Input\n\nEdit mode: {{EDIT_MODE}}\n\n{{CURRENT_CONTENT}}\n",
        encoding="utf-8",
    )

    provider = OpenAIProvider(api_key="test-key", repo_root=repo)
    captured: dict[str, object] = {}

    def fake_request_json(*, prompt: str, schema: dict[str, object], instructions: str) -> dict[str, object]:
        captured["prompt"] = prompt
        captured["instructions"] = instructions
        return {
            "mode": "append_text",
            "append_text": "\nnew line\n",
        }

    provider._request_json = fake_request_json  # type: ignore[method-assign]

    payload = provider.materialize_edit(
        goal="Append a note.",
        path="README.md",
        mode="append_text",
        current_content="old content",
        instructions="Append a note at the end.",
        plan_summary="Add a note.",
        repo_context={},
    )

    assert payload["mode"] == "append_text"
    assert "# Editor Prompt" in str(captured["instructions"])
    assert "# Edit Materialization Input" in str(captured["prompt"])
    assert "append_text" in str(captured["prompt"])
    assert "old content" in str(captured["prompt"])


def test_openai_provider_smoke_check_uses_structured_request(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    prompts = repo / "prompts" / "system"
    prompts.mkdir(parents=True)
    (prompts / "connectivity-smoke.md").write_text("# Connectivity Smoke Check\n\nReturn exact JSON.\n", encoding="utf-8")
    (prompts / "connectivity-smoke-input.md").write_text('Return {"status":"ok"} and no additional keys.\n', encoding="utf-8")
    provider = OpenAIProvider(api_key="test-key", repo_root=repo)
    captured: dict[str, object] = {}

    def fake_request_json(*, prompt: str, schema: dict[str, object], instructions: str) -> dict[str, object]:
        captured["prompt"] = prompt
        captured["schema"] = schema
        captured["instructions"] = instructions
        return {"status": "ok"}

    provider._request_json = fake_request_json  # type: ignore[method-assign]

    payload = provider.smoke_check()

    assert payload == {"provider": "openai", "status": "ok", "model": provider.model}
    assert 'Return {"status":"ok"}' in str(captured["prompt"])
    assert "# Connectivity Smoke Check" in str(captured["instructions"])
