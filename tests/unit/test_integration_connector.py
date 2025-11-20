# [NEXUS IDENTITY] ID: -3993155687098389644 | DATE: 2025-11-19

import pytest

from src.ai.agents.business_analyst_agent_extended import IntegrationConnector


@pytest.fixture
def connector():
    return IntegrationConnector(
        jira_client=None,
        confluence_client=None,
        powerbi_client=None,
        docflow_client=None,
    )


def test_safe_text_trims_and_fallback(connector):
    result = connector._safe_text("   ", max_len=10, fallback="Fallback")
    assert result == "Fallback"

    long_text = "x" * 50
    result = connector._safe_text(long_text, max_len=10, fallback="F")
    assert result == "x" * 10


def test_as_paragraphs_escapes_html(connector):
    body = "<script>alert(1)</script>\nSecond"
    html_value = connector._as_paragraphs(body)

    assert "<script>" not in html_value
    assert html_value.count("<p>") == 2
    assert "&lt;script&gt;" in html_value
