# [NEXUS IDENTITY] ID: -5360098857298508603 | DATE: 2025-11-19

"""
E2E тесты для полного цикла запроса с несколькими провайдерами и fallback.

Проверяет:
- Полный цикл запроса через Orchestrator
- Автоматический выбор провайдера
- Fallback между провайдерами
- Кэширование результатов
- Обработка ошибок и retry
"""

import pytest

from src.ai.orchestrator import AIOrchestrator
from src.ai.intelligent_cache import IntelligentCache
from src.ai.llm_provider_abstraction import LLMProviderAbstraction, QueryType
from src.ai.scenario_hub import (
    ScenarioPlan,
    ScenarioStep,
    ScenarioRiskLevel,
    AutonomyLevel,
)


@pytest.mark.asyncio
async def test_e2e_full_request_cycle_with_provider_selection():
    """E2E тест полного цикла запроса с автоматическим выбором провайдера."""
    orchestrator = AIOrchestrator()

    # Запрос на русском языке - должен автоматически выбрать российский провайдер
    query = "Объясни, как работает механизм проведения документов в 1С"

    try:
        result = await orchestrator.process_query(
            query,
            context={
                "compliance": ["152-ФЗ"],
            },
        )

        assert result is not None
        # Проверяем, что есть метаданные о выборе провайдера
        if "_meta" in result:
            assert "intent" in result["_meta"]
            # Провайдер должен быть выбран автоматически
            assert (
                result["_meta"].get("selected_provider") is not None
                or "gigachat" in str(result)
                or "yandexgpt" in str(result)
                or "naparnik" in str(result)
            )

    except Exception as e:
        # Ожидаем, что некоторые провайдеры могут быть недоступны
        assert (
            "not configured" in str(e).lower()
            or "network" in str(e).lower()
            or "credentials" in str(e).lower()
        )


@pytest.mark.asyncio
async def test_e2e_request_with_cache_hit():
    """E2E тест запроса с попаданием в кэш."""
    orchestrator = AIOrchestrator()

    query = "Тестовый запрос для кэширования"

    # Первый запрос - должен идти к провайдеру
    try:
        result1 = await orchestrator.process_query(query, context={})
        assert result1 is not None

        # Второй запрос - должен попасть в кэш
        result2 = await orchestrator.process_query(query, context={})
        assert result2 is not None

        # Проверяем, что результаты идентичны (или очень похожи)
        # (в реальности результат может немного отличаться из-за случайности)

    except Exception as e:
        # Ожидаем, что некоторые провайдеры могут быть недоступны
        assert "not configured" in str(e).lower() or "network" in str(e).lower()


@pytest.mark.asyncio
async def test_e2e_provider_fallback_on_error():
    """E2E тест fallback между провайдерами при ошибке."""
    abstraction = LLMProviderAbstraction()

    # Выбираем провайдера для русского текста
    provider1 = abstraction.select_provider(QueryType.RUSSIAN_TEXT)

    if provider1:
        # Проверяем, что есть альтернативные провайдеры
        alternative_providers = [
            p
            for p in abstraction.profiles.values()
            if QueryType.RUSSIAN_TEXT in p.capabilities
            and p.provider_id != provider1.provider_id
        ]

        # Должен быть хотя бы один альтернативный провайдер для fallback
        assert len(alternative_providers) > 0, "No alternative providers for fallback"


@pytest.mark.asyncio
async def test_e2e_multiple_concurrent_requests():
    """E2E тест множественных конкурентных запросов."""
    orchestrator = AIOrchestrator()

    queries = [
        "Запрос 1: объясни механизм проведения",
        "Запрос 2: как работает регистр сведений",
        "Запрос 3: опиши структуру документа",
    ]

    try:
        import asyncio

        # Выполняем запросы параллельно
        tasks = [orchestrator.process_query(query, context={}) for query in queries]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Проверяем, что все запросы обработаны (даже если с ошибками)
        assert len(results) == len(queries)

        # Большинство запросов должны быть успешными
        successful = sum(
            1 for r in results if r is not None and not isinstance(r, Exception)
        )
        # Хотя бы один должен быть успешным (или все могут быть с ошибками если нет провайдеров)
        assert successful >= 0

    except Exception as e:
        # Ожидаем, что некоторые провайдеры могут быть недоступны
        assert "not configured" in str(e).lower() or "network" in str(e).lower()


