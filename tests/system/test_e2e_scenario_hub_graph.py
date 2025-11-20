# [NEXUS IDENTITY] ID: -629484157201820076 | DATE: 2025-11-19

"""
E2E тесты для Scenario Hub с Unified Change Graph
--------------------------------------------------

Тестирование полного цикла работы Scenario Hub с интеграцией
Unified Change Graph, Scenario Recommender и Impact Analyzer.
"""

import pytest

from src.ai.code_graph import InMemoryCodeGraphBackend, Node, NodeKind
from src.ai.scenario_hub import ScenarioPlan, ScenarioStep, ScenarioRiskLevel
from src.ai.scenario_recommender import ImpactAnalyzer, ScenarioRecommender


@pytest.mark.asyncio
async def test_e2e_scenario_recommendation_with_graph() -> None:
    """
    E2E тест: запрос → поиск узлов графа → рекомендация сценариев.
    """
    # 1. Создать тестовый граф
    backend = InMemoryCodeGraphBackend()

    # Добавить требования
    req_node = Node(
        id="ba_requirement:FEATURE001",
        kind=NodeKind.BA_REQUIREMENT,
        display_name="Feature: FEATURE001",
    )
    await backend.upsert_node(req_node)

    # Добавить модуль
    module_node = Node(
        id="module:src/feature.py",
        kind=NodeKind.MODULE,
        display_name="Module: feature.py",
    )
    await backend.upsert_node(module_node)

    # 2. Создать Scenario Recommender
    recommender = ScenarioRecommender(backend)

    # 3. Получить рекомендации
    recommendations = await recommender.recommend_scenarios(
        "Нужно реализовать новую фичу с требованиями",
        graph_nodes=["ba_requirement:FEATURE001", "module:src/feature.py"],
        max_recommendations=5,
    )

    # 4. Проверить результаты
    assert len(recommendations) > 0
    assert all("scenario_id" in r for r in recommendations)
    assert all("relevance_score" in r for r in recommendations)
    assert all("reason" in r for r in recommendations)

    # Должен быть рекомендован BA→Dev→QA сценарий
    ba_dev_qa_found = any(
        "ba_dev_qa" in r.get("scenario_id", "") for r in recommendations
    )
    assert ba_dev_qa_found


@pytest.mark.asyncio
async def test_e2e_impact_analysis_with_graph() -> None:
    """
    E2E тест: анализ влияния изменений через граф.
    """
    # 1. Создать тестовый граф
    backend = InMemoryCodeGraphBackend()

    # Добавить модуль
    module_node = Node(
        id="module:src/feature.py",
        kind=NodeKind.MODULE,
        display_name="Module: feature.py",
    )
    await backend.upsert_node(module_node)

    # Добавить тесты
    test_node = Node(
        id="test:test_feature.py",
        kind=NodeKind.TEST,
        display_name="Test: test_feature.py",
    )
    await backend.upsert_node(test_node)

    # 2. Создать Impact Analyzer
    analyzer = ImpactAnalyzer(backend)

    # 3. Проанализировать влияние
    impact_report = await analyzer.analyze_impact(
        ["module:src/feature.py"],
        max_depth=3,
        include_tests=True,
    )

    # 4. Проверить результаты
    assert "affected_nodes" in impact_report
    assert "impact_level" in impact_report
    assert "recommendations" in impact_report
    assert impact_report["impact_level"] in ["none", "low", "medium", "high"]
    assert len(impact_report["recommendations"]) > 0


@pytest.mark.asyncio
async def test_e2e_scenario_plan_with_graph_refs() -> None:
    """
    E2E тест: создание Scenario Plan с автоматическими graph_refs.
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

    module_node = Node(
        id="module:src/feature.py",
        kind=NodeKind.MODULE,
        display_name="Module: feature.py",
    )
    await backend.upsert_node(module_node)

    # 2. Создать Scenario Plan с graph_refs
    from src.ai.graph_refs_builder import GraphRefsBuilder

    builder = GraphRefsBuilder(backend)

    # Найти релевантные узлы
    graph_refs = await builder.find_refs_by_keywords(
        ["feature", "requirement"],
        max_results=5,
    )

    # 3. Создать Scenario Plan
    plan = ScenarioPlan(
        goal="Реализовать новую фичу",
        steps=[
            ScenarioStep(
                id="step1",
                description="Анализ требований",
                metadata={"graph_refs": graph_refs},
            ),
            ScenarioStep(
                id="step2",
                description="Разработка кода",
                metadata={"graph_refs": graph_refs},
            ),
        ],
        risk_level=ScenarioRiskLevel.MEDIUM,
    )

    # 4. Проверить, что graph_refs присутствуют
    assert len(plan.steps) > 0
    assert all("graph_refs" in (step.metadata or {}) for step in plan.steps)


@pytest.mark.asyncio
async def test_e2e_orchestrator_with_scenario_recommendation() -> None:
    """
    E2E тест: Orchestrator → Scenario Recommender → ответ с рекомендациями.
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

    # 2. Импортировать и инициализировать Orchestrator
    from src.ai.orchestrator import AIOrchestrator

    orchestrator = AIOrchestrator()

    # Установить graph_helper с нашим тестовым backend
    if orchestrator.graph_helper:
        orchestrator.graph_helper.set_backend(backend)

    # 3. Отправить запрос
    query = "Нужно реализовать новую фичу с требованиями"
    response = await orchestrator.process_query(query, {})

    # 4. Проверить, что в ответе есть recommended scenarios
    assert "_meta" in response
    meta = response["_meta"]
    assert "suggested_scenarios" in meta or "graph_nodes_touched" in meta

    # Если есть suggested_scenarios, проверить их структуру
    if "suggested_scenarios" in meta:
        scenarios = meta["suggested_scenarios"]
        if scenarios:
            assert all("scenario_id" in s for s in scenarios)
            assert all("relevance_score" in s for s in scenarios)
