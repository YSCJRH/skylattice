from __future__ import annotations

from pathlib import Path

from skylattice.providers.openai import OpenAIProvider


def test_openai_provider_loads_tracked_prompt_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    prompts = repo / "prompts" / "system"
    prompts.mkdir(parents=True)
    (prompts / "core-mission.md").write_text("# Core Mission\n\nProtect the user.\n", encoding="utf-8")
    (prompts / "planner.md").write_text("# Planner Prompt\n\nKeep changes small.\n", encoding="utf-8")

    provider = OpenAIProvider(api_key="test-key", repo_root=repo)

    instructions = provider._compose_instructions(
        "core-mission.md",
        "planner.md",
        fallback="fallback instructions",
    )

    assert "# Core Mission" in instructions
    assert "Protect the user." in instructions
    assert "# Planner Prompt" in instructions
    assert "Keep changes small." in instructions


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
    assert "Create a constrained task plan" in str(captured["prompt"])
