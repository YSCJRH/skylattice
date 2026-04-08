"""Local path helpers for the dual-layer runtime layout."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LocalPaths:
    repo_root: Path
    local_root: Path
    state_root: Path
    memory_root: Path
    work_root: Path
    logs_root: Path
    overrides_root: Path

    @classmethod
    def from_repo_root(cls, repo_root: Path | None = None) -> "LocalPaths":
        root = (repo_root or Path(__file__).resolve().parents[3]).resolve()
        local_root = root / ".local"
        return cls(
            repo_root=root,
            local_root=local_root,
            state_root=local_root / "state",
            memory_root=local_root / "memory",
            work_root=local_root / "work",
            logs_root=local_root / "logs",
            overrides_root=local_root / "overrides",
        )

    def ensure(self) -> "LocalPaths":
        for path in (
            self.local_root,
            self.state_root,
            self.memory_root,
            self.work_root,
            self.logs_root,
            self.overrides_root,
        ):
            path.mkdir(parents=True, exist_ok=True)
        return self

    def to_dict(self) -> dict[str, str]:
        return {
            "repo_root": str(self.repo_root),
            "local_root": str(self.local_root),
            "state_root": str(self.state_root),
            "memory_root": str(self.memory_root),
            "work_root": str(self.work_root),
            "logs_root": str(self.logs_root),
            "overrides_root": str(self.overrides_root),
        }
