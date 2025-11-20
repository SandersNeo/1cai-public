# [NEXUS IDENTITY] ID: -4666218792727110957 | DATE: 2025-11-19

"""
Tests for TraceabilityWithGraph (traceability_with_graph.py).
"""

import pytest

from src.ai.agents.traceability_with_graph import TraceabilityWithGraph
from src.ai.code_graph import (Edge, EdgeKind, InMemoryCodeGraphBackend, Node,
                               NodeKind)


@pytest.mark.asyncio
async def test_build_traceability_matrix() -> None:
    """Тест построения traceability matrix с графом."""
    backend = InMemoryCodeGraphBackend()
    traceability = TraceabilityWithGraph(backend)

    # Создать тестовые узлы
    req_node = Node(
        id="ba_requirement:REQ001",
        kind=NodeKind.BA_REQUIREMENT,
        display_name="Requirement: REQ001",
    )
    await backend.upsert_node(req_node)

    code_node = Node(
        id="module:src/ai/orchestrator.py",
        kind=NodeKind.MODULE,
        display_name="Module: orchestrator.py",
    )
    await backend.upsert_node(code_node)

    test_node = Node(
        id="test_case:test_orchestrator",
        kind=NodeKind.TEST_CASE,
        display_name="test_orchestrator",
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

    # Построить матрицу
    result = await traceability.build_traceability_matrix(
        ["REQ001"],
        include_code=True,
        include_tests=True,
    )

    assert "matrix" in result
    assert len(result["matrix"]) > 0
    assert result["matrix"][0]["requirement_id"] == "REQ001"
    assert len(result["matrix"][0]["code_nodes"]) > 0
    assert len(result["matrix"][0]["test_nodes"]) > 0


@pytest.mark.asyncio
async def test_build_risk_register() -> None:
    """Тест построения Risk Register."""
    backend = InMemoryCodeGraphBackend()
    traceability = TraceabilityWithGraph(backend)

    # Создать требование без тестов (высокий риск)
    req_node = Node(
        id="ba_requirement:REQ002",
        kind=NodeKind.BA_REQUIREMENT,
        display_name="Requirement: REQ002",
    )
    await backend.upsert_node(req_node)

    code_node = Node(
        id="module:src/test.py",
        kind=NodeKind.MODULE,
        display_name="Module: test.py",
    )
    await backend.upsert_node(code_node)

    # Связь: код реализует требование, но нет тестов
    await backend.upsert_edge(
        Edge(
            source=code_node.id,
            target=req_node.id,
            kind=EdgeKind.IMPLEMENTS,
        )
    )

    # Построить Risk Register
    result = await traceability.build_risk_register(["REQ002"])

    assert "risk_register" in result
    assert "risk_heatmap" in result
    assert len(result["risk_register"]) > 0
    # Должен быть высокий риск (нет тестов)
    assert any(r["risk_level"] == "high" for r in result["risk_register"])


@pytest.mark.asyncio
async def test_build_full_traceability_report() -> None:
    """Тест построения полного отчёта traceability & compliance."""
    backend = InMemoryCodeGraphBackend()
    traceability = TraceabilityWithGraph(backend)

    # Создать требование с полным покрытием
    req_node = Node(
        id="ba_requirement:REQ003",
        kind=NodeKind.BA_REQUIREMENT,
        display_name="Requirement: REQ003",
    )
    await backend.upsert_node(req_node)

    code_node = Node(
        id="module:src/complete.py",
        kind=NodeKind.MODULE,
        display_name="Module: complete.py",
    )
    await backend.upsert_node(code_node)

    test_node = Node(
        id="test_case:test_complete",
        kind=NodeKind.TEST_CASE,
        display_name="test_complete",
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

    # Построить полный отчёт
    result = await traceability.build_full_traceability_report(["REQ003"])

    assert "traceability" in result
    assert "risk_register" in result
    assert "risk_heatmap" in result
    assert "compliance" in result
    assert result["compliance"]["status"] in [
        "compliant",
        "partially_compliant",
        "non_compliant",
    ]


@pytest.mark.asyncio
async def test_traceability_without_backend() -> None:
    """Тест работы без backend (graceful degradation)."""
    traceability = TraceabilityWithGraph(None)

    result = await traceability.build_traceability_matrix(["REQ004"])
    assert "matrix" in result
    assert len(result["matrix"]) > 0
    # Coverage должен быть "unknown" без графа
    assert result["matrix"][0]["coverage"] == "unknown"
