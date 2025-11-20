# [NEXUS IDENTITY] ID: -6677885269777976439 | DATE: 2025-11-19

"""
Tests for ScenarioRecommender and ImpactAnalyzer (scenario_recommender.py).
"""

import pytest

from src.ai.code_graph import InMemoryCodeGraphBackend, Node, NodeKind
from src.ai.scenario_recommender import ImpactAnalyzer, ScenarioRecommender


@pytest.mark.asyncio
async def test_recommend_scenarios() -> None:
    """Тест рекомендации сценариев."""
    backend = InMemoryCodeGraphBackend()
    recommender = ScenarioRecommender(backend)

    # Создать тестовые узлы
    req_node = Node(
        id="ba_requirement:FEATURE001",
        kind=NodeKind.BA_REQUIREMENT,
        display_name="Feature: FEATURE001",
    )
    await backend.upsert_node(req_node)

    # Рекомендовать сценарии
    recommendations = await recommender.recommend_scenarios(
        "Нужно реализовать новую фичу с требованиями",
        max_recommendations=5,
    )

    assert len(recommendations) > 0
    assert all("scenario_id" in r for r in recommendations)
    assert all("relevance_score" in r for r in recommendations)


@pytest.mark.asyncio
async def test_recommend_scenarios_with_graph_nodes() -> None:
    """Тест рекомендации сценариев с известными узлами графа."""
    backend = InMemoryCodeGraphBackend()
    recommender = ScenarioRecommender(backend)

    recommendations = await recommender.recommend_scenarios(
        "Проверить код на безопасность",
        graph_nodes=["module:src/feature.py", "test:test_feature.py"],
        max_recommendations=3,
    )

    assert len(recommendations) > 0
    # Должен быть рекомендован code_review сценарий
    code_review_found = any(
        "code_review" in r.get("scenario_id", "") for r in recommendations
    )
    assert code_review_found


@pytest.mark.asyncio
async def test_infer_task_type() -> None:
    """Тест определения типа задачи."""
    backend = InMemoryCodeGraphBackend()
    recommender = ScenarioRecommender(backend)

    # Тест для BA задачи
    task_type = recommender._infer_task_type(
        "Нужно создать требования для новой фичи", []
    )
    assert task_type == "ba_dev_qa"

    # Тест для code review
    task_type = recommender._infer_task_type("Проверить код на безопасность", [])
    assert task_type == "code_review"

    # Тест для DR
    task_type = recommender._infer_task_type(
        "Проверить готовность к аварийному восстановлению", []
    )
    assert task_type == "dr_rehearsal"


@pytest.mark.asyncio
async def test_analyze_impact() -> None:
    """Тест анализа влияния изменений."""
    backend = InMemoryCodeGraphBackend()
    analyzer = ImpactAnalyzer(backend)

    # Создать тестовые узлы
    module_node = Node(
        id="module:src/feature.py",
        kind=NodeKind.MODULE,
        display_name="Module: feature.py",
    )
    await backend.upsert_node(module_node)

    # Проанализировать влияние
    impact_report = await analyzer.analyze_impact(
        ["module:src/feature.py"],
        max_depth=3,
        include_tests=True,
    )

    assert "affected_nodes" in impact_report
    assert "impact_level" in impact_report
    assert "recommendations" in impact_report
    assert impact_report["impact_level"] in ["none", "low", "medium", "high"]


@pytest.mark.asyncio
async def test_analyze_impact_without_backend() -> None:
    """Тест анализа влияния без backend (graceful degradation)."""
    analyzer = ImpactAnalyzer(None)

    impact_report = await analyzer.analyze_impact(
        ["module:src/feature.py"],
        max_depth=3,
    )

    assert "affected_nodes" in impact_report
    assert impact_report["impact_level"] == "unknown"


@pytest.mark.asyncio
async def test_determine_impact_level() -> None:
    """Тест определения уровня влияния."""
    backend = InMemoryCodeGraphBackend()
    analyzer = ImpactAnalyzer(backend)

    # Низкий уровень
    level = analyzer._determine_impact_level(2, 1)
    assert level == "low"

    # Средний уровень
    level = analyzer._determine_impact_level(5, 3)
    assert level == "medium"

    # Высокий уровень
    level = analyzer._determine_impact_level(10, 5)
    assert level == "high"
