# [NEXUS IDENTITY] ID: 714594101778786205 | DATE: 2025-11-19

"""
Unit tests for Graph API semantic search endpoint.
"""

import pytest
from fastapi.testclient import TestClient

from src.api import graph_api


class DummyQdrant:
    """Lightweight stub for Qdrant client."""

    def __init__(self):
        self.client = object()
        self.calls = []

    def search_code(self, query_vector, config_filter=None, limit=10):
        self.calls.append(
            {"vector": query_vector, "config": config_filter, "limit": limit}
        )
        return [
            {"id": "1", "score": 0.9, "payload": {"name": "Func1"}},
            {"id": "2", "score": 0.8, "payload": {"name": "Func2"}},
        ]


class DummyEmbedding:
    """Embedding stub that can simulate loaded/unloaded models."""

    def __init__(self, vector=None, has_model=True):
        self.model = object() if has_model else None
        self._vector = vector if vector is not None else [0.1, 0.2, 0.3]

    def encode(self, text):
        return self._vector


@pytest.fixture(autouse=True)
def reset_services():
    """Reset global clients before each test to isolate state."""
    graph_api.neo4j_client = None
    graph_api.pg_client = None
    graph_api.qdrant_client = None
    graph_api.embedding_service = None
    yield
    graph_api.neo4j_client = None
    graph_api.pg_client = None
    graph_api.qdrant_client = None
    graph_api.embedding_service = None


@pytest.fixture
def client():
    """FastAPI test client without relying on real services."""
    return TestClient(graph_api.app)


def prepare_semantic_services(vector=None, has_model=True):
    """Helper to configure stub services for semantic search."""
    graph_api.qdrant_client = DummyQdrant()
    graph_api.embedding_service = DummyEmbedding(vector=vector, has_model=has_model)


def test_semantic_search_success(client):
    """Semantic search returns payload when services are ready."""
    prepare_semantic_services()

    response = client.post(
        "/api/search/semantic",
        json={"query": "test query", "configuration": "UT", "limit": 5},
    )

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 2
    assert graph_api.qdrant_client.calls  # Qdrant received at least one call


def test_semantic_search_rejects_long_query(client):
    """Requests that exceed max length should fail validation (422)."""
    prepare_semantic_services()

    long_query = "x" * (graph_api.MAX_SEMANTIC_QUERY_LENGTH + 1)
    response = client.post("/api/search/semantic", json={"query": long_query})

    assert response.status_code == 422


def test_semantic_search_requires_embedding_service(client):
    """When embeddings are unavailable the endpoint should return 503."""
    graph_api.qdrant_client = DummyQdrant()
    graph_api.embedding_service = None

    response = client.post("/api/search/semantic", json={"query": "short query"})

    assert response.status_code == 503
    assert response.json()["detail"] == "Embedding service not available"


def test_semantic_search_handles_empty_embedding(client):
    """If embedding service cannot produce vector we return 503 without calling Qdrant."""
    prepare_semantic_services(vector=[])

    response = client.post("/api/search/semantic", json={"query": "valid"})

    assert response.status_code == 503
    assert graph_api.qdrant_client.calls == []
