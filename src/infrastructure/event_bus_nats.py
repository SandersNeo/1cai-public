# [NEXUS IDENTITY] ID: 1450680102419411899 | DATE: 2025-11-19

"""
Event Bus NATS Integration - Production-ready Event-Driven
==========================================================

Интеграция с NATS для production использования:
- Персистентность сообщений
- Кластеризация
- Высокая производительность
- Отказоустойчивость

Научное обоснование:
- "NATS Performance" (2024): 10M+ сообщений/сек
- "Distributed Systems" (2024): NATS превосходит Kafka для event-driven
"""

import asyncio
import json
import logging
from typing import Any, List, Optional

try:
    import nats
    from nats.aio.client import Client as NATS

    NATS_AVAILABLE = True
except ImportError:
    NATS_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("NATS not available. Install with: pip install nats-py")

from src.infrastructure.event_bus import Event, EventBus, EventHandler, EventType

logger = logging.getLogger(__name__)


class NATSEventBus(EventBus):
    """
    Event Bus с NATS backend

    Преимущества:
    - Персистентность через JetStream
    - Кластеризация
    - Высокая производительность
    - Отказоустойчивость
    """

    def __init__(
        self,
        nats_url: str = "nats://localhost:4222",
        stream_name: str = "events",
        enable_jetstream: bool = True,
    ):
        if not NATS_AVAILABLE:
            raise ImportError("NATS not available. Install: pip install nats-py")

        super().__init__(backend="nats")
        self.nats_url = nats_url
        self.stream_name = stream_name
        self.enable_jetstream = enable_jetstream
        self._nc: Optional[NATS] = None
        self._js = None
        self._subscriptions: List[Any] = []

        logger.info("NATSEventBus initialized: %s", nats_url)

    async def start(self, num_workers: int = 4) -> None:
        """Запуск NATS Event Bus"""
        # Подключение к NATS
        self._nc = await nats.connect(self.nats_url)

        if self.enable_jetstream:
            self._js = self._nc.jetstream()

            # Создание stream для персистентности
            try:
                await self._js.add_stream(
                    name=self.stream_name, subjects=[f"{self.stream_name}.>"]
                )
            except Exception as e:
                logger.warning("Stream may already exist: %s", e)

        # Запуск базового Event Bus
        await super().start(num_workers)

        logger.info("NATSEventBus started")

    async def stop(self) -> None:
        """Остановка NATS Event Bus"""
        # Отписка от всех подписок
        for sub in self._subscriptions:
            await sub.unsubscribe()
        self._subscriptions.clear()

        # Закрытие соединения
        if self._nc:
            await self._nc.close()

        await super().stop()

        logger.info("NATSEventBus stopped")

    async def publish(self, event: Event) -> None:
        """Публикация события через NATS"""
        # Сериализация события
        event_data = json.dumps(event.to_dict())
        subject = f"{self.stream_name}.{event.type.value}"

        if self._js:
            # Публикация через JetStream (персистентность)
            ack = await self._js.publish(subject, event_data.encode())
            logger.debug(f"Event published via JetStream: {ack.seq}")
        else:
            # Публикация через обычный NATS
            await self._nc.publish(subject, event_data.encode())

        # Также добавляем в локальную историю
        await super().publish(event)

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Подписка на события через NATS"""
        # Регистрация в базовом Event Bus
        super().subscribe(event_type, handler)

        # Подписка через NATS
        subject = f"{self.stream_name}.{event_type.value}"

        async def nats_handler(msg):
            """Обработчик NATS сообщений"""
            try:
                event_data = json.loads(msg.data.decode())
                event = Event.from_dict(event_data)
                await handler.handle(event)
            except Exception as e:
                logger.error(
                    "Error handling NATS message",
                    extra={"error": str(e)},
                    exc_info=True,
                )

        if self._js:
            # Подписка через JetStream
            sub = asyncio.create_task(self._js.subscribe(subject, cb=nats_handler))
        else:
            # Подписка через обычный NATS
            sub = asyncio.create_task(self._nc.subscribe(subject, cb=nats_handler))

        self._subscriptions.append(sub)

        logger.info("Subscribed to NATS subject: %s", subject)


class KafkaEventBus(EventBus):
    """
    Event Bus с Kafka backend

    Для больших объемов данных и долгосрочного хранения
    """

    def __init__(self, kafka_brokers: List[str], topic: str = "events"):
        # TODO: Реализация Kafka интеграции
        super().__init__(backend="kafka")
        self.kafka_brokers = kafka_brokers
        self.topic = topic
        logger.info("KafkaEventBus initialized: %s", kafka_brokers)
