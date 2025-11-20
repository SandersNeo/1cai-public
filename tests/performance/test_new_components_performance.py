# [NEXUS IDENTITY] ID: 5174014620627342422 | DATE: 2025-11-19

"""
Performance Benchmarks для новых компонентов
--------------------------------------------

Тестирование производительности:
- Scenario Recommender
- LLM Provider Abstraction
- Intelligent Cache
"""

import statistics
import time
from typing import List

import pytest

from src.ai.code_graph import InMemoryCodeGraphBackend, Node, NodeKind
from src.ai.intelligent_cache import IntelligentCache
from src.ai.llm_provider_abstraction import LLMProviderAbstraction, QueryType
from src.ai.scenario_recommender import ImpactAnalyzer, ScenarioRecommender


@pytest.mark.asyncio
async def test_performance_scenario_recommender_small_graph() -> None:
    """
    Benchmark: Scenario Recommender с небольшим графом (100 узлов).

    Target: < 50ms для рекомендации
    """
    # 1. Создать небольшой граф (100 узлов)
    backend = InMemoryCodeGraphBackend()

    for i in range(100):
        node = Node(
            id=f"node:{i}",
            kind=NodeKind.MODULE if i % 2 == 0 else NodeKind.BA_REQUIREMENT,
            display_name=f"Node {i}",
        )
        await backend.upsert_node(node)

    # 2. Создать Scenario Recommender
    recommender = ScenarioRecommender(backend)

    # 3. Измерить время рекомендации
    latencies: List[float] = []

    for _ in range(50):
        start = time.time()
        recommendations = await recommender.recommend_scenarios(
            "Нужно реализовать новую фичу",
            graph_nodes=[f"node:{i}" for i in range(10)],
            max_recommendations=5,
        )
        latency_ms = (time.time() - start) * 1000
        latencies.append(latency_ms)
        assert len(recommendations) > 0

    # 4. Вычислить метрики
    p50 = statistics.median(latencies)
    p95 = (
        statistics.quantiles(latencies, n=20)[18]
        if len(latencies) >= 20
        else latencies[-1]
    )
    p99 = (
        statistics.quantiles(latencies, n=100)[98]
        if len(latencies) >= 100
        else latencies[-1]
    )

    print("\nScenario Recommender (small graph, 100 nodes):")
    print(f"  p50: {p50:.2f}ms")
    print(f"  p95: {p95:.2f}ms")
    print(f"  p99: {p99:.2f}ms")

    assert p95 < 50, f"p95 latency too high: {p95:.2f}ms"


@pytest.mark.asyncio
async def test_performance_scenario_recommender_large_graph() -> None:
    """
    Benchmark: Scenario Recommender с большим графом (1000 узлов).

    Target: < 200ms для рекомендации
    """
    # 1. Создать большой граф (1000 узлов)
    backend = InMemoryCodeGraphBackend()

    for i in range(1000):
        node = Node(
            id=f"node:{i}",
            kind=NodeKind.MODULE if i % 2 == 0 else NodeKind.BA_REQUIREMENT,
            display_name=f"Node {i}",
        )
        await backend.upsert_node(node)

    # 2. Создать Scenario Recommender
    recommender = ScenarioRecommender(backend)

    # 3. Измерить время рекомендации
    latencies: List[float] = []

    for _ in range(20):
        start = time.time()
        recommendations = await recommender.recommend_scenarios(
            "Нужно реализовать новую фичу",
            graph_nodes=[f"node:{i}" for i in range(50)],
            max_recommendations=5,
        )
        latency_ms = (time.time() - start) * 1000
        latencies.append(latency_ms)
        assert len(recommendations) > 0

    # 4. Вычислить метрики
    p50 = statistics.median(latencies)
    p95 = (
        statistics.quantiles(latencies, n=20)[18]
        if len(latencies) >= 20
        else latencies[-1]
    )
    p99 = (
        statistics.quantiles(latencies, n=100)[98]
        if len(latencies) >= 100
        else latencies[-1]
    )

    print("\nScenario Recommender (large graph, 1000 nodes):")
    print(f"  p50: {p50:.2f}ms")
    print(f"  p95: {p95:.2f}ms")
    print(f"  p99: {p99:.2f}ms")

    assert p95 < 200, f"p95 latency too high: {p95:.2f}ms"


