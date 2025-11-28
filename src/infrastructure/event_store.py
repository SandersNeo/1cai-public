# [NEXUS IDENTITY] ID: 2596506657378241299 | DATE: 2025-11-19

"""
Event Store - Event Sourcing для системы
=========================================

Хранилище событий для:
- Event Sourcing паттерна
- Аудит логов
- Восстановление состояния
- Временные запросы

Научное обоснование:
- "Event Sourcing" (Martin Fowler, 2005): Полная история изменений
- "CQRS" (Greg Young, 2010): Разделение чтения и записи
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional

from .event_bus import Event, EventType

logger = logging.getLogger(__name__)


class EventStream:
    """Поток событий"""

    def __init__(self, stream_id: str, events: List[Event], version: int = 0):
        self.stream_id = stream_id
        self.events = events
        self.version = version

    def append(self, event: Event) -> None:
        """Добавление события в поток"""
        self.events.append(event)
        self.version += 1

    def get_events(self, from_version: int = 0, to_version: Optional[int] = None) -> List[Event]:
        """Получение событий из потока"""
        start = from_version
        end = to_version if to_version is not None else len(self.events)
        return self.events[start:end]


class EventStore(ABC):
    """Абстрактное хранилище событий"""

    @abstractmethod
    async def append(self, stream_id: str, event: Event) -> None:
        """Добавление события в поток"""

    @abstractmethod
    async def get_stream(self, stream_id: str, from_version: int = 0, to_version: Optional[int] = None) -> EventStream:
        """Получение потока событий"""

    @abstractmethod
    async def get_events(
        self,
        event_type: Optional[EventType] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Event]:
        """Получение событий по фильтрам"""


class InMemoryEventStore(EventStore):
    """
    In-Memory реализация Event Store

    Для production использовать PostgreSQL или специализированные решения
    """

    def __init__(self):
        self._streams: Dict[str, EventStream] = {}
        self._all_events: List[Event] = []
        logger.info("InMemoryEventStore initialized")

    async def append(self, stream_id: str, event: Event) -> None:
        """Добавление события в поток"""
        if stream_id not in self._streams:
            self._streams[stream_id] = EventStream(stream_id, [])

        stream = self._streams[stream_id]
        stream.append(event)
        self._all_events.append(event)

        logger.debug(
            f"Event appended to stream {stream_id}",
            extra={
                "stream_id": stream_id,
                "event_id": event.id,
                "event_type": event.type.value,
                "version": stream.version,
            },
        )

    async def get_stream(self, stream_id: str, from_version: int = 0, to_version: Optional[int] = None) -> EventStream:
        """Получение потока событий"""
        if stream_id not in self._streams:
            return EventStream(stream_id, [])

        stream = self._streams[stream_id]
        events = stream.get_events(from_version, to_version)

        return EventStream(stream_id, events, stream.version)

    async def get_events(
        self,
        event_type: Optional[EventType] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Event]:
        """Получение событий по фильтрам"""
        events = self._all_events

        # Фильтр по типу
        if event_type:
            events = [e for e in events if e.type == event_type]

        # Фильтр по дате
        if from_date:
            events = [e for e in events if e.timestamp >= from_date]

        if to_date:
            events = [e for e in events if e.timestamp <= to_date]

        # Сортировка по времени (новые первыми)
        events.sort(key=lambda e: e.timestamp, reverse=True)

        # Ограничение
        return events[:limit]


class PostgreSQLEventStore(EventStore):
    """
    PostgreSQL реализация Event Store

    Использует PostgreSQL для персистентного хранения событий
    """

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.conn = None
        self._initialize_connection()
        self._create_tables()
        logger.info("PostgreSQLEventStore initialized")

    def _initialize_connection(self) -> None:
        """Инициализация подключения к PostgreSQL"""
        try:
            import psycopg2

            self.conn = psycopg2.connect(self.connection_string)
            logger.info("PostgreSQL connection established")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}", exc_info=True)
            raise

    def _create_tables(self) -> None:
        """Создание таблиц для event store"""
        try:
            cursor = self.conn.cursor()

            # Таблица для событий
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id SERIAL PRIMARY KEY,
                    event_id VARCHAR(255) UNIQUE NOT NULL,
                    stream_id VARCHAR(255) NOT NULL,
                    event_type VARCHAR(100) NOT NULL,
                    version INTEGER NOT NULL,
                    payload JSONB NOT NULL,
                    metadata JSONB,
                    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    UNIQUE(stream_id, version)
                )
            """
            )

            # Индексы для быстрого поиска
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_events_stream_id ON events(stream_id)
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_events_event_type ON events(event_type)
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)
            """
            )

            self.conn.commit()
            cursor.close()

            logger.info("Event store tables created/verified")

        except Exception as e:
            logger.error(f"Failed to create tables: {e}", exc_info=True)
            self.conn.rollback()
            raise

    async def append(self, stream_id: str, event: Event) -> None:
        """
        Добавление события в PostgreSQL с версионированием

        Args:
            stream_id: ID потока событий
            event: Событие для добавления
        """
        try:
            import json

            cursor = self.conn.cursor()

            # Получаем текущую версию потока
            cursor.execute(
                "SELECT COALESCE(MAX(version), 0) FROM events WHERE stream_id = %s", (stream_id,))
            current_version = cursor.fetchone()[0]
            next_version = current_version + 1

            # Вставляем событие
            cursor.execute(
                """
                INSERT INTO events (event_id, stream_id, event_type, version, payload, metadata, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    event.id,
                    stream_id,
                    event.type.value,
                    next_version,
                    json.dumps(event.payload),
                    json.dumps(event.metadata) if event.metadata else None,
                    event.timestamp,
                ),
            )

            self.conn.commit()
            cursor.close()

            logger.debug(
                f"Event appended to PostgreSQL stream {stream_id}",
                extra={
                    "stream_id": stream_id,
                    "event_id": event.id,
                    "event_type": event.type.value,
                    "version": next_version,
                },
            )

        except Exception as e:
            logger.error(f"Failed to append event: {e}", exc_info=True)
            self.conn.rollback()
            raise

    async def get_stream(self, stream_id: str, from_version: int = 0, to_version: Optional[int] = None) -> EventStream:
        """
        Получение потока из PostgreSQL

        Args:
            stream_id: ID потока
            from_version: начальная версия
            to_version: конечная версия

        Returns:
            EventStream с событиями
        """
        try:
            import json

            from psycopg2.extras import RealDictCursor

            cursor = self.conn.cursor(cursor_factory=RealDictCursor)

            # Запрос событий
            if to_version is not None:
                cursor.execute(
                    """
                    SELECT event_id, event_type, version, payload, metadata, timestamp
                    FROM events
                    WHERE stream_id = %s AND version >= %s AND version <= %s
                    ORDER BY version ASC
                    """,
                    (stream_id, from_version, to_version),
                )
            else:
                cursor.execute(
                    """
                    SELECT event_id, event_type, version, payload, metadata, timestamp
                    FROM events
                    WHERE stream_id = %s AND version >= %s
                    ORDER BY version ASC
                    """,
                    (stream_id, from_version),
                )

            rows = cursor.fetchall()
            cursor.close()

            # Конвертируем в Event объекты
            events = []
            max_version = 0

            for row in rows:
                event = Event(
                    id=row["event_id"],
                    type=EventType(row["event_type"]),
                    payload=json.loads(row["payload"]) if isinstance(
                        row["payload"], str) else row["payload"],
                    metadata=json.loads(row["metadata"])
                    if row["metadata"] and isinstance(row["metadata"], str)
                    else row["metadata"],
                    timestamp=row["timestamp"],
                )
                events.append(event)
                max_version = max(max_version, row["version"])

            logger.debug(
                f"Retrieved stream from PostgreSQL",
                extra={"stream_id": stream_id, "events_count": len(
                    events), "version": max_version},
            )

            return EventStream(stream_id, events, max_version)

        except Exception as e:
            logger.error(f"Failed to get stream: {e}", exc_info=True)
            return EventStream(stream_id, [])

    async def get_events(
        self,
        event_type: Optional[EventType] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Event]:
        """
        Получение событий из PostgreSQL с фильтрами

        Args:
            event_type: фильтр по типу события
            from_date: начальная дата
            to_date: конечная дата
            limit: максимальное количество событий

        Returns:
            Список событий
        """
        try:
            import json

            from psycopg2.extras import RealDictCursor

            cursor = self.conn.cursor(cursor_factory=RealDictCursor)

            # Строим запрос с фильтрами
            conditions = []
            params = []

            if event_type:
                conditions.append("event_type = %s")
                params.append(event_type.value)

            if from_date:
                conditions.append("timestamp >= %s")
                params.append(from_date)

            if to_date:
                conditions.append("timestamp <= %s")
                params.append(to_date)

            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

            query = f"""
                SELECT event_id, event_type, payload, metadata, timestamp
                FROM events
                {where_clause}
                ORDER BY timestamp DESC
                LIMIT %s
            """
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()

            # Конвертируем в Event объекты
            events = []
            for row in rows:
                event = Event(
                    id=row["event_id"],
                    type=EventType(row["event_type"]),
                    payload=json.loads(row["payload"]) if isinstance(
                        row["payload"], str) else row["payload"],
                    metadata=json.loads(row["metadata"])
                    if row["metadata"] and isinstance(row["metadata"], str)
                    else row["metadata"],
                    timestamp=row["timestamp"],
                )
                events.append(event)

            logger.debug(
                f"Retrieved events from PostgreSQL",
                extra={"count": len(
                    events), "event_type": event_type.value if event_type else None},
            )

            return events

        except Exception as e:
            logger.error(f"Failed to get events: {e}", exc_info=True)
            return []


# Глобальный экземпляр Event Store
_global_event_store: Optional[EventStore] = None


def get_event_store() -> EventStore:
    """Получение глобального Event Store"""
    global _global_event_store

    if _global_event_store is None:
        _global_event_store = InMemoryEventStore()

    return _global_event_store


def set_event_store(event_store: EventStore) -> None:
    """Установка глобального Event Store"""
    global _global_event_store
    _global_event_store = event_store
