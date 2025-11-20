# [NEXUS IDENTITY] ID: -7894086034562303994 | DATE: 2025-11-19

"""
Tests for experimental /api/scenarios/examples endpoint.
"""

import pytest
from fastapi.testclient import TestClient

from src.ai.orchestrator import app

client = TestClient(app)


@pytest.mark.unit
def test_get_scenario_examples_basic_shape():
    """Endpoint должен отдавать два сценария с минимально ожидаемой структурой."""
    response = client.get("/api/scenarios/examples")
    assert response.status_code == 200

    data = response.json()
    assert "scenarios" in data
    assert isinstance(data["scenarios"], list)
    assert len(data["scenarios"]) >= 3

    # Проверим один BA→Dev→QA сценарий
    first = data["scenarios"][0]
    assert "id" in first
    assert "goal" in first
    assert "steps" in first
    assert "overall_risk" in first
    assert "required_autonomy" in first
    # Unified Change Graph: витринное поле с узлами
    assert "_graph_nodes_touched" in first
    assert isinstance(first["_graph_nodes_touched"], list)

    # Убедимся, что среди сценариев есть code-review
    ids = {s["id"] for s in data["scenarios"]}
    assert any("code-review" in s_id for s_id in ids)


@pytest.mark.unit
def test_get_scenario_examples_with_autonomy():
    """При передаче autonomy должны появляться policy_decisions."""
    response = client.get(
        "/api/scenarios/examples", params={"autonomy": "A2_non_prod_changes"}
    )
    assert response.status_code == 200

    data = response.json()
    first = data["scenarios"][0]
    assert "policy_decisions" in first
    assert "autonomy_evaluated" in first
    assert isinstance(first["policy_decisions"], dict)
