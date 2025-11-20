# [NEXUS IDENTITY] ID: -4487350310196249049 | DATE: 2025-11-19

import json
from typing import Any, Dict

import httpx
import pytest

from src.ai.agents.business_analyst_agent_extended import IntegrationConnector
from src.integrations.confluence import ConfluenceClient
from src.integrations.jira import JiraClient
from src.integrations.onedocflow import OneCDocflowClient
from src.integrations.powerbi import PowerBIClient


def _mock_transport(handler):
    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_jira_client_create_issue():
    captured: Dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["url"] = request.url
        captured["payload"] = json.loads(request.content.decode())
        assert request.headers["Authorization"] == "Bearer token"
        return httpx.Response(
            201, json={"key": "TEST-1", "self": "https://jira.example.com/TEST-1"}
        )

    client = JiraClient(
        base_url="https://jira.example.com",
        token="token",
        transport=_mock_transport(handler),
    )
    response = await client.create_issue(
        project_key="PROJ",
        summary="Summary",
        description="Desc",
    )
    await client.aclose()

    assert captured["method"] == "POST"
    assert captured["url"].path == "/rest/api/3/issue"
    assert captured["payload"]["fields"]["project"]["key"] == "PROJ"
    assert captured["payload"]["fields"]["summary"] == "Summary"
    assert response["key"] == "TEST-1"


@pytest.mark.asyncio
async def test_confluence_client_create_page():
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content.decode())
        assert payload["title"] == "Demo"
        return httpx.Response(200, json={"id": "123", "links": {"webui": "/wiki/page"}})

    client = ConfluenceClient(
        base_url="https://confluence.example.com",
        token="token",
        transport=_mock_transport(handler),
    )
    response = await client.create_page(
        space_key="SPACE", title="Demo", body="<p>Body</p>"
    )
    await client.aclose()
    assert response["id"] == "123"


@pytest.mark.asyncio
async def test_powerbi_client_trigger_refresh():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path.endswith("/refreshes")
        return httpx.Response(202, json={"status": "InProgress"})

    client = PowerBIClient(
        base_url="https://api.powerbi.com",
        token="token",
        transport=_mock_transport(handler),
    )
    response = await client.trigger_refresh("workspace", "dataset")
    await client.aclose()
    assert response["status"] == "InProgress"


@pytest.mark.asyncio
async def test_docflow_client_register_document():
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content.decode())
        assert payload["title"] == "Doc"
        return httpx.Response(
            200, json={"id": "DOC-1", "url": "https://1c.example.com/doc/1"}
        )

    client = OneCDocflowClient(
        base_url="https://1c.example.com",
        token="token",
        transport=_mock_transport(handler),
    )
    response = await client.register_document(
        title="Doc", description="Desc", category="BA"
    )
    await client.aclose()
    assert response["id"] == "DOC-1"


class _FakeClient:
    def __init__(self, result: Dict[str, Any]):
        self.result = result
        self.called_with = None


class FakeJira(_FakeClient):
    async def create_issue(self, **kwargs):
        self.called_with = kwargs
        return self.result


class FakeConfluence(_FakeClient):
    async def create_page(self, **kwargs):
        self.called_with = kwargs
        return self.result


class FakePowerBI(_FakeClient):
    async def trigger_refresh(self, workspace_id: str, dataset_id: str):
        self.called_with = {"workspace_id": workspace_id, "dataset_id": dataset_id}
        return self.result


class FakeDocflow(_FakeClient):
    async def register_document(self, **kwargs):
        self.called_with = kwargs
        return self.result


@pytest.mark.asyncio
async def test_integration_connector_with_clients(monkeypatch):
    jira = FakeJira({"key": "PROJ-1", "self": "https://jira/PROJ-1"})
    confluence = FakeConfluence({"id": "page", "links": {"webui": "/wiki/page"}})
    powerbi = FakePowerBI({})
    docflow = FakeDocflow({"id": "doc", "url": "https://1c/doc"})

    monkeypatch.setenv("BA_JIRA_DEFAULT_PROJECT", "PROJ")
    monkeypatch.setenv("BA_POWERBI_WORKSPACE_ID", "workspace")
    monkeypatch.setenv("BA_POWERBI_DATASET_ID", "dataset")

    connector = IntegrationConnector(
        jira_client=jira,
        confluence_client=confluence,
        powerbi_client=powerbi,
        docflow_client=docflow,
    )
    artefact = {
        "type": "roadmap",
        "content": "Plan",
        "metadata": {
            "summary": "Roadmap sync",
            "title": "Roadmap v1",
            "description": "Description",
            "space_key": "SPACE",
            "category": "BA",
        },
    }
    result = await connector.sync(
        artefact,
        targets=["jira", "confluence", "powerbi", "1c_docflow"],
    )
    statuses = {item["target"]: item["status"] for item in result["results"]}
    assert statuses["jira"] == "created"
    assert statuses["confluence"] == "published"
    assert statuses["powerbi"] == "refresh_requested"
    assert statuses["1c_docflow"] == "registered"


@pytest.mark.asyncio
async def test_integration_connector_stubs_when_not_configured(monkeypatch):
    # Ensure env variables not set
    monkeypatch.delenv("BA_JIRA_BASE_URL", raising=False)
    monkeypatch.delenv("BA_JIRA_TOKEN", raising=False)

    connector = IntegrationConnector()
    artefact = {"type": "roadmap", "metadata": {"summary": "Test"}}
    result = await connector.sync(artefact, targets=["jira"])
    assert result["results"][0]["status"] == "queued"
