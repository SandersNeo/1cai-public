# [NEXUS IDENTITY] ID: -2681129301552104118 | DATE: 2025-11-19

"""
Tests for IntegrationSyncWithGraph (integrations_with_graph.py).
"""

import pytest

from src.ai.code_graph import Edge, EdgeKind, InMemoryCodeGraphBackend, Node, NodeKind
from src.ai.agents.integrations_with_graph import IntegrationSyncWithGraph


@pytest.mark.asyncio
async def test_sync_requirements_to_jira() -> None:
    """Тест синхронизации требований в Jira."""
    backend = InMemoryCodeGraphBackend()
    integration_sync = IntegrationSyncWithGraph(backend)

    # Создать тестовые узлы
    req_node = Node(
        id="ba_requirement:REQ001",
        kind=NodeKind.BA_REQUIREMENT,
        display_name="Requirement: REQ001",
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

    # Синхронизировать требования
    result = await integration_sync.sync_requirements_to_jira(
        ["REQ001"],
        project_key="TEST",
        issue_type="Story",
    )

    assert "synced" in result
    assert len(result["synced"]) > 0
    assert result["synced"][0]["requirement_id"] == "REQ001"
    assert len(result["synced"][0]["code_refs"]) > 0


@pytest.mark.asyncio
async def test_sync_bpmn_to_confluence() -> None:
    """Тест синхронизации BPMN в Confluence."""
    backend = InMemoryCodeGraphBackend()
    integration_sync = IntegrationSyncWithGraph(backend)

    process_model = {
        "name": "Test Process",
        "steps": [{"id": "step1", "name": "Step 1"}],
        "diagram": "graph TD\n    A[Start]",
        "graph_refs": ["ba_requirement:REQ001"],
    }

    result = await integration_sync.sync_bpmn_to_confluence(
        process_model,
        space_key="TEST",
    )

    assert "page_title" in result
    assert "content" in result
    assert "graph_refs" in result


@pytest.mark.asyncio
async def test_sync_kpi_to_confluence() -> None:
    """Тест синхронизации KPI в Confluence."""
    integration_sync = IntegrationSyncWithGraph(None)

    kpi_report = {
        "initiative": "Test Initiative",
        "kpis": [
            {
                "name": "Code Coverage",
                "value": 80,
                "target": 90,
                "unit": "%",
                "category": "technical",
            }
        ],
        "sql_queries": [
            {
                "description": "Test Query",
                "query": "SELECT * FROM test",
            }
        ],
        "visualizations": [],
    }

    result = await integration_sync.sync_kpi_to_confluence(
        kpi_report,
        space_key="TEST",
    )

    assert "page_title" in result
    assert "content" in result
    assert "KPI Report" in result["page_title"]


@pytest.mark.asyncio
async def test_sync_traceability_to_confluence() -> None:
    """Тест синхронизации Traceability в Confluence."""
    integration_sync = IntegrationSyncWithGraph(None)

    traceability_report = {
        "traceability": {
            "matrix": [
                {
                    "requirement_id": "REQ001",
                    "code_nodes": [],
                    "test_nodes": [],
                    "coverage": "full",
                }
            ]
        },
        "risk_register": [
            {
                "requirement_id": "REQ002",
                "risk_level": "high",
                "risk_reasons": ["no_tests"],
            }
        ],
        "risk_heatmap": {"high": 1, "medium": 0, "low": 0},
    }

    result = await integration_sync.sync_traceability_to_confluence(
        traceability_report,
        space_key="TEST",
    )

    assert "page_title" in result
    assert "content" in result
    assert "Traceability" in result["page_title"]


@pytest.mark.asyncio
async def test_integration_sync_without_backend() -> None:
    """Тест работы без backend (graceful degradation)."""
    integration_sync = IntegrationSyncWithGraph(None)

    result = await integration_sync.sync_requirements_to_jira(["REQ001"])

    assert "synced" in result
    assert "errors" in result
    assert len(result["errors"]) > 0
