"""Repository workspace adapter."""

from __future__ import annotations

import subprocess
from pathlib import Path


class RepoWorkspaceAdapter:
    SAFE_EXTENSIONS = {".md", ".txt", ".py", ".yaml", ".yml", ".json", ".toml"}
    CHECK_PREFIXES = (
        "python -m pytest",
        "python -m compileall",
        "git status --short",
    )
    IGNORE_PARTS = {".git", ".local", "__pycache__", ".pytest_cache", "build", "dist"}

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root.resolve()

    def list_files(self, *, limit: int = 200) -> list[str]:
        files: list[str] = []
        for path in self.repo_root.rglob("*"):
            if len(files) >= limit:
                break
            if not path.is_file():
                continue
            if any(part in self.IGNORE_PARTS for part in path.parts):
                continue
            if path.suffix == ".pyc" or path.name.endswith(".egg-info"):
                continue
            files.append(path.relative_to(self.repo_root).as_posix())
        return sorted(files)

    def read_text(self, relative_path: str) -> str:
        path = self._resolve(relative_path)
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def search(self, pattern: str) -> list[str]:
        matches: list[str] = []
        for rel_path in self.list_files(limit=500):
            content = self.read_text(rel_path)
            if pattern in content:
                matches.append(rel_path)
        return matches

    def write_text(self, relative_path: str, content: str, *, create_if_missing: bool = False) -> str:
        path = self._resolve(relative_path, allow_missing=create_if_missing)
        if not path.exists() and not create_if_missing:
            raise FileNotFoundError(path)
        if path.suffix and path.suffix not in self.SAFE_EXTENSIONS:
            raise ValueError(f"Writes to {path.suffix} files are not allowed in the MVP")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return str(path.relative_to(self.repo_root).as_posix())

    def replace_text(self, relative_path: str, old: str, new: str) -> str:
        content = self.read_text(relative_path)
        if old not in content:
            raise ValueError(f"Pattern not found in {relative_path}")
        updated = content.replace(old, new)
        return self.write_text(relative_path, updated)

    def run_check(self, command: str) -> dict[str, object]:
        if not command.startswith(self.CHECK_PREFIXES):
            raise ValueError(f"Command not allowed: {command}")
        completed = subprocess.run(
            ["powershell", "-Command", command],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        return {
            "command": command,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }

    def _resolve(self, relative_path: str, *, allow_missing: bool = False) -> Path:
        candidate = (self.repo_root / relative_path).resolve()
        try:
            candidate.relative_to(self.repo_root)
        except ValueError as exc:
            raise ValueError(f"Path escapes repository root: {relative_path}") from exc
        if any(part in {".git", ".local"} for part in candidate.parts):
            raise ValueError(f"Path is protected: {relative_path}")
        if not allow_missing and not candidate.exists():
            raise FileNotFoundError(candidate)
        return candidate
