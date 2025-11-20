# [NEXUS IDENTITY] ID: -1289640793020185127 | DATE: 2025-11-19

"""
Tests for ProcessModellerWithGraph (process_modelling_with_graph.py).
"""

import pytest

from src.ai.agents.process_modelling_with_graph import ProcessModellerWithGraph
from src.ai.code_graph import (Edge, EdgeKind, InMemoryCodeGraphBackend, Node,
                               NodeKind)


@pytest.mark.asyncio
async def test_generate_bpmn_with_graph() -> None:
    """Тест генерации BPMN модели с использованием графа."""
    backend = InMemoryCodeGraphBackend()
    process_modeller = ProcessModellerWithGraph(backend)

    # Создать тестовые узлы
    req_node = Node(
        id="ba_requirement:PROC001",
        kind=NodeKind.BA_REQUIREMENT,
        display_name="Process: PROC001",
    )
    await backend.upsert_node(req_node)

    code_node = Node(
        id="module:src/process.py",
        kind=NodeKind.MODULE,
        display_name="Module: process.py",
    )
    await backend.upsert_node(code_node)

    await backend.upsert_edge(
        Edge(
            source=code_node.id,
            target=req_node.id,
            kind=EdgeKind.IMPLEMENTS,
        )
    )

    # Сгенерировать BPMN
    result = await process_modeller.generate_bpmn_with_graph(
        process_description="Step 1. Start\nStep 2. Process\nStep 3. End",
        requirement_id="PROC001",
        format="mermaid",
    )

    assert "steps" in result
    assert "graph_refs" in result
    assert "diagram" in result
    assert len(result["graph_refs"]) > 0


@pytest.mark.asyncio
async def test_generate_journey_map() -> None:
    """Тест генерации Customer Journey Map."""
    backend = InMemoryCodeGraphBackend()
    process_modeller = ProcessModellerWithGraph(backend)

    # Создать API endpoint
    api_node = Node(
        id="api_endpoint:/api/users",
        kind=NodeKind.API_ENDPOINT,
        display_name="GET /api/users",
    )
    await backend.upsert_node(api_node)

    # Сгенерировать Journey Map
    result = await process_modeller.generate_journey_map(
        journey_description="Customer journey from awareness to purchase",
        format="mermaid",
    )

    assert "stages" in result
    assert "touchpoints" in result
    assert "diagram" in result
    assert len(result["stages"]) > 0


@pytest.mark.asyncio
async def test_validate_process() -> None:
    """Тест валидации модели процесса."""
    backend = InMemoryCodeGraphBackend()
    process_modeller = ProcessModellerWithGraph(backend)

    # Создать модель процесса без владельцев
    process_model = {
        "name": "Test Process",
        "steps": [
            {"id": "step1", "name": "Step 1"},  # Нет owner
            {"id": "step2", "name": "Step 2", "owner": "User"},  # Есть owner
        ],
    }

    # Валидировать
    result = await process_modeller.validate_process(process_model)

    assert "valid" in result
    assert "issues" in result
    assert "warnings" in result
    # Должна быть проблема с отсутствием owner
    assert any(issue["type"] == "missing_owner" for issue in result["issues"])


@pytest.mark.asyncio
async def test_process_modelling_without_backend() -> None:
    """Тест работы без backend (graceful degradation)."""
    process_modeller = ProcessModellerWithGraph(None)

    result = await process_modeller.generate_bpmn_with_graph(
        process_description="Simple process",
        format="mermaid",
    )

    assert "steps" in result
    assert "diagram" in result
    # Без графа graph_refs должны быть пустыми
    assert result.get("graph_refs", []) == []
