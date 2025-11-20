# [NEXUS IDENTITY] ID: -3010645292656268884 | DATE: 2025-11-19

from datetime import timedelta

import pytest

from src.ai.agents.developer_agent_secure import DeveloperAISecure


@pytest.fixture
def secure_agent(monkeypatch):
    agent = DeveloperAISecure()

    def fake_generate(prompt, context):
        return "def generated():\n    return 42"

    def safe_analysis(code):
        return {
            "score": 0.99,
            "concerns": [],
            "safe": True,
            "auto_approvable": True,
        }

    monkeypatch.setattr(agent, "_generate_with_ai", fake_generate)
    monkeypatch.setattr(agent, "_analyze_code_safety", safe_analysis)
    return agent


def test_generate_code_produces_token(secure_agent):
    result = secure_agent.generate_code("Напиши функцию суммирования")

    assert result["success"] is True
    assert result["requires_approval"] is True
    assert result["token"] in secure_agent._pending_suggestions
    suggestion = secure_agent._pending_suggestions[result["token"]]
    assert suggestion["approved"] is False


def test_apply_suggestion_happy_path(secure_agent):
    draft = secure_agent.generate_code("создай обработчик заказа")
    token = draft["token"]

    apply_result = secure_agent.apply_suggestion(token, approved_by_user="teamlead")

    assert apply_result["success"] is True
    assert apply_result["applied"] is True
    assert token not in secure_agent._pending_suggestions


def test_apply_suggestion_invalid_token_returns_error(secure_agent):
    result = secure_agent.apply_suggestion("missing-token", approved_by_user="user")

    assert result["blocked"] is True
    assert "Invalid" in result["error"]


def test_apply_suggestion_expires_after_30_minutes(secure_agent, monkeypatch):
    draft = secure_agent.generate_code("сгенерируй модуль уведомлений")
    token = draft["token"]

    # вручную старим запись
    suggestion = secure_agent._pending_suggestions[token]
    suggestion["created_at"] -= timedelta(minutes=31)

    result = secure_agent.apply_suggestion(token, approved_by_user="alice")

    assert result["blocked"] is True
    assert "Token expired" in result["error"]
    assert token not in secure_agent._pending_suggestions
