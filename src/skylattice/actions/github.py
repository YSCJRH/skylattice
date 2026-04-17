"""Direct GitHub REST API adapter."""

from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
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
            diagnostics = self.inspect_local_auth()
            if diagnostics["gh_auth_logged_in"]:
                raise RuntimeError(
                    "GITHUB_TOKEN is required for GitHubAdapter. `gh` is logged in on this machine, "
                    "but Skylattice does not automatically use it. Run "
                    "`python -m skylattice.cli doctor github-bridge --format env` to export explicit env vars."
                )
            raise RuntimeError(
                "GITHUB_TOKEN is required for GitHubAdapter. Set it explicitly or run "
                "`gh auth login` first, then use `python -m skylattice.cli doctor github-bridge --format env`."
            )
        repo_value = repository or os.environ.get("SKYLATTICE_GITHUB_REPOSITORY")
        if not repo_value:
            diagnostics = self.inspect_local_auth()
            detected = str(diagnostics.get("repo_hint_origin_detected") or "").strip()
            if detected:
                raise RuntimeError(
                    "SKYLATTICE_GITHUB_REPOSITORY is required for GitHubAdapter. "
                    f"`origin` suggests `{detected}`, but Skylattice does not adopt it automatically. Run "
                    "`python -m skylattice.cli doctor github-bridge --format env` to export an explicit repo hint."
                )
            raise RuntimeError(
                "SKYLATTICE_GITHUB_REPOSITORY is required for GitHubAdapter. Set it explicitly or run "
                "`python -m skylattice.cli doctor auth` to inspect repo-hint requirements."
            )
        self.repo = self._parse_repo(repo_value)
        self.api_base = api_base.rstrip("/")

    def get_repo(self) -> dict[str, Any]:
        return self._request_json("GET", f"/repos/{self.repo.slug}")

    def get_issue(self, issue_number: int) -> dict[str, Any]:
        payload = self._request_json("GET", f"/repos/{self.repo.slug}/issues/{issue_number}")
        return payload if isinstance(payload, dict) else {}

    def list_issues(
        self,
        *,
        state: str = "open",
        per_page: int = 10,
    ) -> list[dict[str, Any]]:
        payload = self._request_json(
            "GET",
            f"/repos/{self.repo.slug}/issues?{urlencode({'state': state, 'per_page': per_page})}",
        )
        if not isinstance(payload, list):
            return []
        return [item for item in payload if "pull_request" not in item]

    def list_pull_requests(
        self,
        *,
        state: str = "open",
        per_page: int = 10,
    ) -> list[dict[str, Any]]:
        payload = self._request_json(
            "GET",
            f"/repos/{self.repo.slug}/pulls?{urlencode({'state': state, 'per_page': per_page})}",
        )
        return payload if isinstance(payload, list) else []

    def get_pull_request(self, number: int) -> dict[str, Any]:
        payload = self._request_json("GET", f"/repos/{self.repo.slug}/pulls/{number}")
        if not isinstance(payload, dict):
            return {}
        return self._normalize_pull_request(payload)

    def find_open_pull_request_by_head(self, head_branch: str) -> dict[str, Any] | None:
        query = urlencode({"state": "open", "head": f"{self.repo.owner}:{head_branch}"})
        payload = self._request_json("GET", f"/repos/{self.repo.slug}/pulls?{query}")
        if not isinstance(payload, list) or not payload:
            return None
        first = payload[0]
        if not isinstance(first, dict):
            return None
        return self._normalize_pull_request(first, default_head_branch=head_branch)

    def get_repository(self, repo_slug: str) -> dict[str, Any]:
        return self._request_json("GET", f"/repos/{self._parse_repo(repo_slug).slug}")

    def search_repositories(
        self,
        *,
        query: str,
        sort: str = "stars",
        order: str = "desc",
        per_page: int = 30,
        page: int = 1,
    ) -> list[dict[str, Any]]:
        encoded = urlencode(
            {
                "q": query,
                "sort": sort,
                "order": order,
                "per_page": per_page,
                "page": page,
            }
        )
        payload = self._request_json("GET", f"/search/repositories?{encoded}")
        if isinstance(payload, dict):
            items = payload.get("items", [])
            return items if isinstance(items, list) else []
        return []

    def get_latest_release(self, repo_slug: str) -> dict[str, Any] | None:
        try:
            payload = self._request_json("GET", f"/repos/{self._parse_repo(repo_slug).slug}/releases/latest")
        except RuntimeError as exc:
            if "404" in str(exc):
                return None
            raise
        return payload if isinstance(payload, dict) else None

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

    def list_issue_comments(self, *, issue_number: int, per_page: int = 100) -> list[dict[str, Any]]:
        payload = self._request_json(
            "GET",
            f"/repos/{self.repo.slug}/issues/{issue_number}/comments?{urlencode({'per_page': per_page})}",
        )
        return payload if isinstance(payload, list) else []

    def create_or_reuse_issue_comment(self, *, issue_number: int, body: str, dedupe_key: str) -> dict[str, Any]:
        marker = self._comment_marker(dedupe_key)
        for comment in self.list_issue_comments(issue_number=issue_number):
            if marker in str(comment.get("body", "")):
                return {
                    **comment,
                    "reused": True,
                    "sync_mode": "reuse",
                    "dedupe_key": dedupe_key,
                }

        payload = self.add_issue_comment(
            issue_number=issue_number,
            body=self._append_comment_marker(body, marker),
        )
        return {
            **payload,
            "reused": False,
            "sync_mode": "create",
            "dedupe_key": dedupe_key,
        }

    def create_or_update_draft_pr(
        self,
        *,
        head_branch: str,
        base_branch: str,
        title: str,
        body: str,
    ) -> dict[str, Any]:
        existing = self.find_open_pull_request_by_head(head_branch)
        if existing is not None:
            number = int(existing["number"])
            payload = self._request_json(
                "PATCH",
                f"/repos/{self.repo.slug}/pulls/{number}",
                {"title": title, "body": body, "base": base_branch},
            )
            return {
                **self._normalize_pull_request(payload, default_head_branch=head_branch, default_base_branch=base_branch),
                "reused": True,
                "sync_mode": "update",
                "dedupe_key": head_branch,
            }
        payload = self._request_json(
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
        return {
            **self._normalize_pull_request(payload, default_head_branch=head_branch, default_base_branch=base_branch),
            "reused": False,
            "sync_mode": "create",
            "dedupe_key": head_branch,
        }

    def smoke_check(self) -> dict[str, Any]:
        repo = self.get_repo()
        issues = self.list_issues(per_page=1)
        return {
            "provider": "github",
            "status": "ok",
            "repository": self.repo.slug,
            "default_branch": str(repo.get("default_branch", "")),
            "visibility": "private" if bool(repo.get("private", False)) else "public",
            "issue_sample_count": len(issues),
            "checks": ["get_repo", "list_issues"],
        }

    @classmethod
    def inspect_local_auth(
        cls,
        *,
        repo_root: Path | None = None,
        environ: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        env = environ or dict(os.environ)
        gh_status = cls._run_local_command(["gh", "auth", "status"], cwd=repo_root)
        gh_token = cls._run_local_command(["gh", "auth", "token"], cwd=repo_root) if gh_status["command_available"] else {
            "command_available": False,
            "returncode": 127,
            "stdout": "",
            "stderr": "",
        }
        git_origin = cls._run_local_command(["git", "remote", "get-url", "origin"], cwd=repo_root)
        gh_output = "\n".join(
            part for part in [str(gh_status.get("stdout", "")), str(gh_status.get("stderr", ""))] if part
        ).strip()
        origin_remote_url = str(git_origin.get("stdout", "")).strip() or None
        return {
            "gh_cli_available": bool(gh_status["command_available"]),
            "gh_auth_logged_in": bool(gh_status["command_available"] and int(gh_status["returncode"]) == 0),
            "gh_auth_token_accessible": bool(
                gh_token["command_available"] and int(gh_token["returncode"]) == 0 and str(gh_token["stdout"]).strip()
            ),
            "gh_account": cls._extract_gh_account(gh_output),
            "github_token_env_present": bool(str(env.get("GITHUB_TOKEN", "")).strip()),
            "repo_hint_env_present": bool(str(env.get("SKYLATTICE_GITHUB_REPOSITORY", "")).strip()),
            "repo_hint_origin_detected": cls._parse_repo_candidate(origin_remote_url),
            "origin_remote_url": origin_remote_url,
        }

    @classmethod
    def build_explicit_bridge(
        cls,
        *,
        repo_root: Path | None = None,
        preferred_repository: str | None = None,
        environ: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        env = environ or dict(os.environ)
        diagnostics = cls.inspect_local_auth(repo_root=repo_root, environ=env)
        repo_hint = str(preferred_repository or env.get("SKYLATTICE_GITHUB_REPOSITORY", "")).strip()
        repo_hint_source = "explicit" if repo_hint else ""
        if not repo_hint:
            detected = str(diagnostics.get("repo_hint_origin_detected") or "").strip()
            if detected:
                repo_hint = detected
                repo_hint_source = "origin"

        token_value = str(env.get("GITHUB_TOKEN", "")).strip()
        token_source = "env" if token_value else ""
        if not token_value and diagnostics["gh_auth_token_accessible"]:
            gh_token = cls._run_local_command(["gh", "auth", "token"], cwd=repo_root)
            token_value = str(gh_token.get("stdout", "")).strip()
            token_source = "gh" if token_value else ""

        issues: list[str] = []
        if not token_value:
            issues.append("No explicit or bridgeable GitHub token is available.")
        if not repo_hint:
            issues.append("No explicit or inferable GitHub repository slug is available.")

        return {
            "bridge_ready": not issues,
            "token_source": token_source or None,
            "repo_hint_source": repo_hint_source or None,
            "repo_hint": repo_hint or None,
            "issues": issues,
            "token_value": token_value,
            "diagnostics": diagnostics,
        }

    @staticmethod
    def format_explicit_bridge_env(bridge: dict[str, Any]) -> str:
        if not bridge["bridge_ready"]:
            lines = [
                "# Unable to build an explicit GitHub bridge for Skylattice.",
                *[f"# - {issue}" for issue in bridge.get("issues", [])],
                "# Run `python -m skylattice.cli doctor auth` for a read-only capability report.",
            ]
            return "\n".join(lines) + "\n"
        token_value = str(bridge["token_value"])
        repo_hint = str(bridge["repo_hint"])
        return "\n".join(
            [
                f"$env:GITHUB_TOKEN = '{token_value}'",
                f"$env:SKYLATTICE_GITHUB_REPOSITORY = '{repo_hint}'",
            ]
        ) + "\n"

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

    @staticmethod
    def _comment_marker(dedupe_key: str) -> str:
        return f"<!-- skylattice:{dedupe_key} -->"

    @staticmethod
    def _append_comment_marker(body: str, marker: str) -> str:
        if marker in body:
            return body
        return f"{body.rstrip()}\n\n{marker}"

    @classmethod
    def _parse_repo_candidate(cls, value: str | None) -> str | None:
        if not value:
            return None
        try:
            return cls._parse_repo(value).slug
        except ValueError:
            return None

    @staticmethod
    def _extract_gh_account(output: str) -> str | None:
        match = re.search(r"Logged in to github\.com account ([^\s]+)", output)
        return match.group(1) if match else None

    @staticmethod
    def _run_local_command(command: list[str], *, cwd: Path | None = None) -> dict[str, Any]:
        try:
            completed = subprocess.run(
                command,
                cwd=str(cwd) if cwd is not None else None,
                capture_output=True,
                text=False,
                check=False,
            )
        except FileNotFoundError:
            return {
                "command_available": False,
                "returncode": 127,
                "stdout": "",
                "stderr": "command not found",
            }
        return {
            "command_available": True,
            "returncode": completed.returncode,
            "stdout": completed.stdout.decode("utf-8", errors="replace"),
            "stderr": completed.stderr.decode("utf-8", errors="replace"),
        }

    @staticmethod
    def _normalize_pull_request(
        payload: dict[str, Any],
        *,
        default_head_branch: str | None = None,
        default_base_branch: str | None = None,
    ) -> dict[str, Any]:
        head = payload.get("head")
        base = payload.get("base")
        head_branch = (
            str(head.get("ref"))
            if isinstance(head, dict) and head.get("ref")
            else str(payload.get("head_branch") or default_head_branch or "")
        )
        base_branch = (
            str(base.get("ref"))
            if isinstance(base, dict) and base.get("ref")
            else str(payload.get("base_branch") or default_base_branch or "")
        )
        return {
            **payload,
            "number": payload.get("number"),
            "html_url": payload.get("html_url"),
            "state": str(payload.get("state", "open") or "open"),
            "draft": bool(payload.get("draft", False)),
            "head_branch": head_branch,
            "base_branch": base_branch,
        }
