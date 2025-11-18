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
from typing import Any, Dict, List, Optional
from src.infrastructure.data_layer import UnifiedDataLayer, DataOperation, DataSource

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
            from src.db.postgres_saver import PostgreSQLSaver
            if isinstance(client, PostgreSQLSaver):
                self._clients["postgresql"] = client
                self.data_layer.register_source(
                    DataSource.POSTGRESQL,
                    self._postgres_adapter(client)
                )
                logger.info("PostgreSQL client registered")
        except Exception as e:
            logger.error(f"Failed to register PostgreSQL client: {e}")
    
    def register_neo4j_client(self, client):
        """Регистрация Neo4j клиента"""
        try:
            from src.db.neo4j_client import Neo4jClient
            if isinstance(client, Neo4jClient):
                self._clients["neo4j"] = client
                self.data_layer.register_source(
                    DataSource.NEO4J,
                    self._neo4j_adapter(client)
                )
                logger.info("Neo4j client registered")
        except Exception as e:
            logger.error(f"Failed to register Neo4j client: {e}")
    
    def register_qdrant_client(self, client):
        """Регистрация Qdrant клиента"""
        try:
            from src.db.qdrant_client import QdrantClient
            if isinstance(client, QdrantClient):
                self._clients["qdrant"] = client
                self.data_layer.register_source(
                    DataSource.QDRANT,
                    self._qdrant_adapter(client)
                )
                logger.info("Qdrant client registered")
        except Exception as e:
            logger.error(f"Failed to register Qdrant client: {e}")
    
    def register_elasticsearch_client(self, client):
        """Регистрация Elasticsearch клиента"""
        try:
            # Предполагаем, что есть ElasticsearchClient
            self._clients["elasticsearch"] = client
            self.data_layer.register_source(
                DataSource.ELASTICSEARCH,
                self._elasticsearch_adapter(client)
            )
            logger.info("Elasticsearch client registered")
        except Exception as e:
            logger.error(f"Failed to register Elasticsearch client: {e}")
    
    def _postgres_adapter(self, client):
        """Адаптер для PostgreSQL"""
        async def execute(operation: DataOperation, data: Any) -> Any:
            if operation == DataOperation.READ:
                # Адаптация к методу чтения PostgreSQL
                return await client.get_data(data)
            elif operation == DataOperation.WRITE:
                return await client.save_data(data)
            elif operation == DataOperation.UPDATE:
                return await client.update_data(data)
            elif operation == DataOperation.DELETE:
                return await client.delete_data(data)
        
        return execute
    
    def _neo4j_adapter(self, client):
        """Адаптер для Neo4j"""
        async def execute(operation: DataOperation, data: Any) -> Any:
            if operation == DataOperation.READ:
                # Cypher query
                return await client.execute_query(data)
            elif operation == DataOperation.WRITE:
                # Create node/relationship
                return await client.create_node(data)
            elif operation == DataOperation.UPDATE:
                return await client.update_node(data)
            elif operation == DataOperation.DELETE:
                return await client.delete_node(data)
        
        return execute
    
    def _qdrant_adapter(self, client):
        """Адаптер для Qdrant"""
        async def execute(operation: DataOperation, data: Any) -> Any:
            if operation == DataOperation.READ:
                # Vector search
                return await client.search(data)
            elif operation == DataOperation.WRITE:
                # Insert vector
                return await client.insert(data)
            elif operation == DataOperation.UPDATE:
                return await client.update(data)
            elif operation == DataOperation.DELETE:
                return await client.delete(data)
        
        return execute
    
    def _elasticsearch_adapter(self, client):
        """Адаптер для Elasticsearch"""
        async def execute(operation: DataOperation, data: Any) -> Any:
            if operation == DataOperation.READ:
                return await client.search(data)
            elif operation == DataOperation.WRITE:
                return await client.index(data)
            elif operation == DataOperation.UPDATE:
                return await client.update(data)
            elif operation == DataOperation.DELETE:
                return await client.delete(data)
        
        return execute
    
    async def unified_read(
        self,
        source: DataSource,
        query: Any
    ) -> Any:
        """Единый интерфейс для чтения"""
        return await self.data_layer.read(source, query)
    
    async def unified_write(
        self,
        source: DataSource,
        data: Any
    ) -> Any:
        """Единый интерфейс для записи"""
        return await self.data_layer.write(source, data)
    
    async def unified_update(
        self,
        source: DataSource,
        data: Any
    ) -> Any:
        """Единый интерфейс для обновления"""
        return await self.data_layer.update(source, data)
    
    async def unified_delete(
        self,
        source: DataSource,
        data: Any
    ) -> Any:
        """Единый интерфейс для удаления"""
        return await self.data_layer.delete(source, data)