@pytest.mark.asyncio
async def test_performance_impact_analyzer() -> None:
    """
    Benchmark: Impact Analyzer с различными размерами графа.

    Target: < 100ms для анализа влияния
    """
    # 1. Создать граф
    backend = InMemoryCodeGraphBackend()

    for i in range(500):
        node = Node(
            id=f"node:{i}",
            kind=(
                NodeKind.MODULE
                if i % 3 == 0
                else NodeKind.TEST if i % 3 == 1 else NodeKind.BA_REQUIREMENT
            ),
            display_name=f"Node {i}",
        )
        await backend.upsert_node(node)

    # 2. Создать Impact Analyzer
    analyzer = ImpactAnalyzer(backend)

    # 3. Измерить время анализа
    latencies: List[float] = []

    for _ in range(30):
        start = time.time()
        impact_report = await analyzer.analyze_impact(
            ["node:0", "node:1", "node:2"],
            max_depth=3,
            include_tests=True,
        )
        latency_ms = (time.time() - start) * 1000
        latencies.append(latency_ms)
        assert "affected_nodes" in impact_report

    # 4. Вычислить метрики
    p50 = statistics.median(latencies)
    p95 = (
        statistics.quantiles(latencies, n=20)[18]
        if len(latencies) >= 20
        else latencies[-1]
    )
    p99 = (
        statistics.quantiles(latencies, n=100)[98]
        if len(latencies) >= 100
        else latencies[-1]
    )

    print("\nImpact Analyzer (500 nodes):")
    print(f"  p50: {p50:.2f}ms")
    print(f"  p95: {p95:.2f}ms")
    print(f"  p99: {p99:.2f}ms")

    assert p95 < 100, f"p95 latency too high: {p95:.2f}ms"


@pytest.mark.asyncio
async def test_performance_llm_provider_selection() -> None:
    """
    Benchmark: LLM Provider Selection.

    Target: < 1ms для выбора провайдера
    """
    # 1. Создать LLM Provider Abstraction
    abstraction = LLMProviderAbstraction()

    # 2. Измерить время выбора
    latencies: List[float] = []

    query_types = [
        QueryType.CODE_GENERATION,
        QueryType.RUSSIAN_TEXT,
        QueryType.REASONING,
        QueryType.GENERAL,
    ]

    for query_type in query_types:
        for _ in range(100):
            start = time.time()
            profile = abstraction.select_provider(query_type)
            latency_ms = (time.time() - start) * 1000
            latencies.append(latency_ms)
            assert profile is not None

    # 3. Вычислить метрики
    p50 = statistics.median(latencies)
    p95 = (
        statistics.quantiles(latencies, n=20)[18]
        if len(latencies) >= 20
        else latencies[-1]
    )
    p99 = (
        statistics.quantiles(latencies, n=100)[98]
        if len(latencies) >= 100
        else latencies[-1]
    )

    print("\nLLM Provider Selection:")
    print(f"  p50: {p50:.4f}ms")
    print(f"  p95: {p95:.4f}ms")
    print(f"  p99: {p99:.4f}ms")

    assert p95 < 1, f"p95 latency too high: {p95:.4f}ms"


@pytest.mark.asyncio
async def test_performance_intelligent_cache_get() -> None:
    """
    Benchmark: Intelligent Cache GET операции.

    Target: < 1ms для cache hit
    """
    # 1. Создать Intelligent Cache
    cache = IntelligentCache(max_size=1000)

    # 2. Заполнить кэш
    for i in range(100):
        cache.set(f"key{i}", f"value{i}")

    # 3. Измерить время GET (cache hit)
    latencies: List[float] = []

    for _ in range(1000):
        start = time.time()
        value = cache.get("key0")
        latency_ms = (time.time() - start) * 1000
        latencies.append(latency_ms)
        assert value == "value0"

    # 4. Вычислить метрики
    p50 = statistics.median(latencies)
    p95 = (
        statistics.quantiles(latencies, n=20)[18]
        if len(latencies) >= 20
        else latencies[-1]
    )
    p99 = (
        statistics.quantiles(latencies, n=100)[98]
        if len(latencies) >= 100
        else latencies[-1]
    )

    print("\nIntelligent Cache GET (cache hit):")
    print(f"  p50: {p50:.4f}ms")
    print(f"  p95: {p95:.4f}ms")
    print(f"  p99: {p99:.4f}ms")

    assert p95 < 1, f"p95 latency too high: {p95:.4f}ms"


@pytest.mark.asyncio
async def test_performance_intelligent_cache_set() -> None:
    """
    Benchmark: Intelligent Cache SET операции.

    Target: < 2ms для SET
    """
    # 1. Создать Intelligent Cache
    cache = IntelligentCache(max_size=1000)

    # 2. Измерить время SET
    latencies: List[float] = []

    for i in range(1000):
        start = time.time()
        cache.set(f"key{i}", f"value{i}")
        latency_ms = (time.time() - start) * 1000
        latencies.append(latency_ms)

    # 3. Вычислить метрики
    p50 = statistics.median(latencies)
    p95 = (
        statistics.quantiles(latencies, n=20)[18]
        if len(latencies) >= 20
        else latencies[-1]
    )
    p99 = (
        statistics.quantiles(latencies, n=100)[98]
        if len(latencies) >= 100
        else latencies[-1]
    )

    print("\nIntelligent Cache SET:")
    print(f"  p50: {p50:.4f}ms")
    print(f"  p95: {p95:.4f}ms")
    print(f"  p99: {p99:.4f}ms")

    assert p95 < 2, f"p95 latency too high: {p95:.4f}ms"


