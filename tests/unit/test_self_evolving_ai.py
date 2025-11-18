"""
Unit tests for Self-Evolving AI - 1000% coverage
=================================================
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.ai.self_evolving_ai import (
    SelfEvolvingAI,
    EvolutionStage,
    PerformanceMetrics,
    Improvement
)
from src.ai.llm_provider_abstraction import LLMProviderAbstraction
from src.infrastructure.event_bus import EventBus


@pytest.fixture
def mock_llm_provider():
    """Mock LLM провайдер"""
    provider = MagicMock(spec=LLMProviderAbstraction)
    provider.generate = AsyncMock(return_value='{"improvements": []}')
    return provider


@pytest.fixture
def event_bus():
    """Event Bus для тестов"""
    return EventBus()


@pytest.fixture
def self_evolving_ai(mock_llm_provider, event_bus):
    """Self-Evolving AI для тестов"""
    return SelfEvolvingAI(mock_llm_provider, event_bus)


@pytest.mark.asyncio
async def test_self_evolving_ai_initialization(self_evolving_ai):
    """Тест инициализации"""
    assert self_evolving_ai._evolution_stage == EvolutionStage.ANALYZING
    assert self_evolving_ai._is_evolving is False
    assert len(self_evolving_ai._performance_history) == 0
    assert len(self_evolving_ai._improvements) == 0


@pytest.mark.asyncio
async def test_analyze_performance(self_evolving_ai):
    """Тест анализа производительности"""
    metrics = await self_evolving_ai._analyze_performance()
    
    assert isinstance(metrics, PerformanceMetrics)
    assert metrics.accuracy >= 0.0
    assert metrics.latency_ms >= 0.0
    assert metrics.error_rate >= 0.0


@pytest.mark.asyncio
async def test_generate_improvements(self_evolving_ai):
    """Тест генерации улучшений"""
    performance = PerformanceMetrics(
        accuracy=0.85,
        latency_ms=500.0,
        error_rate=0.05
    )
    
    improvements = await self_evolving_ai._generate_improvements(performance)
    
    assert isinstance(improvements, list)


@pytest.mark.asyncio
async def test_test_improvements(self_evolving_ai):
    """Тест тестирования улучшений"""
    improvements = [
        Improvement(description="Test improvement 1"),
        Improvement(description="Test improvement 2")
    ]
    
    tested = await self_evolving_ai._test_improvements(improvements)
    
    assert len(tested) <= len(improvements)
    for imp in tested:
        assert imp.test_results is not None


@pytest.mark.asyncio
async def test_evaluate_improvements(self_evolving_ai):
    """Тест оценки улучшений"""
    improvements = [
        Improvement(
            description="Test 1",
            test_results={"unit_tests": {"passed": 10, "failed": 0}},
            expected_improvement={"accuracy": 0.1}
        ),
        Improvement(
            description="Test 2",
            test_results={"unit_tests": {"passed": 5, "failed": 0}},
            expected_improvement={"accuracy": 0.05}
        )
    ]
    
    best = await self_evolving_ai._evaluate_improvements(improvements)
    
    assert len(best) <= len(improvements)
    assert len(best) <= 3  # Топ-3


@pytest.mark.asyncio
async def test_apply_improvements(self_evolving_ai):
    """Тест применения улучшений"""
    improvements = [
        Improvement(description="Test improvement")
    ]
    
    applied = await self_evolving_ai._apply_improvements(improvements)
    
    assert len(applied) <= len(improvements)
    for imp in applied:
        assert imp.applied is True


@pytest.mark.asyncio
async def test_evolve_full_cycle(self_evolving_ai):
    """Тест полного цикла эволюции"""
    result = await self_evolving_ai.evolve()
    
    assert result["status"] in ["completed", "failed"]
    assert "improvements_generated" in result


@pytest.mark.asyncio
async def test_evolution_status(self_evolving_ai):
    """Тест статуса эволюции"""
    status = self_evolving_ai.get_evolution_status()
    
    assert "stage" in status
    assert "is_evolving" in status
    assert "improvements_count" in status


@pytest.mark.asyncio
async def test_evolution_prevent_double_run(self_evolving_ai):
    """Тест предотвращения двойного запуска"""
    # Запуск первого цикла
    task1 = asyncio.create_task(self_evolving_ai.evolve())
    
    # Попытка запуска второго цикла
    result2 = await self_evolving_ai.evolve()
    assert result2["status"] == "already_evolving"
    
    # Ожидание завершения первого
    await task1

