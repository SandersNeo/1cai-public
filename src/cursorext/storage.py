# [NEXUS IDENTITY] ID: -4219370191420720158 | DATE: 2025-11-19

"""Хранилище событий на базе SQLite."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable, List, Optional

from .events import EventRecord


class SQLiteEventStore:
    """Простое хранилище событий для прототипа."""

    _ALLOWED_JOURNAL_MODES = {"DELETE", "TRUNCATE", "PERSIST", "MEMORY", "WAL", "OFF"}

    def __init__(self, db_path: Path, *, journal_mode: str = "WAL") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.db_path, isolation_level=None)
        self._connection.row_factory = sqlite3.Row
        self._initialize(journal_mode)

    def _initialize(self, journal_mode: str) -> None:
        normalized_mode = (journal_mode or "WAL").strip().upper()
        if normalized_mode not in self._ALLOWED_JOURNAL_MODES:
            normalized_mode = "WAL"

        with self._connection:
            self._connection.execute("PRAGMA foreign_keys = ON;")
            self._connection.execute("PRAGMA journal_mode = ?", (normalized_mode,))
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    record_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    workspace_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    risks TEXT NOT NULL,
                    links TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    synced_at TEXT
                );
                """
            )

    def add_event(self, event: EventRecord, *, synced_at: Optional[str] = None) -> None:
        with self._connection:
            self._connection.execute(
                """
                INSERT OR REPLACE INTO events (
                    record_id, event_type, summary, agent_id, workspace_id,
                    payload, risks, links, created_at, synced_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE(
                    ?, (SELECT synced_at FROM events WHERE record_id = ?), NULL
                ));
                """,
                (
                    event.record_id,
                    event.event_type,
                    event.summary,
                    event.agent_id,
                    event.workspace_id,
                    json.dumps(event.payload, ensure_ascii=False),
                    json.dumps(event.risks, ensure_ascii=False),
                    json.dumps(event.links, ensure_ascii=False),
                    event.created_at,
                    synced_at,
                    event.record_id,
                ),
            )

    def fetch_unsynced(self, limit: Optional[int] = None) -> List[EventRecord]:
        query = "SELECT * FROM events WHERE synced_at IS NULL ORDER BY created_at ASC"
        if limit:
            query += " LIMIT ?"
            rows = self._connection.execute(query, (limit,))
        else:
            rows = self._connection.execute(query)
        return [EventRecord.from_row(dict(row)) for row in rows.fetchall()]

    def fetch_recent(self, limit: int = 50) -> List[EventRecord]:
        rows = self._connection.execute(
            "SELECT * FROM events ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        return [EventRecord.from_row(dict(row)) for row in rows.fetchall()]

    def mark_synced(self, record_ids: Iterable[str], synced_at: str) -> None:
        record_ids = list(record_ids)
        if not record_ids:
            return
        placeholders = ",".join("?" for _ in record_ids)
        query = "UPDATE events SET synced_at = ? WHERE record_id IN ({})".format(
            placeholders
        )
        with self._connection:
            self._connection.execute(
                query,
                (synced_at, *record_ids),
            )

    def count_pending(self) -> int:
        cursor = self._connection.execute(
            "SELECT COUNT(*) FROM events WHERE synced_at IS NULL"
        )
        (count,) = cursor.fetchone()
        return int(count)

    def import_events(
        self, events: Iterable[EventRecord], *, synced_at: Optional[str] = None
    ) -> int:
        records = list(events)
        for event in records:
            self.add_event(event, synced_at=synced_at)
        return len(records)

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "SQLiteEventStore":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
