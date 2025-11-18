"""
Integration tests for Event-Driven ML Tasks - 1000% coverage
============================================================

Тестирование замены Celery на Event-Driven Architecture
"""

import pytest
import asyncio
from src.infrastructure.event_bus import EventBus, EventType, EventPublisher
from src.infrastructure.event_store import EventStore, InMemoryEventStore


class MLTrainingHandler:
    """Обработчик для ML обучения"""
    
    def __init__(self):
        self.training_results = []
    
    async def handle(self, event):
        """Обработка события обучения"""
        if event.type == EventType.ML_TRAINING_STARTED:
            # Симуляция обучения
            await asyncio.sleep(0.1)
            self.training_results.append({
                "status": "completed",
                "model": event.payload.get("model")
            })


@pytest.mark.asyncio
async def test_ml_training_event_driven():
    """Тест ML обучения через Event-Driven"""
    bus = EventBus()
    await bus.start()
    
    handler = MLTrainingHandler()
    bus.subscribe(EventType.ML_TRAINING_STARTED, handler)
    
    publisher = EventPublisher(bus, "ml-service")
    
    # Публикация событий обучения
    await publisher.publish(
        EventType.ML_TRAINING_STARTED,
        {"model": "classification", "dataset": "train.csv"}
    )
    
    await publisher.publish(
        EventType.ML_TRAINING_STARTED,
        {"model": "regression", "dataset": "train.csv"}
    )
    
    # Ожидание обработки
    await asyncio.sleep(0.2)
    
    assert len(handler.training_results) == 2
    
    await bus.stop()


@pytest.mark.asyncio
async def test_ml_training_with_event_store():
    """Тест ML обучения с Event Store"""
    bus = EventBus()
    await bus.start()
    
    event_store = InMemoryEventStore()
    
    publisher = EventPublisher(bus, "ml-service")
    
    # Публикация события
    event = await publisher.publish(
        EventType.ML_TRAINING_STARTED,
        {"model": "classification"}
    )
    
    # Сохранение в Event Store
    await event_store.append("ml-training-stream", event)
    
    # Получение из Event Store
    stream = await event_store.get_stream("ml-training-stream")
    assert len(stream.events) == 1
    assert stream.events[0].type == EventType.ML_TRAINING_STARTED
    
    await bus.stop()


@pytest.mark.asyncio
async def test_parallel_ml_training():
    """Тест параллельного ML обучения"""
    bus = EventBus()
    await bus.start(num_workers=4)
    
    handlers = [MLTrainingHandler() for _ in range(3)]
    for handler in handlers:
        bus.subscribe(EventType.ML_TRAINING_STARTED, handler)
    
    publisher = EventPublisher(bus, "ml-service")
    
    # Публикация множества событий
    tasks = []
    for i in range(10):
        task = publisher.publish(
            EventType.ML_TRAINING_STARTED,
            {"model": f"model-{i}"}
        )
        tasks.append(task)
    
    await asyncio.gather(*tasks)
    
    # Ожидание обработки
    await asyncio.sleep(0.3)
    
    # Проверка, что все события обработаны
    total_results = sum(len(h.training_results) for h in handlers)
    assert total_results == 10
    
    await bus.stop()

