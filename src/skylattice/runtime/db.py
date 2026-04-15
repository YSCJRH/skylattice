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

                CREATE TABLE IF NOT EXISTS radar_runs (
                    run_id TEXT PRIMARY KEY,
                    window TEXT NOT NULL,
                    status TEXT NOT NULL,
                    run_limit INTEGER NOT NULL,
                    summary TEXT,
                    digest_json TEXT,
                    result_json TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS radar_candidates (
                    candidate_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    repo_slug TEXT NOT NULL,
                    repo_name TEXT NOT NULL,
                    html_url TEXT NOT NULL,
                    description TEXT,
                    source_provider TEXT NOT NULL DEFAULT 'github',
                    source_kind TEXT NOT NULL DEFAULT 'repository',
                    source_handle TEXT NOT NULL DEFAULT '',
                    source_url TEXT NOT NULL DEFAULT '',
                    display_name TEXT NOT NULL DEFAULT '',
                    topics_json TEXT NOT NULL,
                    stars INTEGER NOT NULL,
                    forks INTEGER NOT NULL,
                    watchers INTEGER NOT NULL,
                    created_at_remote TEXT,
                    pushed_at_remote TEXT,
                    latest_release_at TEXT,
                    score REAL NOT NULL DEFAULT 0,
                    score_breakdown_json TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    status TEXT NOT NULL,
                    reason TEXT,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (run_id) REFERENCES radar_runs(run_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS radar_evidence (
                    evidence_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    candidate_id TEXT NOT NULL,
                    provider TEXT NOT NULL DEFAULT 'github',
                    provider_object_type TEXT NOT NULL DEFAULT '',
                    provider_object_id TEXT NOT NULL DEFAULT '',
                    provider_url TEXT,
                    evidence_kind TEXT NOT NULL,
                    source TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (run_id) REFERENCES radar_runs(run_id) ON DELETE CASCADE,
                    FOREIGN KEY (candidate_id) REFERENCES radar_candidates(candidate_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS radar_experiments (
                    experiment_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    candidate_id TEXT NOT NULL,
                    branch_name TEXT NOT NULL,
                    hypothesis TEXT NOT NULL,
                    artifact_path TEXT NOT NULL,
                    validation_command TEXT NOT NULL,
                    status TEXT NOT NULL,
                    recommended INTEGER NOT NULL,
                    source_commit TEXT,
                    experiment_commit TEXT,
                    notes_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (run_id) REFERENCES radar_runs(run_id) ON DELETE CASCADE,
                    FOREIGN KEY (candidate_id) REFERENCES radar_candidates(candidate_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS radar_promotions (
                    promotion_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    candidate_id TEXT NOT NULL,
                    experiment_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    source_branch TEXT NOT NULL,
                    base_commit TEXT NOT NULL,
                    experiment_commit TEXT NOT NULL,
                    main_commit TEXT,
                    rollback_target TEXT,
                    pushed INTEGER NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (run_id) REFERENCES radar_runs(run_id) ON DELETE CASCADE,
                    FOREIGN KEY (candidate_id) REFERENCES radar_candidates(candidate_id) ON DELETE CASCADE,
                    FOREIGN KEY (experiment_id) REFERENCES radar_experiments(experiment_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS radar_state (
                    scope TEXT PRIMARY KEY,
                    freeze_mode INTEGER NOT NULL DEFAULT 0,
                    consecutive_failures INTEGER NOT NULL DEFAULT 0,
                    last_failure_at TEXT,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            self._ensure_column(
                connection,
                table="radar_evidence",
                column="provider",
                definition="TEXT NOT NULL DEFAULT 'github'",
            )
            self._ensure_column(
                connection,
                table="radar_candidates",
                column="source_provider",
                definition="TEXT NOT NULL DEFAULT 'github'",
            )
            self._ensure_column(
                connection,
                table="radar_candidates",
                column="source_kind",
                definition="TEXT NOT NULL DEFAULT 'repository'",
            )
            self._ensure_column(
                connection,
                table="radar_candidates",
                column="source_handle",
                definition="TEXT NOT NULL DEFAULT ''",
            )
            self._ensure_column(
                connection,
                table="radar_candidates",
                column="source_url",
                definition="TEXT NOT NULL DEFAULT ''",
            )
            self._ensure_column(
                connection,
                table="radar_candidates",
                column="display_name",
                definition="TEXT NOT NULL DEFAULT ''",
            )
            self._ensure_column(
                connection,
                table="radar_evidence",
                column="provider_object_type",
                definition="TEXT NOT NULL DEFAULT ''",
            )
            self._ensure_column(
                connection,
                table="radar_evidence",
                column="provider_object_id",
                definition="TEXT NOT NULL DEFAULT ''",
            )
            self._ensure_column(
                connection,
                table="radar_evidence",
                column="provider_url",
                definition="TEXT",
            )

    @staticmethod
    def _ensure_column(
        connection: sqlite3.Connection,
        *,
        table: str,
        column: str,
        definition: str,
    ) -> None:
        rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
        existing = {str(row["name"]) for row in rows}
        if column in existing:
            return
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
