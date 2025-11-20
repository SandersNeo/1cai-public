# [NEXUS IDENTITY] ID: -6791952097118863005 | DATE: 2025-11-19

import pytest

from src.ai.agents.ras_monitor_complete import RASMonitorComplete


@pytest.mark.asyncio
async def test_analyze_cluster_health_uses_mock_when_ras_unavailable(monkeypatch):
    monitor = RASMonitorComplete(ras_host="invalid-host", ras_port=1545)

    # Принудительно помечаем как отключённый, чтобы пошли в mock‑ветку
    monitor.connected = False

    report = await monitor.analyze_cluster_health(cluster_name="MainCluster")

    assert report["cluster_name"] == "MainCluster"
    assert report["sessions_count"] >= 0
    assert report["locks_count"] >= 0
    assert report["processes_count"] >= 0
    assert report["health_status"] in {"healthy", "warning", "critical"}


@pytest.mark.asyncio
async def test_terminate_session_returns_false_when_not_connected():
    monitor = RASMonitorComplete()
    monitor.connected = False

    result = await monitor.terminate_session("MainCluster", "sess-001")

    assert result is False
