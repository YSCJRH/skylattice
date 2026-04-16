"""Repository workspace adapter."""

from __future__ import annotations

import subprocess
from collections.abc import Mapping
from pathlib import Path


class RepoWorkspaceAdapter:
    SAFE_EXTENSIONS = {".md", ".txt", ".py", ".yaml", ".yml", ".json", ".toml"}
    DEFAULT_ALLOWED_CHECK_COMMANDS = (
        "python -m pytest -q",
        "python -m compileall src/skylattice",
        "python -m skylattice.cli doctor",
        "git status --short",
    )
    IGNORE_PARTS = {".git", ".local", "__pycache__", ".pytest_cache", "build", "dist"}

    def __init__(
        self,
        repo_root: Path,
        *,
        allowed_check_commands: tuple[str, ...] | None = None,
        check_shell: str = "powershell",
    ) -> None:
        self.repo_root = repo_root.resolve()
        self.allowed_check_commands = allowed_check_commands or self.DEFAULT_ALLOWED_CHECK_COMMANDS
        self.check_shell = check_shell

    def list_files(self, *, limit: int = 200) -> list[str]:
        files: list[str] = []
        for path in self.repo_root.rglob("*"):
            if len(files) >= limit:
                break
            if not path.is_file():
                continue
            relative_parts = path.relative_to(self.repo_root).parts
            if any(part in self.IGNORE_PARTS for part in relative_parts):
                continue
            if path.suffix == ".pyc" or path.name.endswith(".egg-info"):
                continue
            files.append(path.relative_to(self.repo_root).as_posix())
        return sorted(files)

    def read_text(self, relative_path: str) -> str:
        path = self._resolve(relative_path, allow_missing=True)
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
        if not content.strip():
            raise ValueError(f"Writes that leave {relative_path} empty are not allowed")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return str(path.relative_to(self.repo_root).as_posix())

    def create_file(self, relative_path: str, content: str) -> str:
        path = self._resolve(relative_path, allow_missing=True)
        if path.exists():
            raise ValueError(f"File already exists: {relative_path}")
        return self.write_text(relative_path, content, create_if_missing=True)

    def copy_file(self, source_path: str, destination_path: str) -> str:
        source = self._resolve(source_path)
        if not source.is_file():
            raise FileNotFoundError(source)
        destination = self._resolve(destination_path, allow_missing=True)
        if destination.exists():
            raise ValueError(f"Destination already exists: {destination_path}")
        if source.suffix and source.suffix not in self.SAFE_EXTENSIONS:
            raise ValueError(f"Copies from {source.suffix} files are not allowed in the MVP")
        if destination.suffix and destination.suffix not in self.SAFE_EXTENSIONS:
            raise ValueError(f"Copies to {destination.suffix} files are not allowed in the MVP")
        content = source.read_text(encoding="utf-8")
        return self.write_text(destination_path, content, create_if_missing=True)

    def delete_file(self, relative_path: str) -> str:
        path = self._resolve(relative_path)
        if not path.is_file():
            raise ValueError(f"Path is not a file: {relative_path}")
        if path.suffix and path.suffix not in self.SAFE_EXTENSIONS:
            raise ValueError(f"Deletes for {path.suffix} files are not allowed in the MVP")
        path.unlink()
        return str(path.relative_to(self.repo_root).as_posix())

    def move_file(self, source_path: str, destination_path: str) -> str:
        source = self._resolve(source_path)
        if not source.is_file():
            raise FileNotFoundError(source)
        destination = self._resolve(destination_path, allow_missing=True)
        if destination.exists():
            raise ValueError(f"Destination already exists: {destination_path}")
        if source.suffix and source.suffix not in self.SAFE_EXTENSIONS:
            raise ValueError(f"Moves from {source.suffix} files are not allowed in the MVP")
        if destination.suffix and destination.suffix not in self.SAFE_EXTENSIONS:
            raise ValueError(f"Moves to {destination.suffix} files are not allowed in the MVP")
        destination.parent.mkdir(parents=True, exist_ok=True)
        source.rename(destination)
        return str(destination.relative_to(self.repo_root).as_posix())

    def replace_text(
        self,
        relative_path: str,
        target_text: str,
        replacement_text: str,
        *,
        expected_occurrences: int = 1,
        create_if_missing: bool = False,
    ) -> str:
        content = self.read_text(relative_path)
        if not target_text:
            raise ValueError("replace_text requires a non-empty target_text")
        count = content.count(target_text)
        if count == 0:
            raise ValueError(f"Target text not found in {relative_path}")
        if count != expected_occurrences:
            raise ValueError(
                f"Target text matched {count} times in {relative_path}; expected {expected_occurrences}"
            )
        updated = content.replace(target_text, replacement_text)
        return self.write_text(relative_path, updated, create_if_missing=create_if_missing)

    def insert_after(
        self,
        relative_path: str,
        anchor_text: str,
        insert_text: str,
        *,
        expected_occurrences: int = 1,
        create_if_missing: bool = False,
    ) -> str:
        content = self.read_text(relative_path)
        if not anchor_text:
            raise ValueError("insert_after requires a non-empty anchor_text")
        if not insert_text:
            raise ValueError("insert_after requires non-empty insert_text")
        count = content.count(anchor_text)
        if count == 0:
            raise ValueError(f"Anchor text not found in {relative_path}")
        if count != expected_occurrences:
            raise ValueError(
                f"Anchor text matched {count} times in {relative_path}; expected {expected_occurrences}"
            )
        updated = content.replace(anchor_text, anchor_text + insert_text)
        return self.write_text(relative_path, updated, create_if_missing=create_if_missing)

    def append_text(self, relative_path: str, append_text: str, *, create_if_missing: bool = False) -> str:
        if not append_text:
            raise ValueError("append_text requires non-empty append_text")
        content = self.read_text(relative_path)
        updated = content + append_text
        return self.write_text(relative_path, updated, create_if_missing=create_if_missing)

    def apply_materialized_edit(
        self,
        relative_path: str,
        payload: Mapping[str, object],
        *,
        create_if_missing: bool = False,
    ) -> str:
        mode = str(payload.get("mode", ""))
        if mode == "create_file":
            return self.create_file(
                relative_path,
                str(payload.get("content", "")),
            )
        if mode == "copy_file":
            return self.copy_file(
                str(payload.get("source_path", "")),
                relative_path,
            )
        if mode == "delete_file":
            return self.delete_file(relative_path)
        if mode == "move_file":
            return self.move_file(
                str(payload.get("source_path", "")),
                relative_path,
            )
        if mode == "rewrite":
            return self.write_text(
                relative_path,
                str(payload.get("content", "")),
                create_if_missing=create_if_missing,
            )
        if mode == "replace_text":
            return self.replace_text(
                relative_path,
                str(payload.get("target_text", "")),
                str(payload.get("replacement_text", "")),
                expected_occurrences=int(payload.get("expected_occurrences", 1)),
                create_if_missing=create_if_missing,
            )
        if mode == "insert_after":
            return self.insert_after(
                relative_path,
                str(payload.get("anchor_text", "")),
                str(payload.get("insert_text", "")),
                expected_occurrences=int(payload.get("expected_occurrences", 1)),
                create_if_missing=create_if_missing,
            )
        if mode == "append_text":
            return self.append_text(
                relative_path,
                str(payload.get("append_text", "")),
                create_if_missing=create_if_missing,
            )
        raise ValueError(f"Unsupported materialized edit mode: {mode}")

    def run_check(self, command: str) -> dict[str, object]:
        if command not in self.allowed_check_commands:
            raise ValueError(f"Command not allowed: {command}")
        completed = subprocess.run(
            [self.check_shell, "-Command", command],
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
            relative = candidate.relative_to(self.repo_root)
        except ValueError as exc:
            raise ValueError(f"Path escapes repository root: {relative_path}") from exc
        if any(part in {".git", ".local"} for part in relative.parts):
            raise ValueError(f"Path is protected: {relative_path}")
        if not allow_missing and not candidate.exists():
            raise FileNotFoundError(candidate)
        return candidate
