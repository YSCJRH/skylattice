"""Persistent append-only ledger store."""

from __future__ import annotations

import json
import sqlite3
import uuid
from typing import Iterable

from skylattice.runtime.db import RuntimeDatabase

from .models import AuditEvent, EventKind


class LedgerStore:
    def __init__(self, database: RuntimeDatabase) -> None:
        self.database = database

    def append(
        self,
        *,
        run_id: str | None,
        kind: EventKind,
        summary: str,
        actor: str,
        payload: dict[str, object] | None = None,
        artifact_refs: Iterable[str] = (),
        reversible: bool = True,
    ) -> AuditEvent:
        event = AuditEvent(
            event_id=f"evt-{uuid.uuid4().hex}",
            run_id=run_id,
            kind=kind,
            summary=summary,
            actor=actor,
            artifact_refs=tuple(artifact_refs),
            reversible=reversible,
            payload=dict(payload or {}),
        )
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO ledger_events (
                    event_id, run_id, kind, summary, actor, artifact_refs_json,
                    payload_json, reversible, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    event.event_id,
                    event.run_id,
                    event.kind.value,
                    event.summary,
                    event.actor,
                    json.dumps(list(event.artifact_refs)),
                    json.dumps(event.payload),
                    1 if event.reversible else 0,
                ),
            )
        return event

    def list_for_run(self, run_id: str) -> list[AuditEvent]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM ledger_events WHERE run_id = ? ORDER BY created_at ASC, rowid ASC",
                (run_id,),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    @staticmethod
    def _from_row(row: sqlite3.Row) -> AuditEvent:
        return AuditEvent(
            event_id=row["event_id"],
            run_id=row["run_id"],
            kind=EventKind(row["kind"]),
            summary=row["summary"],
            actor=row["actor"],
            artifact_refs=tuple(json.loads(row["artifact_refs_json"] or "[]")),
            reversible=bool(row["reversible"]),
            payload=json.loads(row["payload_json"] or "{}"),
            created_at=row["created_at"],
        )
