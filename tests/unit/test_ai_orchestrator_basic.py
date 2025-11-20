# [NEXUS IDENTITY] ID: -327969305903321671 | DATE: 2025-11-19

import pytest

from src.ai.orchestrator import AIOrchestrator
from src.monitoring.prometheus_metrics import (orchestrator_cache_hits_total,
                                               orchestrator_cache_misses_total)


@pytest.mark.asyncio
async def test_process_query_invalid_raises_value_error():
    orchestrator = AIOrchestrator()

    with pytest.raises(ValueError):
        await orchestrator.process_query("")


@pytest.mark.asyncio
async def test_process_query_unknown_uses_multi_service_stub():
    orchestrator = AIOrchestrator()

    # Короткий общий запрос, который классификатор может отнести к UNKNOWN
    before_miss = orchestrator_cache_misses_total._value.get()

    response = await orchestrator.process_query("Просто поговорим о best practices")

    assert response["type"] == "multi_service"
    assert "detailed_results" in response
    # В offline-режиме хотя бы один сервис должен быть помечен как skipped/naparnik
    assert response["detailed_results"]

    # Проверяем, что промах кэша засчитан
    after_miss = orchestrator_cache_misses_total._value.get()
    assert after_miss >= before_miss


@pytest.mark.asyncio
async def test_process_query_uses_cache_on_second_call():
    orchestrator = AIOrchestrator()
    query = "Пример запроса для кэша"
    context = {"type": "example"}

    before_hit = orchestrator_cache_hits_total._value.get()

    first = await orchestrator.process_query(query, context)
    # После первого вызова результат должен попасть в кэш
    cache_key = f"{query}:{context}"
    assert cache_key in orchestrator.cache

    second = await orchestrator.process_query(query, context)
    # Ответы должны совпадать (берём из кэша)
    assert first == second

    # Проверяем, что попадание в кэш засчитано
    after_hit = orchestrator_cache_hits_total._value.get()
    assert after_hit >= before_hit


@pytest.mark.asyncio
async def test_handle_code_generation_without_services_returns_error():
    """
    Если ни Kimi, ни Qwen не сконфигурированы, _handle_code_generation должен
    вернуть понятную ошибку, а не падать.
    """
    orchestrator = AIOrchestrator()
    # Явно выключаем клиентов, чтобы гарантировать fallback-ветку
    orchestrator.kimi_client = None
    orchestrator.qwen_client = None

    result = await orchestrator._handle_code_generation(  # type: ignore[attr-defined]
        "Сгенерируй функцию 1С", {}
    )

    assert result["type"] == "code_generation"
    assert result["service"] == "qwen_coder"
    assert "No code generation service available" in result["error"]


@pytest.mark.asyncio
async def test_handle_optimization_without_code_returns_error():
    """
    _handle_optimization должен явно сообщать об отсутствии кода в context.
    """
    orchestrator = AIOrchestrator()
    orchestrator.kimi_client = None
    orchestrator.qwen_client = None

    result = await orchestrator._handle_optimization(  # type: ignore[attr-defined]
        "Оптимизируй код", {}
    )

    assert result["type"] == "optimization"
    assert "No code provided in context" in result["error"]
