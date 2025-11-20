# [NEXUS IDENTITY] ID: 7693916182692542221 | DATE: 2025-11-19

"""
Hybrid Search Service
Версия: 2.0.0

Улучшения:
- Улучшенная обработка ошибок
- Timeout для параллельных запросов
- Graceful degradation при ошибках
- Structured logging
"""

import asyncio
from typing import Any, Dict, List, Optional

from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger
MAX_QUERY_LENGTH = 5000


class HybridSearchService:
    """Hybrid search combining Qdrant and Elasticsearch"""

    def __init__(self, qdrant_client, elasticsearch_client, embedding_service):
        """
        Initialize hybrid search

        Args:
            qdrant_client: QdrantClient instance
            elasticsearch_client: ElasticsearchClient instance
            embedding_service: EmbeddingService instance
        """
        self.qdrant = qdrant_client
        self.elasticsearch = elasticsearch_client
        self.embeddings = embedding_service

    async def search(
        self,
        query: str,
        config_filter: Optional[str] = None,
        limit: int = 10,
        rrf_k: int = 60,
        timeout: float = 30.0,
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining vector and full-text

        Args:
            query: Search query
            config_filter: Filter by configuration
            limit: Number of results
            rrf_k: RRF k parameter (default 60)
            timeout: Timeout in seconds (default 30.0)

        Returns:
            Merged and ranked results
        """
        try:
            # Input validation
            if not isinstance(query, str):
                logger.warning(
                    "Invalid query in hybrid search",
                    extra={"query_type": type(query).__name__ if query else None},
                )
                return []

            sanitized_query = query.strip()
            if not sanitized_query:
                logger.warning("Empty query after stripping in hybrid search")
                return []

            if len(sanitized_query) > MAX_QUERY_LENGTH:
                logger.warning(
                    "Query too long in hybrid search",
                    extra={
                        "query_length": len(sanitized_query),
                        "max_length": MAX_QUERY_LENGTH,
                    },
                )
                sanitized_query = sanitized_query[:MAX_QUERY_LENGTH]

            # Validate timeout
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                logger.warning(
                    "Invalid timeout in hybrid search",
                    extra={"timeout": timeout, "timeout_type": type(timeout).__name__},
                )
                timeout = 30.0

            if timeout > 300:  # Max 5 minutes
                logger.warning(
                    "Timeout too large in hybrid search", extra={"timeout": timeout}
                )
                timeout = 300.0

            # Generate query embedding for vector search
            query_vector: List[float] = []
            if not self.embeddings:
                logger.warning(
                    "Embedding service not configured, skipping vector search"
                )
            else:
                try:
                    query_vector = self.embeddings.encode(sanitized_query)
                except Exception as encode_error:  # noqa: BLE001
                    logger.error(
                        "Embedding generation failed",
                        extra={
                            "error": str(encode_error),
                            "error_type": type(encode_error).__name__,
                        },
                        exc_info=True,
                    )
                    query_vector = []

            # Execute searches in parallel (vector can be skipped)
            gather_tasks = []
            task_names: List[str] = []

            if query_vector:
                vector_task = self._vector_search(
                    query_vector, config_filter, limit * 2
                )
                gather_tasks.append(vector_task)
                task_names.append("vector")
            else:
                logger.warning(
                    "Skipping vector search due to empty embedding",
                    extra={"query_preview": sanitized_query[:100]},
                )

            text_task = self._fulltext_search(sanitized_query, config_filter, limit * 2)
            gather_tasks.append(text_task)
            task_names.append("text")

            if not gather_tasks:
                logger.warning("No search tasks scheduled for hybrid search")
                return []

            try:
                task_results = await asyncio.wait_for(
                    asyncio.gather(*gather_tasks, return_exceptions=True),
                    timeout=timeout,  # Use validated timeout
                )
            except asyncio.TimeoutError:
                logger.error(
                    "Timeout при hybrid search",
                    extra={
                        "query": sanitized_query[:100],
                        "config_filter": config_filter,
                        "limit": limit,
                    },
                )
                vector_results = []
                text_results = []
            else:
                vector_results = []
                text_results = []
                result_index = 0
                if "vector" in task_names:
                    vector_results = task_results[result_index]
                    result_index += 1
                if "text" in task_names:
                    text_results = task_results[result_index]

            # Handle errors with structured logging (best practice)
            if isinstance(vector_results, Exception):
                logger.error(
                    "Vector search failed",
                    exc_info=True,
                    extra={
                        "error": str(vector_results),
                        "error_type": type(vector_results).__name__,
                        "query": sanitized_query[:100],
                        "config_filter": config_filter,
                    },
                )
                vector_results = []

            if isinstance(text_results, Exception):
                logger.error(
                    "Text search failed",
                    exc_info=True,
                    extra={
                        "error": str(text_results),
                        "error_type": type(text_results).__name__,
                        "query": sanitized_query[:100],
                        "config_filter": config_filter,
                    },
                )
                text_results = []

            # Merge results using RRF
            merged = self._reciprocal_rank_fusion(vector_results, text_results, k=rrf_k)

            # Return top N
            return merged[:limit]

        except Exception as e:
            logger.error(
                "Unexpected error in hybrid search",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "query": (
                        locals().get("sanitized_query", query)[:100]
                        if isinstance(locals().get("sanitized_query", query), str)
                        else None
                    ),
                    "config_filter": config_filter,
                    "limit": limit,
                },
                exc_info=True,
            )
            return []

    async def _vector_search(
        self, query_vector: List[float], config_filter: Optional[str], limit: int
    ) -> List[Dict[str, Any]]:
        """Execute vector search in Qdrant"""
        if not self.qdrant:
            logger.warning("Qdrant client not configured for vector search")
            return []

        if not query_vector:
            logger.warning("Empty query vector provided to vector search")
            return []

        try:
            results = self.qdrant.search_code(
                query_vector=query_vector, config_filter=config_filter, limit=limit
            )

            # Normalize format
            normalized = []
            for r in results:
                normalized.append(
                    {
                        "id": r["id"],
                        "score": r["score"],
                        "source": "vector",
                        "payload": r["payload"],
                    }
                )

            return normalized

        except Exception as e:
            logger.error(
                "Vector search error",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "config_filter": config_filter,
                    "limit": limit,
                },
                exc_info=True,
            )
            return []

    async def _fulltext_search(
        self, query: str, config_filter: Optional[str], limit: int
    ) -> List[Dict[str, Any]]:
        """Execute full-text search in Elasticsearch"""
        if not self.elasticsearch:
            logger.warning("Elasticsearch client not configured for full-text search")
            return []

        try:
            results = await self.elasticsearch.search_code(
                query=query, config_filter=config_filter, limit=limit
            )

            # Normalize format
            normalized = []
            for r in results:
                normalized.append(
                    {
                        "id": r["id"],
                        "score": r["score"],
                        "source": "fulltext",
                        "payload": r["source"],
                        "highlight": r.get("highlight", {}),
                    }
                )

            return normalized

        except Exception as e:
            logger.error(
                "Full-text search error",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "query": query[:100] if query else None,
                    "config_filter": config_filter,
                    "limit": limit,
                },
                exc_info=True,
            )
            return []

    def _reciprocal_rank_fusion(
        self, vector_results: List[Dict], text_results: List[Dict], k: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Reciprocal Rank Fusion algorithm

        RRF formula: score(d) = Σ 1/(k + rank(d))

        Args:
            vector_results: Results from vector search
            text_results: Results from text search
            k: Constant (typically 60)

        Returns:
            Merged and re-ranked results
        """
        # Build unified result set
        all_results = {}

        # Add vector results with ranks
        for rank, result in enumerate(vector_results, 1):
            doc_id = result["id"]
            rrf_score = 1.0 / (k + rank)

            if doc_id not in all_results:
                all_results[doc_id] = {
                    "id": doc_id,
                    "payload": result["payload"],
                    "rrf_score": 0.0,
                    "vector_rank": rank,
                    "vector_score": result["score"],
                    "sources": [],
                }

            all_results[doc_id]["rrf_score"] += rrf_score
            all_results[doc_id]["sources"].append("vector")

        # Add text results with ranks
        for rank, result in enumerate(text_results, 1):
            doc_id = result["id"]
            rrf_score = 1.0 / (k + rank)

            if doc_id not in all_results:
                all_results[doc_id] = {
                    "id": doc_id,
                    "payload": result["payload"],
                    "rrf_score": 0.0,
                    "sources": [],
                }
            else:
                # Document found in both searches - bonus!
                all_results[doc_id]["rrf_score"] *= 1.2

            all_results[doc_id]["rrf_score"] += rrf_score
            all_results[doc_id]["sources"].append("fulltext")

            if "fulltext_rank" not in all_results[doc_id]:
                all_results[doc_id]["fulltext_rank"] = rank
                all_results[doc_id]["fulltext_score"] = result["score"]

            if "highlight" in result:
                all_results[doc_id]["highlight"] = result["highlight"]

        # Convert to list and sort by RRF score
        merged = list(all_results.values())
        merged.sort(key=lambda x: x["rrf_score"], reverse=True)

        # Add final ranks
        for rank, result in enumerate(merged, 1):
            result["final_rank"] = rank

        return merged
