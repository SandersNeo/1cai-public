# [NEXUS IDENTITY] ID: 2070332358772139552 | DATE: 2025-11-19

import json
from contextlib import contextmanager

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.ba_sessions import router as ba_sessions_router
from src.monitoring.prometheus_metrics import (
    ba_ws_active_participants,
    ba_ws_active_sessions,
    set_ba_session_counts,
)
from src.services.ba_session_manager import ba_session_manager


app = FastAPI()
app.include_router(ba_sessions_router)


@contextmanager
def client():
    with TestClient(app) as test_client:
        yield test_client


def _drain_until(ws, expected_type):
    for _ in range(5):
        message = ws.receive_json()
        if message.get("type") == expected_type:
            return message
    raise AssertionError(f"Expected message type {expected_type} not received")


@pytest.mark.integration
def test_multi_user_session_flow(tmp_path):
    audit_file = tmp_path / "ba_sessions.log"
    old_audit_path = ba_session_manager.audit_path
    ba_session_manager.audit_path = audit_file
    ba_session_manager.audit_path.parent.mkdir(parents=True, exist_ok=True)
    ba_session_manager.clear()
    set_ba_session_counts(0, 0)

    try:
        with client() as test_client:
            with test_client.websocket_connect(
                "/ba-sessions/ws/e2e?user_id=lead&role=lead"
            ) as lead_ws:
                _drain_until(lead_ws, "connected")
                _drain_until(lead_ws, "system")

                with test_client.websocket_connect(
                    "/ba-sessions/ws/e2e?user_id=analyst&role=analyst"
                ) as analyst_ws:
                    _drain_until(analyst_ws, "connected")
                    _drain_until(analyst_ws, "system")

                    # System notification for analyst join broadcasted to lead
                    _drain_until(lead_ws, "system")

                    lead_ws.send_json({"type": "chat", "text": "hello analyst"})
                    chat_msg = _drain_until(analyst_ws, "chat")
                    assert chat_msg["text"] == "hello analyst"
                    assert chat_msg["sender"] == "lead"

                # Analyst disconnect triggers system notification for lead
                _drain_until(lead_ws, "system")

        assert ba_ws_active_sessions._value.get() == 0
        assert ba_ws_active_participants._value.get() == 0

        assert audit_file.exists()
        records = [
            json.loads(line)
            for line in audit_file.read_text(encoding="utf-8").splitlines()
        ]
        event_types = {record["event_type"] for record in records}
        assert {"join", "chat", "leave", "session_closed"} <= event_types
    finally:
        ba_session_manager.audit_path = old_audit_path
        ba_session_manager.clear()
        set_ba_session_counts(0, 0)
