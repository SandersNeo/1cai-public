# [NEXUS IDENTITY] ID: -2009415983217203501 | DATE: 2025-11-19

"""
E2E тесты для BA-функций с Unified Change Graph
------------------------------------------------

Тестирование полного цикла работы BA-функций (BA-03...BA-07)
с интеграцией Unified Change Graph.
"""

import pytest

from src.ai.code_graph import InMemoryCodeGraphBackend, Node, NodeKind


@pytest.mark.asyncio
async def test_e2e_ba_traceability_with_graph() -> None:
    """
    E2E тест: BA-05 Traceability с Unified Change Graph.
    """
    # 1. Создать тестовый граф
    backend = InMemoryCodeGraphBackend()

    # Добавить требования
    req_node = Node(
        id="ba_requirement:REQ001",
        kind=NodeKind.BA_REQUIREMENT,
        display_name="Requirement: REQ001",
    )
    await backend.upsert_node(req_node)

    # Добавить модуль
    module_node = Node(
        id="module:src/feature.py",
        kind=NodeKind.MODULE,
        display_name="Module: feature.py",
    )
    await backend.upsert_node(module_node)

    # Добавить тест
    test_node = Node(
        id="test:test_feature.py",
        kind=NodeKind.TEST,
        display_name="Test: test_feature.py",
    )
    await backend.upsert_node(test_node)

    # 2. Создать TraceabilityWithGraph
    from src.ai.agents.traceability_with_graph import TraceabilityWithGraph

    traceability = TraceabilityWithGraph(backend)

    # 3. Построить traceability matrix
    matrix = await traceability.build_traceability_matrix(
        requirement_ids=["ba_requirement:REQ001"]
    )

    # 4. Проверить результаты
    assert "requirements" in matrix
    assert "coverage" in matrix


@pytest.mark.asyncio
async def test_e2e_ba_kpi_with_graph() -> None:
    """
    E2E тест: BA-04 Analytics & KPI с Unified Change Graph.
    """
    # 1. Создать тестовый граф
    backend = InMemoryCodeGraphBackend()

    # Добавить узлы
    req_node = Node(
        id="ba_requirement:REQ001",
        kind=NodeKind.BA_REQUIREMENT,
        display_name="Requirement: REQ001",
    )
    await backend.upsert_node(req_node)

    module_node = Node(
        id="module:src/feature.py",
        kind=NodeKind.MODULE,
        display_name="Module: feature.py",
    )
    await backend.upsert_node(module_node)

    # 2. Создать KPIGeneratorWithGraph
    from src.ai.agents.analytics_kpi_with_graph import KPIGeneratorWithGraph

    kpi_generator = KPIGeneratorWithGraph(backend)

    # 3. Сгенерировать KPI
    kpis = await kpi_generator.generate_kpis_from_graph(feature_name="Test Feature")

    # 4. Проверить результаты
    assert "technical_kpis" in kpis
    assert "business_kpis" in kpis
    assert len(kpis["technical_kpis"]) > 0


@pytest.mark.asyncio
async def test_e2e_ba_process_modelling_with_graph() -> None:
    """
    E2E тест: BA-03 Process Modelling с Unified Change Graph.
    """
    # 1. Создать тестовый граф
    backend = InMemoryCodeGraphBackend()

    # Добавить узлы
    req_node = Node(
        id="ba_requirement:REQ001",
        kind=NodeKind.BA_REQUIREMENT,
        display_name="Requirement: REQ001",
    )
    await backend.upsert_node(req_node)

    # 2. Создать ProcessModellerWithGraph
    from src.ai.agents.process_modelling_with_graph import ProcessModellerWithGraph

    process_modeller = ProcessModellerWithGraph(backend)

    # 3. Сгенерировать BPMN модель
    bpmn = await process_modeller.generate_bpmn_with_graph(
        process_description="Test process",
        format="mermaid",
    )

    # 4. Проверить результаты
    assert "bpmn_model" in bpmn
    assert "graph_links" in bpmn


@pytest.mark.asyncio
async def test_e2e_ba_enablement_with_graph() -> None:
    """
    E2E тест: BA-07 Enablement с Unified Change Graph.
    """
    # 1. Создать тестовый граф
    backend = InMemoryCodeGraphBackend()

    # Добавить узлы
    req_node = Node(
        id="ba_requirement:FEATURE001",
        kind=NodeKind.BA_REQUIREMENT,
        display_name="Feature: FEATURE001",
    )
    await backend.upsert_node(req_node)

    # 2. Создать EnablementGeneratorWithGraph
    from src.ai.agents.enablement_with_graph import EnablementGeneratorWithGraph

    enablement_generator = EnablementGeneratorWithGraph(backend)

    # 3. Сгенерировать enablement plan
    plan = await enablement_generator.generate_enablement_plan(
        "Test Feature",
        audience="BA+Dev+QA",
        include_examples=True,
        use_graph=True,
    )

    # 4. Проверить результаты
    assert "modules" in plan
    assert "feature_name" in plan
    assert len(plan["modules"]) > 0
