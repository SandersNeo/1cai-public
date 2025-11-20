# [NEXUS IDENTITY] ID: 3778290254917409902 | DATE: 2025-11-19

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.services.ba_session_manager import ba_session_manager


@pytest.mark.integration
def test_ba_websocket_session_broadcast():
    ba_session_manager.clear()
    client = TestClient(app)

    with client.websocket_connect(
        "/ba-sessions/ws/demo?user_id=lead&role=lead"
    ) as lead_ws:
        lead_join = lead_ws.receive_json()
        assert lead_join["event"] == "user_joined"
        assert lead_join["user_id"] == "lead"

        with client.websocket_connect(
            "/ba-sessions/ws/demo?user_id=analyst&role=analyst"
        ) as analyst_ws:
            analyst_join = analyst_ws.receive_json()
            assert analyst_join["event"] == "user_joined"
            assert analyst_join["user_id"] == "analyst"

            # lead получает уведомление о подключении аналитика
            lead_notice = lead_ws.receive_json()
            assert lead_notice["event"] == "user_joined"
            assert lead_notice["user_id"] == "analyst"

            # Отправляем чат-сообщение и проверяем доставку
            lead_ws.send_json({"type": "chat", "text": "Привет"})
            received = analyst_ws.receive_json()
            assert received["type"] == "chat"
            assert received["text"] == "Привет"
            assert received["sender"] == "lead"

            lead_echo = lead_ws.receive_json()
            if lead_echo.get("type") == "chat":
                assert lead_echo["text"] == "Привет"
                left_notice = lead_ws.receive_json()
            else:
                left_notice = lead_echo

        # После выхода аналитика приходит уведомление
        assert left_notice.get("event") == "user_left", left_notice
        assert left_notice.get("user_id") == "analyst"

    # После закрытия всех WebSocket сессий список активных комнат пуст
    response = client.get("/ba-sessions")
    assert response.status_code == 200
    assert response.json() == {"sessions": []}
