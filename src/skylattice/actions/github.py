"""Direct GitHub REST API adapter."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class GitHubRepoRef:
    owner: str
    name: str

    @property
    def slug(self) -> str:
        return f"{self.owner}/{self.name}"


class GitHubAdapter:
    def __init__(
        self,
        *,
        token: str | None = None,
        repository: str | None = None,
        api_base: str = "https://api.github.com",
    ) -> None:
        self.token = token or os.environ.get("GITHUB_TOKEN")
        if not self.token:
            raise RuntimeError("GITHUB_TOKEN is required for GitHubAdapter")
        repo_value = repository or os.environ.get("SKYLATTICE_GITHUB_REPOSITORY")
        if not repo_value:
            raise RuntimeError("SKYLATTICE_GITHUB_REPOSITORY is required for GitHubAdapter")
        self.repo = self._parse_repo(repo_value)
        self.api_base = api_base.rstrip("/")

    def get_repo(self) -> dict[str, Any]:
        return self._request_json("GET", f"/repos/{self.repo.slug}")

    def create_issue(self, *, title: str, body: str) -> dict[str, Any]:
        return self._request_json(
            "POST",
            f"/repos/{self.repo.slug}/issues",
            {"title": title, "body": body},
        )

    def add_issue_comment(self, *, issue_number: int, body: str) -> dict[str, Any]:
        return self._request_json(
            "POST",
            f"/repos/{self.repo.slug}/issues/{issue_number}/comments",
            {"body": body},
        )

    def create_or_update_draft_pr(
        self,
        *,
        head_branch: str,
        base_branch: str,
        title: str,
        body: str,
    ) -> dict[str, Any]:
        query = urlencode({"state": "open", "head": f"{self.repo.owner}:{head_branch}"})
        open_pulls = self._request_json("GET", f"/repos/{self.repo.slug}/pulls?{query}")
        if isinstance(open_pulls, list) and open_pulls:
            number = int(open_pulls[0]["number"])
            return self._request_json(
                "PATCH",
                f"/repos/{self.repo.slug}/pulls/{number}",
                {"title": title, "body": body, "base": base_branch},
            )
        return self._request_json(
            "POST",
            f"/repos/{self.repo.slug}/pulls",
            {
                "title": title,
                "body": body,
                "head": head_branch,
                "base": base_branch,
                "draft": True,
            },
        )

    def _request_json(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            f"{self.api_base}{path}",
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
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
            raise RuntimeError(f"GitHub request failed: {exc.code} {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"GitHub request failed: {exc.reason}") from exc

    @staticmethod
    def _parse_repo(value: str) -> GitHubRepoRef:
        cleaned = value.strip().removesuffix(".git")
        if cleaned.startswith("https://github.com/"):
            cleaned = cleaned.replace("https://github.com/", "", 1)
        elif cleaned.startswith("git@github.com:"):
            cleaned = cleaned.replace("git@github.com:", "", 1)
        elif cleaned.startswith("github.com/"):
            cleaned = cleaned.replace("github.com/", "", 1)

        if not re.fullmatch(r"[^/]+/[^/]+", cleaned):
            raise ValueError(f"Unsupported GitHub repository value: {value}")
        owner, name = cleaned.split("/", 1)
        return GitHubRepoRef(owner=owner, name=name)
