"""SQLite-backed memory repository."""

from __future__ import annotations

import json
import sqlite3
import uuid
from typing import Iterable

from skylattice.runtime.db import RuntimeDatabase

from .interfaces import MemoryIndex, MemoryLayer, MemoryRecord, MemoryStore, RecordStatus, RetrievalRequest


class SQLiteMemoryRepository(MemoryStore, MemoryIndex):
    def __init__(self, database: RuntimeDatabase) -> None:
        self.database = database

    def write(self, record: MemoryRecord) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO memory_records (
                    record_id, run_id, layer, summary, source_refs_json, metadata_json,
                    confidence, status, supersedes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (
                    record.record_id,
                    record.run_id,
                    record.layer.value,
                    record.summary,
                    json.dumps(list(record.source_refs)),
                    json.dumps(record.metadata),
                    record.confidence,
                    record.status.value,
                    record.supersedes,
                ),
            )
            if record.supersedes:
                connection.execute(
                    "UPDATE memory_records SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE record_id = ?",
                    (RecordStatus.SUPERSEDED.value, record.supersedes),
                )

    def create(
        self,
        *,
        layer: MemoryLayer,
        summary: str,
        run_id: str | None = None,
        source_refs: Iterable[str] = (),
        metadata: dict[str, object] | None = None,
        confidence: float = 1.0,
        supersedes: str | None = None,
    ) -> MemoryRecord:
        record = MemoryRecord(
            record_id=f"mem-{uuid.uuid4().hex}",
            layer=layer,
            summary=summary,
            source_refs=tuple(source_refs),
            confidence=confidence,
            status=RecordStatus.ACTIVE,
            metadata=dict(metadata or {}),
            run_id=run_id,
            supersedes=supersedes,
        )
        self.write(record)
        return record

    def rollback(self, record_id: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                "UPDATE memory_records SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE record_id = ?",
                (RecordStatus.TOMBSTONED.value, record_id),
            )

    def retrieve(self, request: RetrievalRequest) -> list[MemoryRecord]:
        clauses = ["layer IN (%s)" % ",".join("?" for _ in request.layers)]
        params: list[object] = [layer.value for layer in request.layers]
        if request.query:
            clauses.append("summary LIKE ?")
            params.append(f"%{request.query}%")
        if not request.include_stale:
            clauses.append("status = ?")
            params.append(RecordStatus.ACTIVE.value)
        params.append(request.limit)

        query = (
            "SELECT * FROM memory_records WHERE "
            + " AND ".join(clauses)
            + " ORDER BY created_at DESC LIMIT ?"
        )
        with self.database.connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._from_row(row) for row in rows]

    def list_for_run(self, run_id: str) -> list[MemoryRecord]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM memory_records WHERE run_id = ? ORDER BY created_at ASC",
                (run_id,),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    @staticmethod
    def _from_row(row: sqlite3.Row) -> MemoryRecord:
        return MemoryRecord(
            record_id=row["record_id"],
            layer=MemoryLayer(row["layer"]),
            summary=row["summary"],
            source_refs=tuple(json.loads(row["source_refs_json"] or "[]")),
            confidence=float(row["confidence"]),
            status=RecordStatus(row["status"]),
            metadata=json.loads(row["metadata_json"] or "{}"),
            run_id=row["run_id"],
            supersedes=row["supersedes"],
        )
