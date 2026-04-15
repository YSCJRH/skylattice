"""SQLite-backed memory repository."""

from __future__ import annotations

import json
import re
import sqlite3
import uuid
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

from .interfaces import MemoryIndex, MemoryLayer, MemoryRecord, MemoryStore, RecordStatus, RetrievalRequest, RetrievalSort

if TYPE_CHECKING:
    from ..runtime.db import RuntimeDatabase

_UNSET = object()
_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+")


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
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP), CURRENT_TIMESTAMP)
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
                    record.created_at,
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
        status: RecordStatus = RecordStatus.ACTIVE,
    ) -> MemoryRecord:
        record = MemoryRecord(
            record_id=f"mem-{uuid.uuid4().hex}",
            layer=layer,
            summary=summary,
            source_refs=tuple(source_refs),
            confidence=confidence,
            status=status,
            metadata=dict(metadata or {}),
            run_id=run_id,
            supersedes=supersedes,
        )
        self.write(record)
        return self.get_record(record.record_id)

    def get_record(self, record_id: str) -> MemoryRecord:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM memory_records WHERE record_id = ?",
                (record_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"Unknown memory record: {record_id}")
        return self._from_row(row)

    def list_records(
        self,
        *,
        layers: Iterable[MemoryLayer] | None = None,
        statuses: Iterable[RecordStatus] | None = None,
        run_id: str | None = None,
        limit: int | None = None,
    ) -> list[MemoryRecord]:
        clauses: list[str] = []
        params: list[object] = []

        normalized_layers = tuple(layers or ())
        if normalized_layers:
            clauses.append("layer IN (%s)" % ",".join("?" for _ in normalized_layers))
            params.extend(layer.value for layer in normalized_layers)

        normalized_statuses = tuple(statuses or ())
        if normalized_statuses:
            clauses.append("status IN (%s)" % ",".join("?" for _ in normalized_statuses))
            params.extend(status.value for status in normalized_statuses)

        if run_id is not None:
            clauses.append("run_id = ?")
            params.append(run_id)

        query = "SELECT * FROM memory_records"
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC, record_id DESC"
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)

        with self.database.connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._from_row(row) for row in rows]

    def update_record(
        self,
        record_id: str,
        *,
        summary: str | object = _UNSET,
        source_refs: Iterable[str] | object = _UNSET,
        metadata: dict[str, object] | object = _UNSET,
        confidence: float | object = _UNSET,
        status: RecordStatus | object = _UNSET,
        supersedes: str | None | object = _UNSET,
        run_id: str | None | object = _UNSET,
    ) -> MemoryRecord:
        current = self.get_record(record_id)
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE memory_records
                SET summary = ?, source_refs_json = ?, metadata_json = ?, confidence = ?, status = ?, supersedes = ?, run_id = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE record_id = ?
                """,
                (
                    current.summary if summary is _UNSET else str(summary),
                    json.dumps(list(current.source_refs if source_refs is _UNSET else source_refs)),
                    json.dumps(current.metadata if metadata is _UNSET else dict(metadata)),
                    current.confidence if confidence is _UNSET else float(confidence),
                    current.status.value if status is _UNSET else status.value,
                    current.supersedes if supersedes is _UNSET else supersedes,
                    current.run_id if run_id is _UNSET else run_id,
                    record_id,
                ),
            )
        return self.get_record(record_id)

    def rollback(self, record_id: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                "UPDATE memory_records SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE record_id = ?",
                (RecordStatus.TOMBSTONED.value, record_id),
            )

    def retrieve(self, request: RetrievalRequest) -> list[MemoryRecord]:
        if not request.layers:
            return []
        statuses = request.statuses
        if not statuses and not request.include_stale:
            statuses = (RecordStatus.ACTIVE,)
        records = self.list_records(layers=request.layers, statuses=statuses or None)
        filtered = [record for record in records if self._matches_metadata_filters(record, request.metadata_filters)]
        ranked = self._rank_records(filtered, request)
        return ranked[: request.limit]

    def list_for_run(self, run_id: str) -> list[MemoryRecord]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM memory_records WHERE run_id = ? ORDER BY created_at ASC, record_id ASC",
                (run_id,),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    @staticmethod
    def _matches_metadata_filters(record: MemoryRecord, filters: tuple[tuple[str, str], ...]) -> bool:
        if not filters:
            return True
        for key, expected in filters:
            candidate = record.metadata.get(key)
            if isinstance(candidate, (list, tuple, set)):
                values = {str(item).strip().lower() for item in candidate}
                if expected.strip().lower() not in values:
                    return False
                continue
            if str(candidate).strip().lower() != expected.strip().lower():
                return False
        return True

    @classmethod
    def _rank_records(cls, records: list[MemoryRecord], request: RetrievalRequest) -> list[MemoryRecord]:
        if request.sort_by is RetrievalSort.RECENT:
            return sorted(records, key=lambda item: ((item.created_at or ""), item.record_id), reverse=True)

        query_lower = request.query.strip().lower()
        query_tokens = cls._tokenize(query_lower)
        recency_order = {
            record.record_id: max(0.0, 1.0 - (index / max(len(records), 1)))
            for index, record in enumerate(records)
        }

        def sort_key(record: MemoryRecord) -> tuple[float, int, str, str]:
            summary_lower = record.summary.lower()
            summary_tokens = cls._tokenize(summary_lower)
            metadata_tokens = cls._metadata_tokens(record.metadata)
            exact_summary = 1.0 if query_lower and query_lower in summary_lower else 0.0
            summary_overlap = cls._overlap_ratio(query_tokens, summary_tokens)
            metadata_overlap = cls._overlap_ratio(query_tokens, metadata_tokens)
            status_weight = {
                RecordStatus.ACTIVE: 2.0,
                RecordStatus.CONSTRAINED: 1.0,
                RecordStatus.SUPERSEDED: 0.2,
                RecordStatus.TOMBSTONED: 0.0,
            }[record.status]
            recency_bonus = recency_order.get(record.record_id, 0.0) * 0.25
            score = (exact_summary * 100.0) + (summary_overlap * 24.0) + (metadata_overlap * 8.0) + status_weight + recency_bonus
            return (score, 1 if record.status is RecordStatus.ACTIVE else 0, record.created_at or "", record.record_id)

        return sorted(records, key=sort_key, reverse=True)

    @staticmethod
    def _overlap_ratio(query_tokens: set[str], target_tokens: set[str]) -> float:
        if not query_tokens or not target_tokens:
            return 0.0
        return len(query_tokens & target_tokens) / len(query_tokens)

    @staticmethod
    def _tokenize(value: str) -> set[str]:
        return {token.lower() for token in _TOKEN_PATTERN.findall(value)}

    @classmethod
    def _metadata_tokens(cls, metadata: dict[str, Any]) -> set[str]:
        tokens: set[str] = set()
        for value in metadata.values():
            if isinstance(value, dict):
                for nested in value.values():
                    tokens.update(cls._tokenize(str(nested)))
            elif isinstance(value, (list, tuple, set)):
                for item in value:
                    tokens.update(cls._tokenize(str(item)))
            else:
                tokens.update(cls._tokenize(str(value)))
        return tokens

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
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
