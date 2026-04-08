"""SQLite repositories for technology radar state."""

from __future__ import annotations

import json
import sqlite3
from typing import Iterable

from .models import (
    RadarCandidate,
    RadarCandidateStatus,
    RadarDecision,
    RadarEvidence,
    RadarExperiment,
    RadarExperimentStatus,
    RadarPromotion,
    RadarPromotionStatus,
    RadarRun,
    RadarRunStatus,
    RadarState,
    RadarWindow,
)
from skylattice.runtime.db import RuntimeDatabase


class RadarRepository:
    def __init__(self, database: RuntimeDatabase) -> None:
        self.database = database
        self._ensure_state()

    def _ensure_state(self) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO radar_state (scope, freeze_mode, consecutive_failures)
                VALUES ('default', 0, 0)
                """
            )

    def create_run(self, run: RadarRun) -> RadarRun:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO radar_runs (run_id, window, status, run_limit, summary, digest_json, result_json, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.run_id,
                    run.window.value,
                    run.status.value,
                    run.limit,
                    run.summary,
                    json.dumps(run.digest),
                    json.dumps(run.result),
                    run.error,
                ),
            )
        return self.get_run(run.run_id)

    def update_run(
        self,
        run_id: str,
        *,
        status: RadarRunStatus | None = None,
        summary: str | None = None,
        digest: dict[str, object] | None = None,
        result: dict[str, object] | None = None,
        error: str | None = None,
    ) -> RadarRun:
        assignments: list[str] = ["updated_at = CURRENT_TIMESTAMP"]
        params: list[object] = []
        if status is not None:
            assignments.append("status = ?")
            params.append(status.value)
        if summary is not None:
            assignments.append("summary = ?")
            params.append(summary)
        if digest is not None:
            assignments.append("digest_json = ?")
            params.append(json.dumps(digest))
        if result is not None:
            assignments.append("result_json = ?")
            params.append(json.dumps(result))
        if error is not None:
            assignments.append("error = ?")
            params.append(error)
        params.append(run_id)
        with self.database.connect() as connection:
            connection.execute(
                f"UPDATE radar_runs SET {', '.join(assignments)} WHERE run_id = ?",
                params,
            )
        return self.get_run(run_id)

    def get_run(self, run_id: str) -> RadarRun:
        with self.database.connect() as connection:
            row = connection.execute("SELECT * FROM radar_runs WHERE run_id = ?", (run_id,)).fetchone()
        if row is None:
            raise KeyError(f"Unknown radar run: {run_id}")
        return self._run_from_row(row)

    def latest_run(self) -> RadarRun | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM radar_runs ORDER BY created_at DESC, rowid DESC LIMIT 1"
            ).fetchone()
        return self._run_from_row(row) if row is not None else None

    def latest_digest(self) -> dict[str, object]:
        run = self.latest_run()
        return run.digest if run is not None else {}

    def create_candidates(self, candidates: Iterable[RadarCandidate]) -> None:
        with self.database.connect() as connection:
            for candidate in candidates:
                connection.execute(
                    """
                    INSERT INTO radar_candidates (
                        candidate_id, run_id, repo_slug, repo_name, html_url, description,
                        topics_json, stars, forks, watchers, created_at_remote, pushed_at_remote,
                        latest_release_at, score, score_breakdown_json, decision, status, reason,
                        metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        candidate.candidate_id,
                        candidate.run_id,
                        candidate.repo_slug,
                        candidate.repo_name,
                        candidate.html_url,
                        candidate.description,
                        json.dumps(list(candidate.topics)),
                        candidate.stars,
                        candidate.forks,
                        candidate.watchers,
                        candidate.created_at_remote,
                        candidate.pushed_at_remote,
                        candidate.latest_release_at,
                        candidate.score,
                        json.dumps(candidate.score_breakdown),
                        candidate.decision.value,
                        candidate.status.value,
                        candidate.reason,
                        json.dumps(candidate.metadata),
                    ),
                )

    def update_candidate(self, candidate: RadarCandidate) -> RadarCandidate:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE radar_candidates
                SET description = ?, topics_json = ?, stars = ?, forks = ?, watchers = ?,
                    created_at_remote = ?, pushed_at_remote = ?, latest_release_at = ?,
                    score = ?, score_breakdown_json = ?, decision = ?, status = ?, reason = ?,
                    metadata_json = ?, updated_at = CURRENT_TIMESTAMP
                WHERE candidate_id = ?
                """,
                (
                    candidate.description,
                    json.dumps(list(candidate.topics)),
                    candidate.stars,
                    candidate.forks,
                    candidate.watchers,
                    candidate.created_at_remote,
                    candidate.pushed_at_remote,
                    candidate.latest_release_at,
                    candidate.score,
                    json.dumps(candidate.score_breakdown),
                    candidate.decision.value,
                    candidate.status.value,
                    candidate.reason,
                    json.dumps(candidate.metadata),
                    candidate.candidate_id,
                ),
            )
        return self.get_candidate(candidate.candidate_id)

    def get_candidate(self, candidate_id: str) -> RadarCandidate:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM radar_candidates WHERE candidate_id = ?",
                (candidate_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"Unknown radar candidate: {candidate_id}")
        return self._candidate_from_row(row)

    def list_candidates(self, run_id: str) -> list[RadarCandidate]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM radar_candidates WHERE run_id = ? ORDER BY score DESC, created_at ASC",
                (run_id,),
            ).fetchall()
        return [self._candidate_from_row(row) for row in rows]

    def add_evidence(self, evidence: Iterable[RadarEvidence]) -> None:
        with self.database.connect() as connection:
            for item in evidence:
                connection.execute(
                    """
                    INSERT INTO radar_evidence (evidence_id, run_id, candidate_id, evidence_kind, source, summary, payload_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item.evidence_id,
                        item.run_id,
                        item.candidate_id,
                        item.evidence_kind,
                        item.source,
                        item.summary,
                        json.dumps(item.payload),
                    ),
                )

    def list_evidence(self, run_id: str | None = None, candidate_id: str | None = None) -> list[RadarEvidence]:
        clauses: list[str] = []
        params: list[object] = []
        if run_id is not None:
            clauses.append("run_id = ?")
            params.append(run_id)
        if candidate_id is not None:
            clauses.append("candidate_id = ?")
            params.append(candidate_id)
        sql = "SELECT * FROM radar_evidence"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY created_at ASC, rowid ASC"
        with self.database.connect() as connection:
            rows = connection.execute(sql, params).fetchall()
        return [self._evidence_from_row(row) for row in rows]

    def create_experiment(self, experiment: RadarExperiment) -> RadarExperiment:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO radar_experiments (
                    experiment_id, run_id, candidate_id, branch_name, hypothesis, artifact_path,
                    validation_command, status, recommended, source_commit, experiment_commit, notes_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    experiment.experiment_id,
                    experiment.run_id,
                    experiment.candidate_id,
                    experiment.branch_name,
                    experiment.hypothesis,
                    experiment.artifact_path,
                    experiment.validation_command,
                    experiment.status.value,
                    1 if experiment.recommended else 0,
                    experiment.source_commit,
                    experiment.experiment_commit,
                    json.dumps(experiment.notes),
                ),
            )
        return self.get_experiment(experiment.experiment_id)

    def update_experiment(self, experiment: RadarExperiment) -> RadarExperiment:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE radar_experiments
                SET branch_name = ?, hypothesis = ?, artifact_path = ?, validation_command = ?,
                    status = ?, recommended = ?, source_commit = ?, experiment_commit = ?,
                    notes_json = ?, updated_at = CURRENT_TIMESTAMP
                WHERE experiment_id = ?
                """,
                (
                    experiment.branch_name,
                    experiment.hypothesis,
                    experiment.artifact_path,
                    experiment.validation_command,
                    experiment.status.value,
                    1 if experiment.recommended else 0,
                    experiment.source_commit,
                    experiment.experiment_commit,
                    json.dumps(experiment.notes),
                    experiment.experiment_id,
                ),
            )
        return self.get_experiment(experiment.experiment_id)

    def get_experiment(self, experiment_id: str) -> RadarExperiment:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM radar_experiments WHERE experiment_id = ?",
                (experiment_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"Unknown radar experiment: {experiment_id}")
        return self._experiment_from_row(row)

    def list_experiments(self, run_id: str) -> list[RadarExperiment]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM radar_experiments WHERE run_id = ? ORDER BY created_at ASC, rowid ASC",
                (run_id,),
            ).fetchall()
        return [self._experiment_from_row(row) for row in rows]

    def create_promotion(self, promotion: RadarPromotion) -> RadarPromotion:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO radar_promotions (
                    promotion_id, run_id, candidate_id, experiment_id, status, source_branch,
                    base_commit, experiment_commit, main_commit, rollback_target, pushed, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    promotion.promotion_id,
                    promotion.run_id,
                    promotion.candidate_id,
                    promotion.experiment_id,
                    promotion.status.value,
                    promotion.source_branch,
                    promotion.base_commit,
                    promotion.experiment_commit,
                    promotion.main_commit,
                    promotion.rollback_target,
                    1 if promotion.pushed else 0,
                    json.dumps(promotion.metadata),
                ),
            )
        return self.get_promotion(promotion.promotion_id)

    def update_promotion(self, promotion: RadarPromotion) -> RadarPromotion:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE radar_promotions
                SET status = ?, source_branch = ?, base_commit = ?, experiment_commit = ?,
                    main_commit = ?, rollback_target = ?, pushed = ?, metadata_json = ?, updated_at = CURRENT_TIMESTAMP
                WHERE promotion_id = ?
                """,
                (
                    promotion.status.value,
                    promotion.source_branch,
                    promotion.base_commit,
                    promotion.experiment_commit,
                    promotion.main_commit,
                    promotion.rollback_target,
                    1 if promotion.pushed else 0,
                    json.dumps(promotion.metadata),
                    promotion.promotion_id,
                ),
            )
        return self.get_promotion(promotion.promotion_id)

    def get_promotion(self, promotion_id: str) -> RadarPromotion:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM radar_promotions WHERE promotion_id = ?",
                (promotion_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"Unknown radar promotion: {promotion_id}")
        return self._promotion_from_row(row)

    def list_promotions(self, run_id: str | None = None) -> list[RadarPromotion]:
        sql = "SELECT * FROM radar_promotions"
        params: list[object] = []
        if run_id is not None:
            sql += " WHERE run_id = ?"
            params.append(run_id)
        sql += " ORDER BY created_at ASC, rowid ASC"
        with self.database.connect() as connection:
            rows = connection.execute(sql, params).fetchall()
        return [self._promotion_from_row(row) for row in rows]

    def count_promotions_since(self, cutoff: str) -> int:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS count FROM radar_promotions WHERE status = ? AND created_at >= ?",
                (RadarPromotionStatus.PROMOTED.value, cutoff),
            ).fetchone()
        return int(row["count"] if row is not None else 0)

    def get_state(self) -> RadarState:
        with self.database.connect() as connection:
            row = connection.execute("SELECT * FROM radar_state WHERE scope = 'default'").fetchone()
        if row is None:
            return RadarState()
        return RadarState(
            freeze_mode=bool(row["freeze_mode"]),
            consecutive_failures=int(row["consecutive_failures"]),
            last_failure_at=row["last_failure_at"],
        )

    def set_state(
        self,
        *,
        freeze_mode: bool | None = None,
        consecutive_failures: int | None = None,
        last_failure_at: str | None = None,
    ) -> RadarState:
        assignments: list[str] = ["updated_at = CURRENT_TIMESTAMP"]
        params: list[object] = []
        if freeze_mode is not None:
            assignments.append("freeze_mode = ?")
            params.append(1 if freeze_mode else 0)
        if consecutive_failures is not None:
            assignments.append("consecutive_failures = ?")
            params.append(consecutive_failures)
        if last_failure_at is not None:
            assignments.append("last_failure_at = ?")
            params.append(last_failure_at)
        params.append("default")
        with self.database.connect() as connection:
            connection.execute(
                f"UPDATE radar_state SET {', '.join(assignments)} WHERE scope = ?",
                params,
            )
        return self.get_state()

    @staticmethod
    def _run_from_row(row: sqlite3.Row) -> RadarRun:
        return RadarRun(
            run_id=row["run_id"],
            window=RadarWindow(row["window"]),
            status=RadarRunStatus(row["status"]),
            limit=int(row["run_limit"]),
            summary=row["summary"] or "",
            digest=json.loads(row["digest_json"] or "{}"),
            result=json.loads(row["result_json"] or "{}"),
            error=row["error"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _candidate_from_row(row: sqlite3.Row) -> RadarCandidate:
        return RadarCandidate(
            candidate_id=row["candidate_id"],
            run_id=row["run_id"],
            repo_slug=row["repo_slug"],
            repo_name=row["repo_name"],
            html_url=row["html_url"],
            description=row["description"] or "",
            topics=tuple(json.loads(row["topics_json"] or "[]")),
            stars=int(row["stars"]),
            forks=int(row["forks"]),
            watchers=int(row["watchers"]),
            created_at_remote=row["created_at_remote"],
            pushed_at_remote=row["pushed_at_remote"],
            latest_release_at=row["latest_release_at"],
            score=float(row["score"]),
            score_breakdown={str(key): float(value) for key, value in json.loads(row["score_breakdown_json"] or "{}").items()},
            decision=RadarDecision(row["decision"]),
            status=RadarCandidateStatus(row["status"]),
            reason=row["reason"] or "",
            metadata=json.loads(row["metadata_json"] or "{}"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _evidence_from_row(row: sqlite3.Row) -> RadarEvidence:
        return RadarEvidence(
            evidence_id=row["evidence_id"],
            run_id=row["run_id"],
            candidate_id=row["candidate_id"],
            evidence_kind=row["evidence_kind"],
            source=row["source"],
            summary=row["summary"],
            payload=json.loads(row["payload_json"] or "{}"),
            created_at=row["created_at"],
        )

    @staticmethod
    def _experiment_from_row(row: sqlite3.Row) -> RadarExperiment:
        return RadarExperiment(
            experiment_id=row["experiment_id"],
            run_id=row["run_id"],
            candidate_id=row["candidate_id"],
            branch_name=row["branch_name"],
            hypothesis=row["hypothesis"],
            artifact_path=row["artifact_path"],
            validation_command=row["validation_command"],
            status=RadarExperimentStatus(row["status"]),
            recommended=bool(row["recommended"]),
            source_commit=row["source_commit"],
            experiment_commit=row["experiment_commit"],
            notes=json.loads(row["notes_json"] or "{}"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _promotion_from_row(row: sqlite3.Row) -> RadarPromotion:
        return RadarPromotion(
            promotion_id=row["promotion_id"],
            run_id=row["run_id"],
            candidate_id=row["candidate_id"],
            experiment_id=row["experiment_id"],
            status=RadarPromotionStatus(row["status"]),
            source_branch=row["source_branch"],
            base_commit=row["base_commit"],
            experiment_commit=row["experiment_commit"],
            main_commit=row["main_commit"],
            rollback_target=row["rollback_target"],
            pushed=bool(row["pushed"]),
            metadata=json.loads(row["metadata_json"] or "{}"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )



