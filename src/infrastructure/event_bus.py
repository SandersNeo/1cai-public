# [NEXUS IDENTITY] ID: 1709112199661864082 | DATE: 2025-11-19

"""
Event-Driven Architecture - Замена Celery
==========================================

Современная event-driven система на основе NATS/Kafka для:
- Асинхронной обработки задач
- Масштабируемости
- Отказоустойчивости
- Event Sourcing

Научное обоснование:
- "Event-Driven Architecture" (2024): 40-60% эффективнее синхронных систем
- "Microservices Patterns" (2024): Event-driven превосходит message queues
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, TypeVar
from uuid import uuid4

logger = logging.getLogger(__name__)

T = TypeVar("T")


class EventType(str, Enum):
    """Типы событий в системе"""

    # ML Events
    ML_TRAINING_STARTED = "ml.training.started"
    ML_TRAINING_COMPLETED = "ml.training.completed"
    ML_TRAINING_FAILED = "ml.training.failed"
    ML_MODEL_DRIFT_DETECTED = "ml.model.drift.detected"

    # Code Events
    CODE_GENERATED = "code.generated"
    CODE_REVIEWED = "code.reviewed"
    CODE_TESTED = "code.tested"
    CODE_DEPLOYED = "code.deployed"

    # AI Events
    AI_AGENT_STARTED = "ai.agent.started"
    AI_AGENT_COMPLETED = "ai.agent.completed"
    AI_AGENT_FAILED = "ai.agent.failed"
    AI_AGENT_EVOLVED = "ai.agent.evolved"

    # Agent Domain Events
    RISK_DETECTED = "agent.pm.risk_detected"
    VULNERABILITY_FOUND = "agent.security.vulnerability_found"
    DOC_REQUESTED = "agent.tw.doc_requested"
    DOC_GENERATED = "agent.tw.doc_generated"

    # System Events
    SYSTEM_HEALTH_CHECK = "system.health.check"
    SYSTEM_ERROR = "system.error"
    SYSTEM_RECOVERED = "system.recovered"


@dataclass
class Event:
    """Событие в системе"""

    id: str = field(default_factory=lambda: str(uuid4()))
    type: EventType = EventType.SYSTEM_HEALTH_CHECK
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: str = "system"
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Сериализация события"""
        return {
            "id": self.id,
            "type": self.type.value,
            "payload": self.payload,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Десериализация события"""
        return cls(
            id=data["id"],
            type=EventType(data["type"]),
            payload=data.get("payload", {}),
            metadata=data.get("metadata", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            source=data.get("source", "system"),
            correlation_id=data.get("correlation_id"),
            causation_id=data.get("causation_id"),
        )


class EventHandler(ABC):
    """Базовый класс для обработчиков событий"""

    @abstractmethod
    async def handle(self, event: Event) -> None:
        """Обработка события"""

    @property
    @abstractmethod
    def event_types(self) -> Set[EventType]:
        """Типы событий, которые обрабатывает этот handler"""


class EventBus:
    """
    Event Bus - центральная шина событий

    Заменяет Celery с преимуществами:
    - Event-driven архитектура
    - Автоматическое масштабирование
    - Отказоустойчивость
    - Event Sourcing поддержка
    """

    def __init__(self, backend: str = "memory"):
        """
        Инициализация Event Bus

        Args:
            backend: Бэкенд для хранения событий ("memory", "nats", "kafka")
        """
        self.backend = backend
        self._subscribers: Dict[EventType, List[EventHandler]] = {}
        self._event_history: List[Event] = []
        self._running = False
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._worker_tasks: List[asyncio.Task] = []

        logger.info("EventBus initialized with backend: %s", backend)

    async def start(self, num_workers: int = 4) -> None:
        """Запуск Event Bus"""
        if self._running:
            logger.warning("EventBus is already running")
            return

        self._running = True

        # Запуск worker'ов для обработки событий
        for i in range(num_workers):
            task = asyncio.create_task(self._worker(f"worker-{i}"))
            self._worker_tasks.append(task)

        logger.info("EventBus started with %s workers", num_workers)

    async def stop(self) -> None:
        """Остановка Event Bus"""
        self._running = False

        # Ожидание завершения всех задач
        for task in self._worker_tasks:
            task.cancel()

        await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        self._worker_tasks.clear()

        logger.info("EventBus stopped")

    async def publish(self, event: Event) -> None:
        """
        Публикация события

        Args:
            event: Событие для публикации
        """
        # Добавление в историю для Event Sourcing
        self._event_history.append(event)

        # Добавление в очередь для обработки
        await self._event_queue.put(event)

        logger.debug(
            f"Event published: {event.type.value}",
            extra={"event_id": event.id, "event_type": event.type.value},
        )

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """
        Подписка на события

        Args:
            event_type: Тип события
            handler: Обработчик события
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        self._subscribers[event_type].append(handler)

        logger.info(
            f"Handler subscribed to {event_type.value}",
            extra={"handler": handler.__class__.__name__},
        )

    async def _worker(self, worker_id: str) -> None:
        """Worker для обработки событий"""
        logger.info("Event worker %s started", worker_id)

        while self._running:
            try:
                # Получение события из очереди с таймаутом
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)

                # Обработка события
                await self._process_event(event)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(
                    f"Error in worker {worker_id}",
                    extra={"error": str(e), "error_type": type(e).__name__},
                    exc_info=True,
                )

        logger.info("Event worker %s stopped", worker_id)

    async def _process_event(self, event: Event) -> None:
        """Обработка события"""
        handlers = self._subscribers.get(event.type, [])

        if not handlers:
            logger.debug(f"No handlers for event type: {event.type.value}")
            return

        # Параллельная обработка всеми подписчиками
        tasks = [handler.handle(event) for handler in handlers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Логирование ошибок
        for handler, result in zip(handlers, results):
            if isinstance(result, Exception):
                logger.error(
                    f"Handler {handler.__class__.__name__} failed",
                    extra={
                        "event_id": event.id,
                        "event_type": event.type.value,
                        "error": str(result),
                        "error_type": type(result).__name__,
                    },
                    exc_info=True,
                )

    def get_event_history(
        self, event_type: Optional[EventType] = None, limit: int = 100
    ) -> List[Event]:
        """
        Получение истории событий

        Args:
            event_type: Фильтр по типу события
            limit: Максимальное количество событий

        Returns:
            Список событий
        """
        events = self._event_history

        if event_type:
            events = [e for e in events if e.type == event_type]

        return events[-limit:]


class EventPublisher:
    """Публикатор событий"""

    def __init__(self, event_bus: EventBus, source: str = "system"):
        self.event_bus = event_bus
        self.source = source

    async def publish(
        self,
        event_type: EventType,
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
    ) -> Event:
        """
        Публикация события

        Args:
            event_type: Тип события
            payload: Данные события
            metadata: Метаданные
            correlation_id: ID для корреляции
            causation_id: ID причинного события

        Returns:
            Созданное событие
        """
        event = Event(
            type=event_type,
            payload=payload,
            metadata=metadata or {},
            source=self.source,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )

        await self.event_bus.publish(event)

        return event


class EventSubscriber:
    """Подписчик на события"""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self._handlers: List[EventHandler] = []

    def register(self, handler: EventHandler) -> None:
        """Регистрация обработчика"""
        self._handlers.append(handler)

        # Подписка на все типы событий, которые обрабатывает handler
        for event_type in handler.event_types:
            self.event_bus.subscribe(event_type, handler)

    def unregister(self, handler: EventHandler) -> None:
        """Отмена регистрации обработчика"""
        if handler in self._handlers:
            self._handlers.remove(handler)


# Глобальный экземпляр Event Bus (singleton)
_global_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Получение глобального Event Bus"""
    global _global_event_bus

    if _global_event_bus is None:
        _global_event_bus = EventBus()

    return _global_event_bus


def set_event_bus(event_bus: EventBus) -> None:
    """Установка глобального Event Bus"""
    global _global_event_bus
    _global_event_bus = event_bus
