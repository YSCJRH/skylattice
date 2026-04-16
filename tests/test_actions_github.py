from __future__ import annotations

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
