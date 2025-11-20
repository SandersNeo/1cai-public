# [NEXUS IDENTITY] ID: -7622878186415183541 | DATE: 2025-11-19

"""
Tests for experimental /api/tools/registry/examples endpoint.
"""

import pytest
from fastapi.testclient import TestClient

from src.ai.orchestrator import app

client = TestClient(app)


@pytest.mark.unit
def test_get_tool_registry_examples_basic_shape():
    """Endpoint должен отдавать список инструментов с ожидаемыми полями."""
    response = client.get("/api/tools/registry/examples")
    assert response.status_code == 200

    data = response.json()
    assert "tools" in data
    assert isinstance(data["tools"], list)
    assert len(data["tools"]) >= 1

    tool = data["tools"][0]
    assert "id" in tool
    assert "display_name" in tool
    assert "category" in tool
    assert "risk" in tool
    assert "endpoints" in tool
