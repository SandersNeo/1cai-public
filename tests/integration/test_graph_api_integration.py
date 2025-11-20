# [NEXUS IDENTITY] ID: 7234445431799216721 | DATE: 2025-11-19

"""
Integration-style tests for src.api.graph_api using TestClient with mocked dependencies.
"""

import pytest
from fastapi.testclient import TestClient

from src.api import graph_api


class DummyNeo4jSession:
    def __init__(self, records=None):
        self.records = records or [{"result": 1}]
        self.last_query = None
        self.last_parameters = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def run(self, query, parameters=None):
        self.last_query = query
        self.last_parameters = parameters or {}
        return self.records


class DummyNeo4jDriver:
    def __init__(self):
        self.session_instance = DummyNeo4jSession()

    def session(self):
        return self.session_instance


class DummyNeo4jClient:
    def __init__(self):
        self.driver = DummyNeo4jDriver()

    def search_objects_by_type(self, object_type, config_name):
        return [
            {
                "type": object_type,
                "name": f"{config_name}::{object_type}",
                "description": "demo",
            }
        ]

    def get_function_dependencies(self, module_name, function_name):
        return [{"module": module_name, "function": f"{function_name}_dep"}]

    def get_function_callers(self, module_name, function_name):
        return [{"module": module_name, "function": f"{function_name}_caller"}]

    def get_statistics(self):
        return {"nodes": 1}


class DummyQdrantClient:
    def __init__(self):
        self.client = object()
        self.last_search = None

    def search_code(self, query_vector, config_filter=None, limit=10):
        self.last_search = {
            "query_vector": query_vector,
            "config_filter": config_filter,
            "limit": limit,
        }
        return [
            {"id": "doc-1", "score": 0.99, "configuration": config_filter or "default"},
        ]

    def get_statistics(self):
        return {"collections": 1}


class DummyEmbeddingService:
    def __init__(self):
        self.model = object()
        self.last_input = None

    def encode(self, text):
        self.last_input = text
        return [0.1, 0.2, 0.3]


class DummyPostgresSaver:
    def get_statistics(self):
        return {"tables": 1}


@pytest.fixture
def graph_test_client(monkeypatch):
    """
    Provide TestClient with patched dependencies so tests don't hit real services.
    """
    original_startup = list(graph_api.app.router.on_startup)
    original_shutdown = list(graph_api.app.router.on_shutdown)
    graph_api.app.router.on_startup.clear()
    graph_api.app.router.on_shutdown.clear()

    dummy_neo4j = DummyNeo4jClient()
    dummy_qdrant = DummyQdrantClient()
    dummy_embeddings = DummyEmbeddingService()
    dummy_pg = DummyPostgresSaver()

    monkeypatch.setattr(graph_api, "neo4j_client", dummy_neo4j)
    monkeypatch.setattr(graph_api, "qdrant_client", dummy_qdrant)
    monkeypatch.setattr(graph_api, "embedding_service", dummy_embeddings)
    monkeypatch.setattr(graph_api, "pg_client", dummy_pg)

    client = TestClient(graph_api.app)

    yield client, {
        "neo4j": dummy_neo4j,
        "qdrant": dummy_qdrant,
        "embeddings": dummy_embeddings,
        "postgres": dummy_pg,
    }

    client.close()
    graph_api.app.router.on_startup[:] = original_startup
    graph_api.app.router.on_shutdown[:] = original_shutdown
    monkeypatch.setattr(graph_api, "neo4j_client", None)
    monkeypatch.setattr(graph_api, "qdrant_client", None)
    monkeypatch.setattr(graph_api, "embedding_service", None)
    monkeypatch.setattr(graph_api, "pg_client", None)


def test_health_endpoint_reports_ready(graph_test_client):
    client, _ = graph_test_client

    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["services"]["neo4j"] is True
    assert body["services"]["qdrant"] is True
    assert body["services"]["postgres"] is True


def test_graph_query_executes_with_mocked_neo4j(graph_test_client):
    client, deps = graph_test_client

    response = client.post(
        "/api/graph/query",
        json={"query": "MATCH (n) RETURN n", "parameters": {"limit": 1}},
    )

    assert response.status_code == 200
    assert "results" in response.json()
    session = deps["neo4j"].driver.session_instance
    assert session.last_query == "MATCH (n) RETURN n"
    assert session.last_parameters == {"limit": 1}


def test_graph_query_rejects_non_match_return(graph_test_client):
    client, _ = graph_test_client

    response = client.post(
        "/api/graph/query",
        json={"query": "WITH 1 as x RETURN x"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only MATCH and RETURN queries are allowed"


def test_graph_query_returns_503_without_neo4j(graph_test_client, monkeypatch):
    client, _ = graph_test_client
    monkeypatch.setattr(graph_api, "neo4j_client", None)

    response = client.post(
        "/api/graph/query",
        json={"query": "MATCH (n) RETURN n"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Neo4j not available"


def test_semantic_search_uses_embeddings_and_qdrant(graph_test_client):
    client, deps = graph_test_client

    response = client.post(
        "/api/search/semantic",
        json={"query": "Find sales documents", "configuration": "UT", "limit": 5},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["results"]

    assert deps["embeddings"].last_input.startswith("Find sales")
    assert deps["qdrant"].last_search["config_filter"] == "UT"
    assert deps["qdrant"].last_search["limit"] == 5
