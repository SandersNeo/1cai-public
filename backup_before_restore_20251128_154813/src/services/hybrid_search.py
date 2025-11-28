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
