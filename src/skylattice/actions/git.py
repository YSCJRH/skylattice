"""Git adapter for controlled repository operations."""

from __future__ import annotations

import subprocess
from pathlib import Path


class GitCommandError(RuntimeError):
    pass


class GitAdapter:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root.resolve()

    def current_branch(self) -> str:
        return self._run(["git", "branch", "--show-current"]).strip()

    def status_porcelain(self) -> str:
        return self._run(["git", "status", "--short"])

    def create_branch(self, branch_name: str) -> dict[str, str]:
        self._run(["git", "checkout", "-b", branch_name])
        return {"branch": branch_name}

    def checkout(self, branch_name: str) -> str:
        self._run(["git", "checkout", branch_name])
        return branch_name

    def add_all(self) -> None:
        self._run(["git", "add", "--all"])

    def commit(self, message: str) -> str:
        self._run(["git", "commit", "-m", message])
        return message

    def push(self, branch_name: str, remote: str = "origin") -> str:
        self._run(["git", "-c", "protocol.file.allow=always", "push", "-u", remote, branch_name])
        return branch_name

    def current_commit(self) -> str:
        return self._run(["git", "rev-parse", "HEAD"]).strip()

    def cherry_pick(self, commit: str) -> str:
        self._run(["git", "cherry-pick", commit])
        return commit

    def revert(self, commit: str) -> str:
        self._run(["git", "revert", "--no-edit", commit])
        return commit

    def has_branch(self, branch_name: str) -> bool:
        completed = subprocess.run(
            ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch_name}"],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        return completed.returncode == 0

    def remote_url(self, remote: str = "origin") -> str:
        return self._run(["git", "remote", "get-url", remote]).strip()

    def _run(self, command: list[str]) -> str:
        completed = subprocess.run(
            command,
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise GitCommandError(completed.stderr.strip() or completed.stdout.strip() or " ".join(command))
        return completed.stdout
