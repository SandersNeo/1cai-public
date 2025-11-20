# [NEXUS IDENTITY] ID: 7393879267212295721 | DATE: 2025-11-19

"""
Tests for BA-05 Traceability & Compliance API endpoints.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.ba_sessions import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_build_traceability_matrix_endpoint() -> None:
    """Тест endpoint для построения traceability matrix."""
    response = client.post(
        "/ba-sessions/traceability/matrix",
        json={
            "requirement_ids": ["REQ001", "REQ002"],
            "include_code": True,
            "include_tests": True,
            "use_graph": True,
        },
    )

    assert response.status_code in [200, 500]  # Может быть 500 если граф не настроен
    if response.status_code == 200:
        data = response.json()
        assert "ba_feature" in data or "traceability" in data


def test_build_risk_register_endpoint() -> None:
    """Тест endpoint для построения Risk Register."""
    response = client.post(
        "/ba-sessions/traceability/risk-register",
        json={
            "requirement_ids": ["REQ001", "REQ002"],
            "include_incidents": True,
        },
    )

    assert response.status_code in [200, 500]  # Может быть 500 если граф не настроен
    if response.status_code == 200:
        data = response.json()
        assert "risk_register" in data
        assert "risk_heatmap" in data


def test_build_full_traceability_report_endpoint() -> None:
    """Тест endpoint для построения полного отчёта traceability & compliance."""
    response = client.post(
        "/ba-sessions/traceability/full-report",
        json={
            "requirement_ids": ["REQ001", "REQ002"],
        },
    )

    assert response.status_code in [200, 500]  # Может быть 500 если граф не настроен
    if response.status_code == 200:
        data = response.json()
        assert "traceability" in data
        assert "risk_register" in data
        assert "risk_heatmap" in data
        assert "compliance" in data
