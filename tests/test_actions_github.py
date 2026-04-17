from __future__ import annotations

from pathlib import Path

from skylattice.actions.github import GitHubAdapter


def test_github_adapter_smoke_check_uses_read_only_calls(monkeypatch) -> None:
    adapter = GitHubAdapter(token="test-token", repository="example/skylattice")
    calls: list[tuple[str, str]] = []

    def fake_request_json(method: str, path: str, payload=None):
        calls.append((method, path))
        if path == "/repos/example/skylattice":
            return {"default_branch": "main", "private": False}
        if path.startswith("/repos/example/skylattice/issues?"):
            return []
        raise AssertionError(f"Unexpected request path: {path}")

    monkeypatch.setattr(adapter, "_request_json", fake_request_json)

    payload = adapter.smoke_check()

    assert payload["provider"] == "github"
    assert payload["status"] == "ok"
    assert payload["repository"] == "example/skylattice"
    assert payload["default_branch"] == "main"
    assert payload["visibility"] == "public"
    assert payload["issue_sample_count"] == 0
    assert payload["checks"] == ["get_repo", "list_issues"]
    assert calls == [
        ("GET", "/repos/example/skylattice"),
        ("GET", "/repos/example/skylattice/issues?state=open&per_page=1"),
    ]


def test_github_adapter_inspect_local_auth_detects_logged_in_cli_and_origin(monkeypatch, tmp_path: Path) -> None:
    def fake_run_local_command(command, *, cwd=None):
        if command == ["gh", "auth", "status"]:
            return {
                "command_available": True,
                "returncode": 0,
                "stdout": "Logged in to github.com account YSCJRH\n",
                "stderr": "",
            }
        if command == ["gh", "auth", "token"]:
            return {
                "command_available": True,
                "returncode": 0,
                "stdout": "gho_test_token_value\n",
                "stderr": "",
            }
        if command == ["git", "remote", "get-url", "origin"]:
            return {
                "command_available": True,
                "returncode": 0,
                "stdout": "https://github.com/YSCJRH/skylattice.git\n",
                "stderr": "",
            }
        raise AssertionError(f"Unexpected command: {command}")

    monkeypatch.setattr(GitHubAdapter, "_run_local_command", staticmethod(fake_run_local_command))

    diagnostics = GitHubAdapter.inspect_local_auth(repo_root=tmp_path, environ={})

    assert diagnostics["gh_cli_available"] is True
    assert diagnostics["gh_auth_logged_in"] is True
    assert diagnostics["gh_auth_token_accessible"] is True
    assert diagnostics["gh_account"] == "YSCJRH"
    assert diagnostics["repo_hint_origin_detected"] == "YSCJRH/skylattice"
    assert diagnostics["origin_remote_url"] == "https://github.com/YSCJRH/skylattice.git"


def test_github_adapter_build_explicit_bridge_formats_env_exports(monkeypatch, tmp_path: Path) -> None:
    def fake_run_local_command(command, *, cwd=None):
        if command == ["gh", "auth", "status"]:
            return {
                "command_available": True,
                "returncode": 0,
                "stdout": "Logged in to github.com account YSCJRH\n",
                "stderr": "",
            }
        if command == ["gh", "auth", "token"]:
            return {
                "command_available": True,
                "returncode": 0,
                "stdout": "gho_test_token_value\n",
                "stderr": "",
            }
        if command == ["git", "remote", "get-url", "origin"]:
            return {
                "command_available": True,
                "returncode": 0,
                "stdout": "https://github.com/YSCJRH/skylattice.git\n",
                "stderr": "",
            }
        raise AssertionError(f"Unexpected command: {command}")

    monkeypatch.setattr(GitHubAdapter, "_run_local_command", staticmethod(fake_run_local_command))

    bridge = GitHubAdapter.build_explicit_bridge(repo_root=tmp_path, environ={})
    rendered = GitHubAdapter.format_explicit_bridge_env(bridge)

    assert bridge["bridge_ready"] is True
    assert bridge["token_source"] == "gh"
    assert bridge["repo_hint_source"] == "origin"
    assert bridge["repo_hint"] == "YSCJRH/skylattice"
    assert "$env:GITHUB_TOKEN = 'gho_test_token_value'" in rendered
    assert "$env:SKYLATTICE_GITHUB_REPOSITORY = 'YSCJRH/skylattice'" in rendered
