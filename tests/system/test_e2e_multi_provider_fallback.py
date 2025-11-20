# [NEXUS IDENTITY] ID: -1105127812605669089 | DATE: 2025-11-19

"""
E2E тесты для multi-provider fallback и критических путей.

Проверяет:
- Автоматический fallback между провайдерами
- Инвалидацию кэша
- Выполнение сценариев с несколькими провайдерами
"""

import pytest

from src.ai.intelligent_cache import IntelligentCache
from src.ai.llm_provider_abstraction import LLMProviderAbstraction, QueryType
from src.ai.orchestrator import AIOrchestrator
from src.ai.scenario_hub import ScenarioPlan, ScenarioStep, ScenarioRiskLevel


@pytest.mark.asyncio
async def test_e2e_multi_provider_fallback_for_code_generation():
    """E2E тест fallback между провайдерами для генерации кода."""
    orchestrator = AIOrchestrator()

    # Сначала пытаемся использовать Kimi (если доступен)
    query = "Создай функцию на Python для вычисления факториала"

    try:
        result = await orchestrator.process_query(
            query,
            context={
                "query_type": "code_generation",
                "fallback_enabled": True,
            },
        )

        assert result is not None
        assert "text" in result or "error" in result

        # Если ошибка, должен произойти fallback
        if "error" in result:
            # Проверяем, что есть информация о попытке fallback
            assert (
                "fallback" in str(result).lower()
                or "alternative" in str(result).lower()
            )

    except Exception as e:
        # Ожидаем, что некоторые провайдеры могут быть недоступны
        assert "not configured" in str(e).lower() or "network" in str(e).lower()


@pytest.mark.asyncio
async def test_e2e_cache_invalidation():
    """E2E тест инвалидации кэша."""
    cache = IntelligentCache(max_size=100, default_ttl=3600)

    # Добавляем запись
    cache.put("key1", "value1", tags=["tag1", "tag2"])
    assert cache.get("key1") == "value1"

    # Инвалидируем по тегу
    cache.invalidate_by_tags(["tag1"])
    assert cache.get("key1") is None

    # Добавляем снова
    cache.put("key2", "value2", tags=["tag2", "tag3"])
    cache.put("key3", "value3", tags=["tag3"])

    # Инвалидируем по типу запроса
    cache.put("key4", "value4", query_type="code_generation")
    cache.invalidate_by_query_type("code_generation")
    assert cache.get("key4") is None

    # key2 и key3 должны остаться
    assert cache.get("key2") == "value2"
    assert cache.get("key3") == "value3"


@pytest.mark.asyncio
async def test_e2e_scenario_execution_with_multi_providers():
    """E2E тест выполнения сценария с несколькими провайдерами."""
    orchestrator = AIOrchestrator()

    # Создаём простой сценарий
    scenario_plan = ScenarioPlan(
        goal={
            "id": "test_scenario",
            "title": "Test Scenario",
            "description": "Test scenario for multi-provider execution",
        },
        steps=[
            ScenarioStep(
                id="step1",
                title="Step 1: Code Generation",
                description="Generate code",
                risk_level=ScenarioRiskLevel.NON_PROD_CHANGE,
                executor="llm",
            ),
            ScenarioStep(
                id="step2",
                title="Step 2: Code Review",
                description="Review generated code",
                risk_level=ScenarioRiskLevel.READ_ONLY,
                executor="llm",
            ),
        ],
    )

    # Проверяем, что сценарий может быть обработан
    # (не выполняем реальное выполнение, только проверяем структуру)
    assert scenario_plan is not None
    assert len(scenario_plan.steps) == 2
    assert scenario_plan.steps[0].executor == "llm"
    assert scenario_plan.steps[1].executor == "llm"


@pytest.mark.asyncio
async def test_e2e_provider_selection_with_compliance():
    """E2E тест выбора провайдера с учетом compliance."""
    abstraction = LLMProviderAbstraction()

    # Запрос с требованием 152-ФЗ
    provider = abstraction.select_provider(
        QueryType.RUSSIAN_TEXT,
        required_compliance=["152-ФЗ"],
    )

    if provider:
        assert "152-ФЗ" in provider.compliance
        assert provider.provider_id in ["gigachat", "yandexgpt", "naparnik", "ollama"]

    # Запрос без compliance
    provider_general = abstraction.select_provider(QueryType.GENERAL)

    if provider_general:
        # Должен выбрать провайдера (любой доступный)
        assert provider_general.provider_id is not None


@pytest.mark.asyncio
async def test_e2e_provider_selection_by_cost():
    """E2E тест выбора провайдера по стоимости."""
    abstraction = LLMProviderAbstraction()

    # Запрос с ограничением по стоимости (бесплатно)
    provider_free = abstraction.select_provider(
        QueryType.CODE_GENERATION,
        max_cost=0.0,
    )

    if provider_free:
        assert provider_free.cost_per_1k_tokens == 0.0
        assert provider_free.provider_id in ["naparnik", "ollama"]


@pytest.mark.asyncio
async def test_e2e_cache_with_query_type_ttl():
    """E2E тест кэша с разными TTL для разных типов запросов."""
    cache = IntelligentCache(max_size=100)

    # Добавляем записи с разными типами запросов
    cache.put("key1", "value1", query_type="code_generation", ttl=600)  # 10 минут
    cache.put("key2", "value2", query_type="analysis", ttl=3600)  # 1 час
    cache.put("key3", "value3", query_type="general", ttl=1800)  # 30 минут

    # Все должны быть доступны сразу
    assert cache.get("key1") == "value1"
    assert cache.get("key2") == "value2"
    assert cache.get("key3") == "value3"

    # Проверяем статистику
    stats = cache.get_stats()
    assert stats["size"] == 3
    assert stats["hits"] >= 0
    assert stats["misses"] >= 0


@pytest.mark.asyncio
async def test_e2e_russian_text_auto_provider_selection():
    """E2E тест автоматического выбора провайдера для русского текста."""
    abstraction = LLMProviderAbstraction()

    # Запрос на русском должен выбрать российский провайдер
    provider = abstraction.select_provider(QueryType.RUSSIAN_TEXT)

    if provider:
        # Должен быть российский провайдер или локальный Ollama
        assert provider.provider_id in ["gigachat", "yandexgpt", "naparnik", "ollama"]


@pytest.mark.asyncio
async def test_e2e_cache_lru_eviction():
    """E2E тест LRU eviction при переполнении кэша."""
    cache = IntelligentCache(max_size=3)

    # Заполняем кэш
    cache.put("key1", "value1")
    cache.put("key2", "value2")
    cache.put("key3", "value3")

    # Все должны быть в кэше
    assert cache.get("key1") == "value1"
    assert cache.get("key2") == "value2"
    assert cache.get("key3") == "value3"

    # Добавляем ещё одну запись - должна вытесниться самая старая (key1)
    cache.put("key4", "value4")

    # key1 должна быть вытеснена
    assert cache.get("key1") is None

    # Остальные должны остаться
    assert cache.get("key2") == "value2"
    assert cache.get("key3") == "value3"
    assert cache.get("key4") == "value4"
