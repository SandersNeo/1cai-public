# [NEXUS IDENTITY] ID: 1140481912916084981 | DATE: 2025-11-19

"""
Unit tests for Event Bus - 1000% coverage
==========================================
"""

import asyncio

import pytest

from src.infrastructure.event_bus import (Event, EventBus, EventHandler,
                                          EventPublisher, EventSubscriber,
                                          EventType)


class MockEventHandler(EventHandler):
    """Mock обработчик событий для тестов"""

    def __init__(self, event_types):
        self.event_types = set(event_types)
        self.handled_events = []

    async def handle(self, event: Event) -> None:
        self.handled_events.append(event)


@pytest.mark.asyncio
async def test_event_creation():
    """Тест создания события"""
    event = Event(
        type=EventType.ML_TRAINING_STARTED, payload={"model": "test"}, source="test"
    )

    assert event.type == EventType.ML_TRAINING_STARTED
    assert event.payload == {"model": "test"}
    assert event.source == "test"
    assert event.id is not None


@pytest.mark.asyncio
async def test_event_serialization():
    """Тест сериализации события"""
    event = Event(type=EventType.ML_TRAINING_STARTED, payload={"model": "test"})

    data = event.to_dict()
    assert data["type"] == EventType.ML_TRAINING_STARTED.value
    assert data["payload"] == {"model": "test"}

    # Десериализация
    restored = Event.from_dict(data)
    assert restored.type == event.type
    assert restored.payload == event.payload


@pytest.mark.asyncio
async def test_event_bus_start_stop():
    """Тест запуска и остановки Event Bus"""
    bus = EventBus()

    await bus.start(num_workers=2)
    assert bus._running is True
    assert len(bus._worker_tasks) == 2

    await bus.stop()
    assert bus._running is False


@pytest.mark.asyncio
async def test_event_bus_publish_subscribe():
    """Тест публикации и подписки на события"""
    bus = EventBus()
    await bus.start()

    handler = MockEventHandler([EventType.ML_TRAINING_STARTED])
    bus.subscribe(EventType.ML_TRAINING_STARTED, handler)

    event = Event(type=EventType.ML_TRAINING_STARTED, payload={"test": "data"})

    await bus.publish(event)

    # Ожидание обработки
    await asyncio.sleep(0.1)

    assert len(handler.handled_events) == 1
    assert handler.handled_events[0].id == event.id

    await bus.stop()


@pytest.mark.asyncio
async def test_event_bus_multiple_handlers():
    """Тест множественных обработчиков"""
    bus = EventBus()
    await bus.start()

    handler1 = MockEventHandler([EventType.ML_TRAINING_STARTED])
    handler2 = MockEventHandler([EventType.ML_TRAINING_STARTED])

    bus.subscribe(EventType.ML_TRAINING_STARTED, handler1)
    bus.subscribe(EventType.ML_TRAINING_STARTED, handler2)

    event = Event(type=EventType.ML_TRAINING_STARTED)
    await bus.publish(event)

    await asyncio.sleep(0.1)

    assert len(handler1.handled_events) == 1
    assert len(handler2.handled_events) == 1

    await bus.stop()


@pytest.mark.asyncio
async def test_event_publisher():
    """Тест Event Publisher"""
    bus = EventBus()
    await bus.start()

    publisher = EventPublisher(bus, source="test")

    handler = MockEventHandler([EventType.ML_TRAINING_STARTED])
    bus.subscribe(EventType.ML_TRAINING_STARTED, handler)

    event = await publisher.publish(
        EventType.ML_TRAINING_STARTED, payload={"test": "data"}
    )

    await asyncio.sleep(0.1)

    assert len(handler.handled_events) == 1
    assert event.source == "test"

    await bus.stop()


@pytest.mark.asyncio
async def test_event_subscriber():
    """Тест Event Subscriber"""
    bus = EventBus()
    await bus.start()

    subscriber = EventSubscriber(bus)

    handler = MockEventHandler([EventType.ML_TRAINING_STARTED])
    subscriber.register(handler)

    event = Event(type=EventType.ML_TRAINING_STARTED)
    await bus.publish(event)

    await asyncio.sleep(0.1)

    assert len(handler.handled_events) == 1

    await bus.stop()


@pytest.mark.asyncio
async def test_event_history():
    """Тест истории событий"""
    bus = EventBus()

    event1 = Event(type=EventType.ML_TRAINING_STARTED)
    event2 = Event(type=EventType.ML_TRAINING_COMPLETED)

    await bus.publish(event1)
    await bus.publish(event2)

    history = bus.get_event_history()
    assert len(history) == 2

    filtered = bus.get_event_history(EventType.ML_TRAINING_STARTED)
    assert len(filtered) == 1
    assert filtered[0].type == EventType.ML_TRAINING_STARTED


@pytest.mark.asyncio
async def test_event_correlation():
    """Тест корреляции событий"""
    bus = EventBus()
    await bus.start()

    event1 = Event(type=EventType.ML_TRAINING_STARTED, correlation_id="corr-123")

    event2 = Event(
        type=EventType.ML_TRAINING_COMPLETED,
        correlation_id="corr-123",
        causation_id=event1.id,
    )

    await bus.publish(event1)
    await bus.publish(event2)

    history = bus.get_event_history()
    assert len(history) == 2
    assert history[1].causation_id == event1.id

    await bus.stop()