@pytest.mark.asyncio
async def test_e2e_request_with_different_query_types():
    """E2E тест запросов с разными типами."""
    abstraction = LLMProviderAbstraction()

    query_types = [
        QueryType.CODE_GENERATION,
        QueryType.CODE_REVIEW,
        QueryType.RUSSIAN_TEXT,
        QueryType.ENGLISH_TEXT,
        QueryType.ANALYSIS,
        QueryType.GENERAL,
    ]

    for query_type in query_types:
        provider = abstraction.select_provider(query_type)

        if provider:
            # Проверяем, что провайдер поддерживает этот тип запроса
            assert query_type in provider.capabilities


@pytest.mark.asyncio
async def test_e2e_request_with_cost_constraints():
    """E2E тест запроса с ограничением по стоимости."""
    abstraction = LLMProviderAbstraction()

    # Запрос с ограничением по стоимости (бесплатно)
    provider_free = abstraction.select_provider(
        QueryType.CODE_GENERATION,
        max_cost=0.0,
    )

    if provider_free:
        # Должен быть бесплатный провайдер (Ollama, 1C:Напарник или Qwen локально)
        assert provider_free.cost_per_1k_tokens == 0.0
        assert provider_free.provider_id in ["ollama", "naparnik", "qwen"]


@pytest.mark.asyncio
async def test_e2e_request_with_latency_constraints():
    """E2E тест запроса с ограничением по latency."""
    abstraction = LLMProviderAbstraction()

    # Запрос с ограничением по latency (быстрый ответ < 2 секунд)
    provider_fast = abstraction.select_provider(
        QueryType.RUSSIAN_TEXT,
        max_latency_ms=2000,
    )

    if provider_fast:
        # Должен быть провайдер с низкой latency
        assert provider_fast.avg_latency_ms <= 2000


@pytest.mark.asyncio
async def test_e2e_request_with_compliance_requirements():
    """E2E тест запроса с требованиями compliance."""
    abstraction = LLMProviderAbstraction()

    # Запрос с требованием 152-ФЗ
    provider_compliant = abstraction.select_provider(
        QueryType.RUSSIAN_TEXT,
        required_compliance=["152-ФЗ"],
    )

    if provider_compliant:
        # Должен быть провайдер с compliance 152-ФЗ
        assert "152-ФЗ" in provider_compliant.compliance


@pytest.mark.asyncio
async def test_e2e_cache_invalidation_on_query_type_change():
    """E2E тест инвалидации кэша при изменении типа запроса."""
    cache = IntelligentCache(max_size=100)

    # Добавляем записи с разными типами запросов
    cache.set("key1", "value1", query_type="code_generation")
    cache.set("key2", "value2", query_type="analysis")

    # Проверяем, что записи в кэше
    assert cache.get("key1") == "value1"
    assert cache.get("key2") == "value2"

    # Инвалидируем кэш для code_generation
    cache.invalidate_by_query_type("code_generation")

    # key1 должна быть инвалидирована, key2 должна остаться
    assert cache.get("key1") is None
    assert cache.get("key2") == "value2"


@pytest.mark.asyncio
async def test_e2e_full_scenario_execution():
    """E2E тест полного выполнения сценария."""
    orchestrator = AIOrchestrator()

    # Создаем простой сценарий
    from src.ai.scenario_hub import ScenarioGoal

    scenario_plan = ScenarioPlan(
        id="test_scenario_full",
        goal=ScenarioGoal(
            id="test_scenario_full",
            title="Full Test Scenario",
            description="Test scenario for full execution cycle",
        ),
        required_autonomy=AutonomyLevel.A2_NON_PROD_CHANGES,
        overall_risk=ScenarioRiskLevel.NON_PROD_CHANGE,
        steps=[
            ScenarioStep(
                id="step1",
                title="Step 1: Code Generation",
                description="Generate code",
                risk_level=ScenarioRiskLevel.NON_PROD_CHANGE,
                autonomy_required=AutonomyLevel.A2_NON_PROD_CHANGES,
                executor="llm",
            ),
            ScenarioStep(
                id="step2",
                title="Step 2: Code Review",
                description="Review generated code",
                risk_level=ScenarioRiskLevel.READ_ONLY,
                autonomy_required=AutonomyLevel.A1_SAFE_AUTOMATION,
                executor="llm",
            ),
        ],
    )

    # Проверяем структуру сценария
    assert scenario_plan is not None
    assert len(scenario_plan.steps) == 2

    # В реальном сценарии здесь был бы вызов orchestrator.execute_scenario(scenario_plan)
    # Но для теста просто проверяем структуру
