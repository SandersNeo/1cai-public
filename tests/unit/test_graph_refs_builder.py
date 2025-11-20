# [NEXUS IDENTITY] ID: -408764451067444684 | DATE: 2025-11-19

"""
Tests for GraphRefsBuilder (graph_refs_builder.py).
"""

import pytest

from src.ai.code_graph import InMemoryCodeGraphBackend, NodeKind
from src.ai.graph_refs_builder import (GraphRefsBuilder,
                                       build_refs_for_feature,
                                       build_refs_for_service)


def test_build_refs_for_feature() -> None:
    """Тест построения graph_refs для фичи."""
    refs = build_refs_for_feature(
        "DEMO_FEATURE",
        code_paths=["src/ai/orchestrator.py"],
        test_paths=["tests/unit/test_orchestrator.py"],
        doc_paths=["docs/06-features/AI_ORCHESTRATOR_GUIDE.md"],
    )

    assert len(refs) > 0
    # Должен быть BA Requirement узел
    assert any("ba-requirement:DEMO_FEATURE" in ref for ref in refs)
    # Должны быть узлы для кода, тестов и документации
    assert any("orchestrator" in ref.lower() for ref in refs)
    assert any("test" in ref.lower() for ref in refs)


def test_build_refs_for_service() -> None:
    """Тест построения graph_refs для сервиса."""
    refs = build_refs_for_service(
        "ai-orchestrator",
        deployment_path="infrastructure/k8s/orchestrator-deployment.yaml",
        helm_chart_path="infrastructure/helm/orchestrator",
        alert_paths=["monitoring/prometheus/alerts/orchestrator.yml"],
    )

    assert len(refs) > 0
    # Должен быть Service узел
    assert any("service:ai-orchestrator" in ref for ref in refs)
    # Должны быть узлы для deployment, helm chart и alerts
    assert any("deployment" in ref.lower() or "k8s" in ref.lower() for ref in refs)


def test_build_refs_for_module() -> None:
    """Тест построения graph_refs для BSL модуля."""
    builder = GraphRefsBuilder()

    refs = builder.build_refs_for_module(
        "ОбщийМодуль.УправлениеЗаказами",
        functions=["СоздатьЗаказ", "ОбновитьЗаказ"],
    )

    assert len(refs) > 0
    # Должен быть Module узел
    assert any("module:ОбщийМодуль.УправлениеЗаказами" in ref for ref in refs)
    # Должны быть Function узлы
    assert any("СоздатьЗаказ" in ref for ref in refs)
    assert any("ОбновитьЗаказ" in ref for ref in refs)


def test_infer_node_kind() -> None:
    """Тест определения типа узла по пути."""
    builder = GraphRefsBuilder()

    # Python модуль
    assert builder._infer_node_kind("src/ai/orchestrator.py") == NodeKind.MODULE

    # Тест
    assert (
        builder._infer_node_kind("tests/unit/test_orchestrator.py")
        == NodeKind.TEST_CASE
    )

    # K8s deployment
    assert (
        builder._infer_node_kind("infrastructure/k8s/deployment.yaml")
        == NodeKind.K8S_DEPLOYMENT
    )

    # Helm chart
    assert (
        builder._infer_node_kind("infrastructure/helm/chart/values.yaml")
        == NodeKind.HELM_CHART
    )

    # Alert
    assert builder._infer_node_kind("monitoring/alerts.yml") == NodeKind.ALERT

    # Markdown
    assert builder._infer_node_kind("docs/guide.md") == NodeKind.FILE


def test_normalize_path() -> None:
    """Тест нормализации путей."""
    builder = GraphRefsBuilder()

    # Относительный путь (должен остаться как есть, если файл существует)
    # Для теста используем путь, который точно существует
    normalized = builder._normalize_path("src/ai/orchestrator.py")
    assert normalized is not None
    assert "orchestrator" in normalized

    # Несуществующий путь
    normalized = builder._normalize_path("nonexistent/file.py")
    assert normalized is None


def test_build_node_id() -> None:
    """Тест построения ID узла."""
    builder = GraphRefsBuilder()

    # Module узел (расширение должно быть убрано)
    node_id = builder._build_node_id("src/ai/orchestrator.py", NodeKind.MODULE)
    assert "orchestrator" in node_id
    assert ".py" not in node_id

    # K8s deployment (расширение может остаться)
    node_id = builder._build_node_id(
        "infrastructure/k8s/deployment.yaml", NodeKind.K8S_DEPLOYMENT
    )
    assert "deployment" in node_id


@pytest.mark.asyncio
async def test_find_refs_by_keywords() -> None:
    """Тест поиска refs по ключевым словам."""
    backend = InMemoryCodeGraphBackend()
    builder = GraphRefsBuilder(backend)

    # Создать тестовый узел
    test_node = Node(
        id="module:Тест",
        kind=NodeKind.MODULE,
        display_name="Module: Тест",
        labels=["тест"],
    )
    await backend.upsert_node(test_node)

    # Поиск по ключевому слову
    refs = await builder.find_refs_by_keywords(["тест"])
    assert len(refs) > 0
    assert any("module:Тест" in ref for ref in refs)


def test_graph_refs_builder_without_backend() -> None:
    """Тест работы без backend (graceful degradation)."""
    builder = GraphRefsBuilder(None)

    # Построение refs должно работать без backend
    refs = builder.build_refs_for_feature("TEST", code_paths=["src/test.py"])
    assert len(refs) > 0
