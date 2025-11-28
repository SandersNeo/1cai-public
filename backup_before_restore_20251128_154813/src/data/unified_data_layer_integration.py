# [NEXUS IDENTITY] ID: -8408895667735676383 | DATE: 2025-11-19

"""
Unified Data Layer Integration
===============================

Интеграция Unified Data Layer с существующими клиентами:
- PostgreSQLSaver
- Neo4jClient
- QdrantClient
- ElasticsearchClient
"""

import logging
from typing import Any, Dict

from src.infrastructure.data_layer import (DataOperation, DataSource,
                                           UnifiedDataLayer)

logger = logging.getLogger(__name__)


class UnifiedDataLayerIntegration:
    """
    Интеграция Unified Data Layer с существующими клиентами

    Обеспечивает единый интерфейс для работы с:
    - PostgreSQL
    - Neo4j
    - Qdrant
    - Elasticsearch
    - Redis
    """

    def __init__(self):
        self.data_layer = UnifiedDataLayer()
        self._clients: Dict[str, Any] = {}
        logger.info("UnifiedDataLayerIntegration initialized")

    def register_postgres_client(self, client):
        """Регистрация PostgreSQL клиента"""
        try:
