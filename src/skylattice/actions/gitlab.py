"""Direct GitLab REST API adapter for radar discovery."""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


class GitLabAdapter:
    def __init__(
        self,
        *,
        token: str | None = None,
        api_base: str = "https://gitlab.com/api/v4",
    ) -> None:
        self.token = token or os.environ.get("GITLAB_TOKEN")
        if not self.token:
            raise RuntimeError(
                "GITLAB_TOKEN is required for GitLabAdapter. Set it explicitly before GitLab-backed radar use."
            )
        self.api_base = api_base.rstrip("/")

    def list_projects(
        self,
        *,
        topic: str | None = None,
        search: str | None = None,
        order_by: str = "last_activity_at",
        sort: str = "desc",
        per_page: int = 20,
        page: int = 1,
        visibility: str = "public",
        simple: bool = True,
    ) -> list[dict[str, Any]]:
        params = {
            "order_by": order_by,
            "sort": sort,
            "per_page": per_page,
            "page": page,
            "visibility": visibility,
            "simple": "true" if simple else "false",
            "archived": "false",
        }
        if topic:
            params["topic"] = topic
        if search:
            params["search"] = search
        payload = self._request_json("GET", f"/projects?{urlencode(params)}")
        return payload if isinstance(payload, list) else []

    def get_project(self, project_id_or_path: int | str) -> dict[str, Any]:
        payload = self._request_json("GET", f"/projects/{self._project_ref(project_id_or_path)}")
        return payload if isinstance(payload, dict) else {}

    def get_latest_release(self, project_id_or_path: int | str) -> dict[str, Any] | None:
        try:
            payload = self._request_json(
                "GET",
                f"/projects/{self._project_ref(project_id_or_path)}/releases/permalink/latest",
            )
        except RuntimeError as exc:
            if "404" in str(exc):
                return None
            raise
        return payload if isinstance(payload, dict) else None

    def smoke_check(self) -> dict[str, Any]:
        projects = self.list_projects(per_page=1)
        return {
            "provider": "gitlab",
            "status": "ok",
            "project_sample_count": len(projects),
            "checks": ["list_projects"],
        }

    @classmethod
    def inspect_local_auth(
        cls,
        *,
        environ: dict[str, str] | None = None,
        api_base: str = "https://gitlab.com/api/v4",
    ) -> dict[str, Any]:
        env = environ or dict(os.environ)
        return {
            "gitlab_token_env_present": bool(str(env.get("GITLAB_TOKEN", "")).strip()),
            "gitlab_api_base": api_base.rstrip("/"),
        }

    def _request_json(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            f"{self.api_base}{path}",
            data=data,
            method=method,
            headers={
                "PRIVATE-TOKEN": str(self.token),
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "skylattice-agent",
            },
        )
        try:
            with urlopen(request, timeout=60) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitLab request failed: {exc.code} {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"GitLab request failed: {exc.reason}") from exc

    @staticmethod
    def _project_ref(project_id_or_path: int | str) -> str:
        value = str(project_id_or_path).strip()
        if not value:
            raise ValueError("GitLab project reference cannot be empty")
        return value if value.isdigit() else quote(value, safe="")
