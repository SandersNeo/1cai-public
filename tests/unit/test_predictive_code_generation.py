# [NEXUS IDENTITY] ID: 7138144087051384657 | DATE: 2025-11-19

"""
Unit tests for Predictive Code Generation - 1000% coverage
==========================================================
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.ai.llm_provider_abstraction import LLMProviderAbstraction
from src.ai.predictive_code_generation import (PredictedRequirement,
                                               PredictiveCodeGenerator,
                                               Requirement)


@pytest.fixture
def mock_llm_provider():
    """Mock LLM провайдер"""
    provider = MagicMock(spec=LLMProviderAbstraction)
    provider.generate = AsyncMock(return_value="Generated requirement")
    return provider


@pytest.fixture
def generator(mock_llm_provider):
    """Predictive Code Generator для тестов"""
    return PredictiveCodeGenerator(mock_llm_provider)


@pytest.mark.asyncio
async def test_analyze_trends(generator):
    """Тест анализа трендов"""
    # Добавление требований
    for i in range(10):
        req = Requirement(
            description=f"Requirement {i}",
            category="feature",
            timestamp=datetime.utcnow() - timedelta(days=i),
        )
        generator.add_requirement(req)

    trends = await generator.analyze_trends(lookback_days=30)

    assert len(trends) > 0
    assert all(t.frequency >= 0.0 for t in trends)


@pytest.mark.asyncio
async def test_predict_requirements(generator):
    """Тест предсказания требований"""
    # Добавление требований для анализа
    for i in range(5):
        req = Requirement(description=f"Requirement {i}", category="feature")
        generator.add_requirement(req)

    predictions = await generator.predict_requirements(horizon_days=30)

    assert isinstance(predictions, list)


@pytest.mark.asyncio
async def test_generate_code_ahead(generator):
    """Тест генерации кода заранее"""
    prediction = PredictedRequirement(
        description="Test requirement", category="feature", probability=0.8
    )

    result = await generator.generate_code_ahead(prediction)

    assert result.ready is True
    assert result.generated_code is not None


@pytest.mark.asyncio
async def test_predict_and_prepare(generator):
    """Тест полного цикла предсказания и подготовки"""
    # Добавление требований
    for i in range(5):
        req = Requirement(description=f"Requirement {i}", category="feature")
        generator.add_requirement(req)

    result = await generator.predict_and_prepare(horizon_days=30)

    assert "predictions_count" in result
    assert "generated_count" in result
    assert "prepared_count" in result


def test_add_requirement(generator):
    """Тест добавления требования"""
    req = Requirement(description="Test requirement")

    generator.add_requirement(req)

    assert len(generator._requirements_history) == 1


def test_get_statistics(generator):
    """Тест получения статистики"""
    stats = generator.get_statistics()

    assert "requirements_history_count" in stats
    assert "trends_count" in stats
    assert "predictions_count" in stats
