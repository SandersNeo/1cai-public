# [NEXUS IDENTITY] ID: -35508739372294776 | DATE: 2025-11-19

"""Высокоуровневый логгер событий."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .events import EventRecord, _now_utc
from .storage import SQLiteEventStore


class EventLogger:
    """Инкапсулирует работу с локальным хранилищем событий."""

    def __init__(
        self,
        workspace_id: str,
        *,
        agent_id: str,
        db_path: Optional[Path] = None,
        outbox_dir: Optional[Path] = None,
    ) -> None:
        self.workspace_id = workspace_id
        self.agent_id = agent_id
        self.db_path = Path(db_path or Path("data") / "events.sqlite")
        self.outbox_dir = Path(outbox_dir or Path("outbox"))
        self.outbox_dir.mkdir(parents=True, exist_ok=True)
        self._store = SQLiteEventStore(self.db_path)

    def log(
        self,
        event_type: str,
        summary: str,
        *,
        payload: Optional[Dict[str, object]] = None,
        risks: Optional[Iterable[str]] = None,
        links: Optional[Iterable[str]] = None,
    ) -> EventRecord:
        event = EventRecord(
            event_type=event_type,
            summary=summary,
            agent_id=self.agent_id,
            workspace_id=self.workspace_id,
            payload=dict(payload or {}),
            risks=list(risks or []),
            links=list(links or []),
        )
        self._store.add_event(event)
        return event

    def export_unsynced(self, *, limit: Optional[int] = None) -> Path:
        events = self._store.fetch_unsynced(limit=limit)
        if not events:
            raise RuntimeError("Нет несинхронизированных событий для экспорта")

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = self.outbox_dir / f"events-{timestamp}.json"
        serialized = [event.to_dict() for event in events]
        out_path.write_text(
            json.dumps(
                serialized,
                ensure_ascii=False,
                indent=2),
            encoding="utf-8")

        self._store.mark_synced(
            (event.record_id for event in events), _now_utc())
        return out_path

    def pending_count(self) -> int:
        return self._store.count_pending()

    def unsynced(self, limit: Optional[int] = None) -> List[EventRecord]:
        return self._store.fetch_unsynced(limit=limit)

    def recent(self, limit: int = 20) -> List[EventRecord]:
        return self._store.fetch_recent(limit=limit)

    def import_events(
        self, events: Iterable[EventRecord], *, mark_synced: bool = True
    ) -> int:
        synced_at = _now_utc() if mark_synced else None
        return self._store.import_events(events, synced_at=synced_at)

    def close(self) -> None:
        self._store.close()

    def __enter__(self) -> "EventLogger":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
