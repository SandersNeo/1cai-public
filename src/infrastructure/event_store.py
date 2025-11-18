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

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .event_bus import Event, EventType

logger = logging.getLogger(__name__)


class EventStream:
    """Поток событий"""
    
    def __init__(
        self,
        stream_id: str,
        events: List[Event],
        version: int = 0
    ):
        self.stream_id = stream_id
        self.events = events
        self.version = version
    
    def append(self, event: Event) -> None:
        """Добавление события в поток"""
        self.events.append(event)
        self.version += 1
    
    def get_events(
        self,
        from_version: int = 0,
        to_version: Optional[int] = None
    ) -> List[Event]:
        """Получение событий из потока"""
        start = from_version
        end = to_version if to_version is not None else len(self.events)
        return self.events[start:end]


class EventStore(ABC):
    """Абстрактное хранилище событий"""
    
    @abstractmethod
    async def append(
        self,
        stream_id: str,
        event: Event
    ) -> None:
        """Добавление события в поток"""
        pass
    
    @abstractmethod
    async def get_stream(
        self,
        stream_id: str,
        from_version: int = 0,
        to_version: Optional[int] = None
    ) -> EventStream:
        """Получение потока событий"""
        pass
    
    @abstractmethod
    async def get_events(
        self,
        event_type: Optional[EventType] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Event]:
        """Получение событий по фильтрам"""
        pass


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
                "version": stream.version
            }
        )
    
    async def get_stream(
        self,
        stream_id: str,
        from_version: int = 0,
        to_version: Optional[int] = None
    ) -> EventStream:
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
        limit: int = 100
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
        # TODO: Инициализация подключения к PostgreSQL
        logger.info("PostgreSQLEventStore initialized")
    
    async def append(self, stream_id: str, event: Event) -> None:
        """Добавление события в PostgreSQL"""
        # TODO: Реализация записи в БД
        logger.debug(f"Event appended to PostgreSQL stream {stream_id}")
    
    async def get_stream(
        self,
        stream_id: str,
        from_version: int = 0,
        to_version: Optional[int] = None
    ) -> EventStream:
        """Получение потока из PostgreSQL"""
        # TODO: Реализация чтения из БД
        return EventStream(stream_id, [])
    
    async def get_events(
        self,
        event_type: Optional[EventType] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Event]:
        """Получение событий из PostgreSQL"""
        # TODO: Реализация запроса к БД
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

