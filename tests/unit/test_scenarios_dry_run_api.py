# [NEXUS IDENTITY] ID: -7205633061486018285 | DATE: 2025-11-19

"""
Тесты для endpoint /api/scenarios/dry-run (экспериментальный).
"""

from fastapi.testclient import TestClient

from src.ai.orchestrator import app


client = TestClient(app)


def test_dry_run_playbook_endpoint_success() -> None:
    """Должен возвращать report для существующего плейбука."""
    response = client.get(
        "/api/scenarios/dry-run",
        params={
            "path": "playbooks/ba_dev_qa_example.yaml",
            "autonomy": "A2_non_prod_changes",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "report" in data
    report = data["report"]
    assert report.get("scenario_id") == "plan-ba-dev-qa-DEMO_FEATURE"
    assert "summary" in report
    assert isinstance(report.get("timeline"), list)
    # Unified Change Graph: поле graph_nodes_touched присутствует
    assert "graph_nodes_touched" in report
    assert isinstance(report["graph_nodes_touched"], list)


def test_dry_run_playbook_endpoint_not_found() -> None:
    """Для несуществующего файла должен возвращаться 404."""
    response = client.get(
        "/api/scenarios/dry-run",
        params={"path": "playbooks/does_not_exist.yaml"},
    )
    assert response.status_code == 404
    assert "Playbook not found" in response.json()["detail"]