@pytest.mark.asyncio
async def test_performance_intelligent_cache_invalidation() -> None:
    """
    Benchmark: Intelligent Cache инвалидация по тегам.

    Target: < 10ms для инвалидации 100 записей
    """
    # 1. Создать Intelligent Cache
    cache = IntelligentCache(max_size=1000)

    # 2. Заполнить кэш с тегами
    for i in range(100):
        cache.set(f"key{i}", f"value{i}", tags={"tag1" if i % 2 == 0 else "tag2"})

    # 3. Измерить время инвалидации
    latencies: List[float] = []

    for _ in range(50):
        start = time.time()
        count = cache.invalidate_by_tags({"tag1"})
        latency_ms = (time.time() - start) * 1000
        latencies.append(latency_ms)
        assert count == 50  # Половина записей с tag1

        # Восстановить для следующей итерации
        for i in range(100):
            cache.set(f"key{i}", f"value{i}", tags={"tag1" if i % 2 == 0 else "tag2"})

    # 4. Вычислить метрики
    p50 = statistics.median(latencies)
    p95 = (
        statistics.quantiles(latencies, n=20)[18]
        if len(latencies) >= 20
        else latencies[-1]
    )
    p99 = (
        statistics.quantiles(latencies, n=100)[98]
        if len(latencies) >= 100
        else latencies[-1]
    )

    print("\nIntelligent Cache Invalidation (by tags, 100 entries):")
    print(f"  p50: {p50:.4f}ms")
    print(f"  p95: {p95:.4f}ms")
    print(f"  p99: {p99:.4f}ms")

    assert p95 < 10, f"p95 latency too high: {p95:.4f}ms"


@pytest.mark.asyncio
async def test_performance_intelligent_cache_lru_eviction() -> None:
    """
    Benchmark: Intelligent Cache LRU eviction при переполнении.

    Target: < 5ms для eviction при переполнении
    """
    # 1. Создать небольшой кэш
    cache = IntelligentCache(max_size=100)

    # 2. Заполнить кэш до предела
    for i in range(100):
        cache.set(f"key{i}", f"value{i}")

    # 3. Измерить время eviction при добавлении нового элемента
    latencies: List[float] = []

    for i in range(100, 200):
        start = time.time()
        cache.set(f"key{i}", f"value{i}")
        latency_ms = (time.time() - start) * 1000
        latencies.append(latency_ms)

    # 4. Вычислить метрики
    p50 = statistics.median(latencies)
    p95 = (
        statistics.quantiles(latencies, n=20)[18]
        if len(latencies) >= 20
        else latencies[-1]
    )
    p99 = (
        statistics.quantiles(latencies, n=100)[98]
        if len(latencies) >= 100
        else latencies[-1]
    )

    print("\nIntelligent Cache LRU Eviction (overflow):")
    print(f"  p50: {p50:.4f}ms")
    print(f"  p95: {p95:.4f}ms")
    print(f"  p99: {p99:.4f}ms")

    assert p95 < 5, f"p95 latency too high: {p95:.4f}ms"


@pytest.mark.asyncio
async def test_performance_intelligent_cache_concurrent_access() -> None:
    """
    Benchmark: Intelligent Cache конкурентный доступ.

    Target: < 5ms для конкурентных операций
    """
    import asyncio

    # 1. Создать Intelligent Cache
    cache = IntelligentCache(max_size=1000)

    # 2. Заполнить кэш
    for i in range(100):
        cache.set(f"key{i}", f"value{i}")

    # 3. Конкурентные операции
    async def concurrent_get(key: str) -> float:
        start = time.time()
        cache.get(key)
        return (time.time() - start) * 1000

    async def concurrent_set(key: str, value: str) -> float:
        start = time.time()
        cache.set(key, value)
        return (time.time() - start) * 1000

    # 4. Запустить конкурентные операции
    tasks = []
    for i in range(200):
        if i % 2 == 0:
            tasks.append(concurrent_get(f"key{i % 100}"))
        else:
            tasks.append(concurrent_set(f"newkey{i}", f"newvalue{i}"))

    latencies = await asyncio.gather(*tasks)

    # 5. Вычислить метрики
    p50 = statistics.median(latencies)
    p95 = (
        statistics.quantiles(latencies, n=20)[18]
        if len(latencies) >= 20
        else latencies[-1]
    )
    p99 = (
        statistics.quantiles(latencies, n=100)[98]
        if len(latencies) >= 100
        else latencies[-1]
    )

    print("\nIntelligent Cache Concurrent Access (200 operations):")
    print(f"  p50: {p50:.4f}ms")
    print(f"  p95: {p95:.4f}ms")
    print(f"  p99: {p99:.4f}ms")

    assert p95 < 5, f"p95 latency too high: {p95:.4f}ms"
