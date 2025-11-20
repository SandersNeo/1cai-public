# [NEXUS IDENTITY] ID: 1955752185931703533 | DATE: 2025-11-19

"""
Tests for KPIGeneratorWithGraph (analytics_kpi_with_graph.py).
"""

import pytest

from src.ai.agents.analytics_kpi_with_graph import KPIGeneratorWithGraph
from src.ai.code_graph import (Edge, EdgeKind, InMemoryCodeGraphBackend, Node,
                               NodeKind)


@pytest.mark.asyncio
async def test_generate_kpis_from_graph() -> None:
    """Тест генерации KPI с использованием графа."""
    backend = InMemoryCodeGraphBackend()
    kpi_generator = KPIGeneratorWithGraph(backend)

    # Создать тестовые узлы
    req_node = Node(
        id="ba_requirement:FEATURE001",
        kind=NodeKind.BA_REQUIREMENT,
        display_name="Feature: FEATURE001",
    )
    await backend.upsert_node(req_node)

    code_node = Node(
        id="module:src/feature.py",
        kind=NodeKind.MODULE,
        display_name="Module: feature.py",
    )
    await backend.upsert_node(code_node)

    test_node = Node(
        id="test_case:test_feature",
        kind=NodeKind.TEST_CASE,
        display_name="test_feature",
    )
    await backend.upsert_node(test_node)

    # Создать связи
    await backend.upsert_edge(
        Edge(
            source=code_node.id,
            target=req_node.id,
            kind=EdgeKind.IMPLEMENTS,
        )
    )
    await backend.upsert_edge(
        Edge(
            source=test_node.id,
            target=code_node.id,
            kind=EdgeKind.TESTED_BY,
        )
    )

    # Сгенерировать KPI
    result = await kpi_generator.generate_kpis_from_graph(
        feature_id="FEATURE001",
        include_technical=True,
        include_business=True,
    )

    assert "kpis" in result
    assert "sql_queries" in result
    assert "visualizations" in result
    assert len(result["kpis"]) > 0


@pytest.mark.asyncio
async def test_technical_kpis() -> None:
    """Тест построения технических KPI."""
    backend = InMemoryCodeGraphBackend()
    kpi_generator = KPIGeneratorWithGraph(backend)

    # Создать модули и тесты
    module1 = Node(
        id="module:src/module1.py",
        kind=NodeKind.MODULE,
        display_name="Module 1",
    )
    await backend.upsert_node(module1)

    test1 = Node(
        id="test_case:test_module1",
        kind=NodeKind.TEST_CASE,
        display_name="test_module1",
    )
    await backend.upsert_node(test1)

    await backend.upsert_edge(
        Edge(
            source=test1.id,
            target=module1.id,
            kind=EdgeKind.TESTED_BY,
        )
    )

    # Построить технические KPI
    kpis = await kpi_generator._build_technical_kpis()

    assert len(kpis) > 0
    # Должен быть Test Coverage KPI
    assert any(kpi["id"] == "kpi_test_coverage" for kpi in kpis)


@pytest.mark.asyncio
async def test_sql_queries_generation() -> None:
    """Тест генерации SQL-запросов для KPI."""
    backend = InMemoryCodeGraphBackend()
    kpi_generator = KPIGeneratorWithGraph(backend)

    # Создать KPI
    kpis = [
        {
            "id": "kpi_code_coverage",
            "name": "Code Coverage",
            "category": "technical",
        },
        {
            "id": "kpi_revenue_impact",
            "name": "Revenue Impact",
            "category": "business",
        },
    ]

    # Сгенерировать SQL-запросы
    queries = await kpi_generator._generate_sql_queries(kpis, feature_id="FEATURE001")

    assert len(queries) > 0
    # Должен быть SQL для технического KPI
    assert any("query" in q for q in queries)


@pytest.mark.asyncio
async def test_visualizations_generation() -> None:
    """Тест генерации рекомендаций по визуализациям."""
    kpi_generator = KPIGeneratorWithGraph(None)

    kpis = [
        {
            "id": "kpi_code_coverage",
            "name": "Code Coverage",
            "category": "technical",
            "description": "Test coverage",
        },
        {
            "id": "kpi_revenue_impact",
            "name": "Revenue Impact",
            "category": "business",
            "description": "Revenue",
        },
    ]

    visualizations = kpi_generator._generate_visualizations(kpis)

    assert len(visualizations) == len(kpis)
    assert all("type" in viz for viz in visualizations)
    assert all("recommended_tool" in viz for viz in visualizations)


@pytest.mark.asyncio
async def test_kpi_generation_without_backend() -> None:
    """Тест работы без backend (graceful degradation)."""
    kpi_generator = KPIGeneratorWithGraph(None)

    result = await kpi_generator.generate_kpis_from_graph()

    assert "kpis" in result
    assert "sql_queries" in result
    assert "visualizations" in result
    # Должны быть шаблонные KPI
    assert len(result["kpis"]) > 0
