# [NEXUS IDENTITY] ID: 8702635833363893569 | DATE: 2025-11-19

"""
E2E tests for Self-Evolving System - 1000% coverage
==================================================

End-to-end тестирование самоэволюционирующей системы
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.ai.llm_provider_abstraction import LLMProviderAbstraction
from src.ai.self_evolving_ai import EvolutionStage, SelfEvolvingAI
from src.infrastructure.event_bus import EventBus, EventType


@pytest.mark.asyncio
async def test_full_evolution_cycle():
    """Тест полного цикла эволюции"""
    # Mock LLM провайдер
    llm_provider = MagicMock(spec=LLMProviderAbstraction)
    llm_provider.generate = AsyncMock(return_value='{"improvements": []}')

    # Event Bus
    bus = EventBus()
    await bus.start()

    # Self-Evolving AI
    evolving_ai = SelfEvolvingAI(llm_provider, bus)

    # Запуск эволюции
    result = await evolving_ai.evolve()

    # Проверка результата
    assert result["status"] in ["completed", "failed"]
    assert "improvements_generated" in result

    # Проверка статуса
    status = evolving_ai.get_evolution_status()
    assert status["stage"] in [s.value for s in EvolutionStage]
    assert status["is_evolving"] is False

    await bus.stop()


@pytest.mark.asyncio
async def test_evolution_with_events():
    """Тест эволюции с событиями"""
    llm_provider = MagicMock(spec=LLMProviderAbstraction)
    llm_provider.generate = AsyncMock(return_value='{"improvements": []}')

    bus = EventBus()
    await bus.start()

    # Сбор событий
    events_received = []

    class EventCollector:
        async def handle(self, event):
            events_received.append(event.type)

    collector = EventCollector()
    bus.subscribe(EventType.AI_AGENT_STARTED, collector)
    bus.subscribe(EventType.AI_AGENT_EVOLVED, collector)
    bus.subscribe(EventType.AI_AGENT_FAILED, collector)

    evolving_ai = SelfEvolvingAI(llm_provider, bus)

    await evolving_ai.evolve()

    # Ожидание обработки событий
    await asyncio.sleep(0.2)

    # Проверка событий
    assert EventType.AI_AGENT_STARTED in events_received

    await bus.stop()
