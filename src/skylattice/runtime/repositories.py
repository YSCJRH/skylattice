"""Repositories for task runs, steps, and approvals."""

from __future__ import annotations

import json
import sqlite3
from typing import Iterable

from skylattice.governance import PermissionTier

from .db import RuntimeDatabase
from .models import ApprovalGrant, RunStatus, RunStep, RunStepStatus, TaskRun


class RunRepository:
    def __init__(self, database: RuntimeDatabase) -> None:
        self.database = database

    def create_run(
        self,
        *,
        run_id: str,
        goal: str,
        goal_source: str,
        runtime_snapshot: dict[str, object],
        status: RunStatus,
    ) -> TaskRun:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO runs (run_id, goal, goal_source, status, runtime_snapshot_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (run_id, goal, goal_source, status.value, json.dumps(runtime_snapshot)),
            )
        return self.get_run(run_id)

    def save_plan(
        self,
        run_id: str,
        *,
        plan_summary: str,
        plan: dict[str, object],
        branch_name: str | None,
        steps: Iterable[RunStep],
    ) -> TaskRun:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE runs
                SET status = ?, plan_summary = ?, plan_json = ?, branch_name = ?, updated_at = CURRENT_TIMESTAMP
                WHERE run_id = ?
                """,
                (RunStatus.PLANNED.value, plan_summary, json.dumps(plan), branch_name, run_id),
            )
            connection.execute("DELETE FROM run_steps WHERE run_id = ?", (run_id,))
            for step in steps:
                connection.execute(
                    """
                    INSERT INTO run_steps (
                        run_id, step_index, step_id, summary, required_tier,
                        action_name, action_args_json, verification_json, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        step.run_id,
                        step.step_index,
                        step.step_id,
                        step.summary,
                        step.required_tier.value,
                        step.action_name,
                        json.dumps(step.action_args),
                        json.dumps(step.verification),
                        step.status.value,
                    ),
                )
        return self.get_run(run_id)

    def update_status(self, run_id: str, status: RunStatus, *, error: str | None = None) -> TaskRun:
        with self.database.connect() as connection:
            connection.execute(
                "UPDATE runs SET status = ?, error = ?, updated_at = CURRENT_TIMESTAMP WHERE run_id = ?",
                (status.value, error, run_id),
            )
        return self.get_run(run_id)

    def set_result(self, run_id: str, result: dict[str, object]) -> TaskRun:
        with self.database.connect() as connection:
            connection.execute(
                "UPDATE runs SET result_json = ?, updated_at = CURRENT_TIMESTAMP WHERE run_id = ?",
                (json.dumps(result), run_id),
            )
        return self.get_run(run_id)

    def set_current_step(self, run_id: str, step_index: int) -> None:
        with self.database.connect() as connection:
            connection.execute(
                "UPDATE runs SET current_step = ?, updated_at = CURRENT_TIMESTAMP WHERE run_id = ?",
                (step_index, run_id),
            )

    def grant_approvals(self, run_id: str, approvals: Iterable[ApprovalGrant]) -> TaskRun:
        with self.database.connect() as connection:
            for grant in approvals:
                connection.execute(
                    """
                    INSERT INTO run_approvals (run_id, tier, granted, actor)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(run_id, tier) DO UPDATE SET granted = excluded.granted, actor = excluded.actor
                    """,
                    (run_id, grant.tier.value, 1 if grant.granted else 0, grant.actor),
                )
        return self.get_run(run_id)

    def update_step(self, step: RunStep) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE run_steps
                SET status = ?, result_json = ?, updated_at = CURRENT_TIMESTAMP
                WHERE run_id = ? AND step_index = ?
                """,
                (step.status.value, json.dumps(step.result), step.run_id, step.step_index),
            )

    def get_run(self, run_id: str) -> TaskRun:
        with self.database.connect() as connection:
            row = connection.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
            if row is None:
                raise KeyError(f"Unknown run_id: {run_id}")
            approvals = connection.execute(
                "SELECT * FROM run_approvals WHERE run_id = ? ORDER BY tier ASC",
                (run_id,),
            ).fetchall()
        return self._run_from_row(row, approvals)

    def list_steps(self, run_id: str) -> list[RunStep]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM run_steps WHERE run_id = ? ORDER BY step_index ASC",
                (run_id,),
            ).fetchall()
        return [self._step_from_row(row) for row in rows]

    def _run_from_row(self, row: sqlite3.Row, approvals: list[sqlite3.Row]) -> TaskRun:
        return TaskRun(
            run_id=row["run_id"],
            goal=row["goal"],
            goal_source=row["goal_source"],
            status=RunStatus(row["status"]),
            runtime_snapshot=json.loads(row["runtime_snapshot_json"] or "{}"),
            plan_summary=row["plan_summary"] or "",
            plan=json.loads(row["plan_json"] or "{}"),
            branch_name=row["branch_name"],
            current_step=int(row["current_step"]),
            approvals=tuple(
                ApprovalGrant(
                    tier=PermissionTier(item["tier"]),
                    granted=bool(item["granted"]),
                    actor=item["actor"],
                    created_at=item["created_at"],
                )
                for item in approvals
            ),
            error=row["error"],
            result=json.loads(row["result_json"] or "{}"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _step_from_row(row: sqlite3.Row) -> RunStep:
        return RunStep(
            run_id=row["run_id"],
            step_index=int(row["step_index"]),
            step_id=row["step_id"],
            summary=row["summary"],
            required_tier=PermissionTier(row["required_tier"]),
            action_name=row["action_name"],
            action_args=json.loads(row["action_args_json"] or "{}"),
            verification=json.loads(row["verification_json"] or "{}"),
            status=RunStepStatus(row["status"]),
            result=json.loads(row["result_json"] or "{}"),
        )
