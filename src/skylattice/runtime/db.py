"""SQLite runtime database helpers."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from skylattice.storage import LocalPaths


class RuntimeDatabase:
    def __init__(self, repo_root: Path | None = None, db_path: Path | None = None) -> None:
        self.paths = LocalPaths.from_repo_root(repo_root).ensure()
        self.db_path = db_path or (self.paths.state_root / "skylattice.sqlite3")
        self._ensure_schema()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _ensure_schema(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    goal TEXT NOT NULL,
                    goal_source TEXT NOT NULL,
                    status TEXT NOT NULL,
                    plan_summary TEXT,
                    plan_json TEXT,
                    branch_name TEXT,
                    current_step INTEGER NOT NULL DEFAULT 0,
                    error TEXT,
                    runtime_snapshot_json TEXT NOT NULL,
                    result_json TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS run_steps (
                    run_id TEXT NOT NULL,
                    step_index INTEGER NOT NULL,
                    step_id TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    required_tier TEXT NOT NULL,
                    action_name TEXT NOT NULL,
                    action_args_json TEXT NOT NULL,
                    verification_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    result_json TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (run_id, step_index),
                    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS run_approvals (
                    run_id TEXT NOT NULL,
                    tier TEXT NOT NULL,
                    granted INTEGER NOT NULL,
                    actor TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (run_id, tier),
                    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS ledger_events (
                    event_id TEXT PRIMARY KEY,
                    run_id TEXT,
                    kind TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    artifact_refs_json TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    reversible INTEGER NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS memory_records (
                    record_id TEXT PRIMARY KEY,
                    run_id TEXT,
                    layer TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    source_refs_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    status TEXT NOT NULL,
                    supersedes TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
                );
                """
            )
