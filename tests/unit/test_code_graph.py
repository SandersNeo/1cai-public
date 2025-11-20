# [NEXUS IDENTITY] ID: -5424158410218130697 | DATE: 2025-11-19

"""
Tests for Unified Change Graph (InMemoryCodeGraphBackend).
"""

import pytest

from src.ai.code_graph import Edge, EdgeKind, InMemoryCodeGraphBackend, Node, NodeKind


@pytest.mark.asyncio
async def test_upsert_and_get_node() -> None:
    backend = InMemoryCodeGraphBackend()
    node = Node(
        id="service:ai-orchestrator",
        kind=NodeKind.SERVICE,
        display_name="AI Orchestrator",
        labels=["python", "fastapi"],
        props={"owner": "platform-team"},
    )

    await backend.upsert_node(node)
    loaded = await backend.get_node("service:ai-orchestrator")
    assert loaded is not None
    assert loaded.display_name == "AI Orchestrator"
    assert "python" in loaded.labels


@pytest.mark.asyncio
async def test_neighbors_and_find_nodes() -> None:
    backend = InMemoryCodeGraphBackend()

    service = Node(
        id="service:ai-orchestrator",
        kind=NodeKind.SERVICE,
        display_name="AI Orchestrator",
    )
    alert = Node(
        id="alert:orchestrator-latency-p95-high",
        kind=NodeKind.ALERT,
        display_name="Orchestrator p95 latency high",
        labels=["ai", "latency"],
    )
    test_case = Node(
        id="test_case:test_ai_orchestrator_basic",
        kind=NodeKind.TEST_CASE,
        display_name="test_ai_orchestrator_basic",
        labels=["unit", "orchestrator"],
    )

    await backend.upsert_node(service)
    await backend.upsert_node(alert)
    await backend.upsert_node(test_case)

    await backend.upsert_edge(
        Edge(
            source=service.id,
            target=alert.id,
            kind=EdgeKind.MONITORED_BY,
        )
    )
    await backend.upsert_edge(
        Edge(
            source=service.id,
            target=test_case.id,
            kind=EdgeKind.TESTED_BY,
        )
    )

    neighbors = await backend.neighbors(service.id)
    neighbor_ids = {n.id for n in neighbors}
    assert "alert:orchestrator-latency-p95-high" in neighbor_ids
    assert "test_case:test_ai_orchestrator_basic" in neighbor_ids

    # Фильтрация по типу и лейблу
    latency_alerts = await backend.find_nodes(kind=NodeKind.ALERT, label="latency")
    assert len(latency_alerts) == 1
    assert latency_alerts[0].id == "alert:orchestrator-latency-p95-high"
