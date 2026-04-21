from __future__ import annotations

from skylattice.actions.gitlab import GitLabAdapter


def test_gitlab_adapter_smoke_check_uses_read_only_calls(monkeypatch) -> None:
    adapter = GitLabAdapter(token="test-token")
    calls: list[tuple[str, str]] = []

    def fake_request_json(method: str, path: str, payload=None):
        calls.append((method, path))
        if path.startswith("/projects?"):
            return [{"id": 1, "path_with_namespace": "example/skylattice"}]
        raise AssertionError(f"Unexpected request path: {path}")

    monkeypatch.setattr(adapter, "_request_json", fake_request_json)

    payload = adapter.smoke_check()

    assert payload["provider"] == "gitlab"
    assert payload["status"] == "ok"
    assert payload["project_sample_count"] == 1
    assert payload["checks"] == ["list_projects"]
    assert calls == [("GET", "/projects?order_by=last_activity_at&sort=desc&per_page=1&page=1&visibility=public&simple=true&archived=false")]


def test_gitlab_adapter_inspect_local_auth_reports_token_presence() -> None:
    diagnostics = GitLabAdapter.inspect_local_auth(environ={"GITLAB_TOKEN": "glpat-test"})

    assert diagnostics["gitlab_token_env_present"] is True
    assert diagnostics["gitlab_api_base"] == "https://gitlab.com/api/v4"
