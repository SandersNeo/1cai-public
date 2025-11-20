# [NEXUS IDENTITY] ID: -8524025343121146606 | DATE: 2025-11-19

"""
E2E тесты для Intelligent Cache
--------------------------------

Тестирование полного цикла работы Intelligent Cache
с Orchestrator и различными типами запросов.
"""

import pytest

from src.ai.intelligent_cache import IntelligentCache
from src.ai.orchestrator import AIOrchestrator


@pytest.mark.asyncio
async def test_e2e_cache_with_orchestrator() -> None:
    """
    E2E тест: Orchestrator использует Intelligent Cache.
    """
    # 1. Создать Orchestrator (должен автоматически инициализировать Intelligent Cache)
    orchestrator = AIOrchestrator()

    # 2. Проверить, что кэш инициализирован
    assert orchestrator.cache is not None

    # 3. Отправить запрос
    query = "Как создать функцию в 1С?"
    response1 = await orchestrator.process_query(query, {})

    # 4. Отправить тот же запрос снова (должен быть cache hit)
    response2 = await orchestrator.process_query(query, {})

    # 5. Проверить, что ответы одинаковые (если кэш работает)
    if isinstance(orchestrator.cache, dict):
        # Простой dict кэш
        assert response1 == response2
    else:
        # IntelligentCache
        assert response1 == response2

        # Проверить метрики кэша
        metrics = orchestrator.cache.get_metrics()
        assert metrics["hits"] >= 1
        assert metrics["hit_rate"] > 0


@pytest.mark.asyncio
async def test_e2e_cache_ttl_by_query_type() -> None:
    """
    E2E тест: TTL кэша зависит от типа запроса.
    """
    # 1. Создать Intelligent Cache
    cache = IntelligentCache(max_size=100, default_ttl_seconds=300)

    # 2. Сохранить запрос с типом code_generation (TTL 10 минут)
    cache.set(
        "Создай функцию",
        {"result": "function code"},
        query_type="code_generation",
    )

    # 3. Проверить, что запись сохранена
    value = cache.get("Создай функцию")
    assert value is not None
    assert value["result"] == "function code"

    # 4. Проверить, что TTL установлен правильно
    key = cache._generate_key("Создай функцию")
    entry = cache._cache[key]
    assert entry.query_type == "code_generation"
    assert entry.expires_at is not None


@pytest.mark.asyncio
async def test_e2e_cache_invalidation_by_tags() -> None:
    """
    E2E тест: инвалидация кэша по тегам.
    """
    # 1. Создать Intelligent Cache
    cache = IntelligentCache(max_size=100)

    # 2. Сохранить несколько записей с разными тегами
    cache.set("query1", "value1", tags={"orchestrator", "ai_query"})
    cache.set("query2", "value2", tags={"orchestrator"})
    cache.set("query3", "value3", tags={"other"})

    # 3. Инвалидировать по тегу orchestrator
    count = cache.invalidate_by_tags({"orchestrator"})

    # 4. Проверить результаты
    assert count == 2  # query1 и query2 должны быть удалены
    assert cache.get("query1") is None
    assert cache.get("query2") is None
    assert cache.get("query3") == "value3"  # query3 должен остаться


@pytest.mark.asyncio
async def test_e2e_cache_invalidation_by_query_type() -> None:
    """
    E2E тест: инвалидация кэша по типу запроса.
    """
    # 1. Создать Intelligent Cache
    cache = IntelligentCache(max_size=100)

    # 2. Сохранить несколько записей с разными типами запросов
    cache.set("query1", "value1", query_type="code_generation")
    cache.set("query2", "value2", query_type="reasoning")
    cache.set("query3", "value3", query_type="code_generation")

    # 3. Инвалидировать по типу code_generation
    count = cache.invalidate_by_query_type("code_generation")

    # 4. Проверить результаты
    assert count == 2  # query1 и query3 должны быть удалены
    assert cache.get("query1") is None
    assert cache.get("query2") == "value2"  # query2 должен остаться
    assert cache.get("query3") is None


@pytest.mark.asyncio
async def test_e2e_cache_metrics_tracking() -> None:
    """
    E2E тест: отслеживание метрик кэша.
    """
    # 1. Создать Intelligent Cache
    cache = IntelligentCache(max_size=100)

    # 2. Сделать несколько операций
    cache.set("query1", "value1")
    cache.get("query1")  # hit
    cache.get("query2")  # miss
    cache.get("query1")  # hit

    # 3. Получить метрики
    metrics = cache.get_metrics()

    # 4. Проверить результаты
    assert metrics["hits"] == 2
    assert metrics["misses"] == 1
    assert metrics["hit_rate"] == 2 / 3
    assert metrics["size"] == 1
    assert metrics["max_size"] == 100


@pytest.mark.asyncio
async def test_e2e_cache_lru_eviction() -> None:
    """
    E2E тест: LRU eviction при переполнении кэша.
    """
    # 1. Создать небольшой кэш
    cache = IntelligentCache(max_size=3)

    # 2. Заполнить кэш
    cache.set("query1", "value1")
    cache.set("query2", "value2")
    cache.set("query3", "value3")

    # 3. Добавить ещё один запрос (должен вытеснить самый старый)
    cache.set("query4", "value4")

    # 4. Проверить, что query1 удалён (самый старый)
    assert cache.get("query1") is None
    assert cache.get("query2") == "value2"
    assert cache.get("query3") == "value3"
    assert cache.get("query4") == "value4"

    # 5. Проверить метрики eviction
    metrics = cache.get_metrics()
    assert metrics["evictions"] >= 1
