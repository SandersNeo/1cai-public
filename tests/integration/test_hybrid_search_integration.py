# [NEXUS IDENTITY] ID: 2867967284889326908 | DATE: 2025-11-19

"""
Integration-style tests for HybridSearchService with mocked backends.
"""

import asyncio

import pytest

from src.services.hybrid_search import HybridSearchService


class DummyQdrantClient:
    def __init__(self):
        self.calls = []

    def search_code(self, query_vector, config_filter=None, limit=10):
        self.calls.append(
            {"vector": query_vector, "config_filter": config_filter, "limit": limit}
        )
        return [
            {
                "id": "doc-vector-1",
                "score": 0.9,
                "payload": {"text": "vector doc 1"},
            },
            {
                "id": "doc-shared",
                "score": 0.8,
                "payload": {"text": "vector doc shared"},
            },
        ]


class DummyElasticsearchClient:
    def __init__(self, delay: float = 0.0):
        self.calls = []
        self.delay = delay

    async def search_code(self, query, config_filter=None, limit=10):
        self.calls.append(
            {"query": query, "config_filter": config_filter, "limit": limit}
        )
        if self.delay:
            await asyncio.sleep(self.delay)
        return [
            {
                "id": "doc-text-1",
                "score": 0.95,
                "source": {"text": "text doc"},
                "highlight": {"field": ["hit"]},
            },
            {
                "id": "doc-shared",
                "score": 0.7,
                "source": {"text": "text shared"},
            },
        ]


class DummyEmbeddingService:
    def __init__(self, should_fail=False):
        self.should_fail = should_fail
        self.last_input = None

    def encode(self, text):
        self.last_input = text
        if self.should_fail:
            raise RuntimeError("encoder offline")
        return [0.1, 0.2, 0.3]


@pytest.mark.asyncio
async def test_hybrid_search_merges_vector_and_text_results():
    qdrant = DummyQdrantClient()
    elastic = DummyElasticsearchClient()
    embeddings = DummyEmbeddingService()
    service = HybridSearchService(qdrant, elastic, embeddings)

    results = await service.search("Find invoices", config_filter="UT", limit=2)

    assert len(results) == 2
    assert results[0]["final_rank"] == 1
    assert "sources" in results[0]
    assert qdrant.calls and elastic.calls
    assert embeddings.last_input.startswith("Find invoices")


@pytest.mark.asyncio
async def test_hybrid_search_falls_back_to_text_when_embeddings_fail():
    qdrant = DummyQdrantClient()
    elastic = DummyElasticsearchClient()
    embeddings = DummyEmbeddingService(should_fail=True)
    service = HybridSearchService(qdrant, elastic, embeddings)

    results = await service.search("No vectors today", limit=1)

    assert len(results) == 1
    assert results[0]["sources"] == ["fulltext"]
    assert not qdrant.calls  # vector search skipped


@pytest.mark.asyncio
async def test_hybrid_search_handles_timeout_and_returns_empty():
    qdrant = DummyQdrantClient()
    elastic = DummyElasticsearchClient(delay=0.05)
    embeddings = DummyEmbeddingService()
    service = HybridSearchService(qdrant, elastic, embeddings)

    results = await service.search("slow query", timeout=0.01)

    assert results == []
