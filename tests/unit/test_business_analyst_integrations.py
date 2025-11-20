# [NEXUS IDENTITY] ID: -9072365439784840525 | DATE: 2025-11-19

import pytest

from src.ai.agents.business_analyst_agent_extended import IntegrationConnector


class DummyJiraClient:
    def __init__(self):
        self.calls = []

    async def create_issue(self, **fields):
        self.calls.append(fields)
        return {"key": "BA-101", "self": "https://jira.example.com/BA-101"}


class DummyConfluenceClient:
    def __init__(self):
        self.calls = []

    async def create_page(self, **fields):
        self.calls.append(fields)
        return {"id": "12345", "links": {"webui": "https://wiki/pages/12345"}}


@pytest.mark.asyncio
async def test_jira_sync_success():
    connector = IntegrationConnector(jira_client=DummyJiraClient())
    artefact = {
        "title": "New Feature",
        "content": "Details",
        "metadata": {
            "project_key": "BA",
            "summary": "Summary",
            "description": "Body",
        },
    }

    result = await connector._sync_jira(artefact)

    assert result["status"] == "created"
    assert result["key"] == "BA-101"
    assert connector.jira_client.calls, "Jira client should be invoked"


@pytest.mark.asyncio
async def test_jira_sync_queued_when_not_configured():
    connector = IntegrationConnector(jira_client=None)
    result = await connector._sync_jira({"metadata": {}})

    assert result["status"] == "queued"
    assert result["reason"] == "not_configured"


@pytest.mark.asyncio
async def test_confluence_sync_success():
    connector = IntegrationConnector(confluence_client=DummyConfluenceClient())
    artefact = {
        "title": "Architecture",
        "content": "Doc body",
        "metadata": {
            "space_key": "BA",
            "title": "Doc Title",
            "body": "Doc body",
        },
    }

    result = await connector._sync_confluence(artefact)

    assert result["status"] == "published"
    assert result["url"] == "https://wiki/pages/12345"


@pytest.mark.asyncio
async def test_confluence_sync_missing_space(monkeypatch):
    connector = IntegrationConnector(confluence_client=DummyConfluenceClient())
    # Remove env fallback if any
    monkeypatch.delenv("BA_CONFLUENCE_SPACE_KEY", raising=False)
    artefact = {"metadata": {}}

    result = await connector._sync_confluence(artefact)

    assert result["status"] == "queued"
    assert result["reason"] == "space_key_missing"
