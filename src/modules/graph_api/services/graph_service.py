import re
from typing import Any, Dict, List, Optional

from src.config import USE_TEMPORAL_GNN
from src.db.neo4j_client import Neo4jClient
from src.db.qdrant_client import QdrantClient
from src.services.embedding_service import EmbeddingService
from src.utils.retry_utils import retry_on_transient_error
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

MAX_SEMANTIC_QUERY_LENGTH = 5000


class GraphService:
    """
    Service for graph database operations with async support.

    With optional Temporal GNN for code evolution tracking.
    """

    def __init__(self, neo4j_client: Neo4jClient):
        self.neo4j = neo4j_client

        # Temporal GNN integration (optional)
        self._temporal = None
        if USE_TEMPORAL_GNN:
            try:
                from src.modules.graph_api.services.temporal_graph_service import (
                    TemporalGraphService,
                )

                self._temporal = TemporalGraphService(self)
                logger.info("Temporal GNN enabled for GraphService")
            except Exception as e:
                logger.warning(f"Failed to initialize Temporal GNN: {e}", exc_info=True)

    @retry_on_transient_error(max_attempts=3, min_wait=1.0, max_wait=10.0)
    async def execute_query(self, query: str, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute Cypher query with validation and retry logic (async)."""
        query_upper = query.strip().upper()
        if not (query_upper.startswith("MATCH") or query_upper.startswith("RETURN")):
            raise ValueError("Only MATCH and RETURN queries are allowed")

        # Use async session
        async with self.neo4j.driver.session() as session:
            try:
                result = await session.run(query, parameters)
                records = []
                async for record in result:
                    try:
                        records.append(dict(record))
                    except Exception as e:
                        logger.warning(
                            f"Failed to convert record: {e}",
                            extra={"record_keys": list(record.keys())},
                        )
                        continue
            except Exception as e:
                logger.error(
                    f"Query execution failed: {e}",
                    extra={"query_preview": query[:100]},
                    exc_info=True,
                )
                raise

        logger.info(
            "Graph query executed successfully",
            extra={
                "query_length": len(query),
                "results_count": len(records),
                "has_parameters": bool(parameters),
            },
        )
        return records

    async def get_configurations(self) -> List[Dict[str, Any]]:
        """Get all configurations."""
        async with self.neo4j.driver.session() as session:
            result = await session.run(
                """
                MATCH (c:Configuration)
                RETURN c.name as name,
                       c.full_name as full_name,
                       c.version as version
                ORDER BY c.name
            """
            )
            records = []
            async for record in result:
                records.append(dict(record))
            return records

    async def get_objects(self, config_name: str, object_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get objects of a configuration."""
        # Sanitize inputs
        config_name = re.sub(r"[^a-zA-Z0-9_.-]", "", config_name)
        if object_type:
            object_type = re.sub(r"[^a-zA-Z0-9_.-]", "", object_type)

        if object_type:
            objects = await self.neo4j.search_objects_by_type(object_type, config_name)
        else:
            async with self.neo4j.driver.session() as session:
                result = await session.run(
                    """
                    MATCH (c:Configuration {name: $config})-[:HAS_OBJECT]->(o:Object)
                    RETURN o.type as type,
                           o.name as name,
                           o.description as description
                    ORDER BY o.type, o.name
                """,
                    config=config_name,
                )
                objects = []
                async for record in result:
                    objects.append(dict(record))

        logger.info(
            "Objects retrieved successfully",
            extra={
                "config_name": config_name,
                "object_type": object_type,
                "objects_count": len(objects),
            },
        )
        return objects

    async def get_function_dependencies(self, module_name: str, function_name: str) -> Dict[str, Any]:
        """Get function call graph."""
        dependencies = await self.neo4j.get_function_dependencies(module_name, function_name)
        callers = await self.neo4j.get_function_callers(module_name, function_name)

        return {
            "function": {"module": module_name, "name": function_name},
            "calls_to": dependencies,
            "called_by": callers,
        }

    async def get_statistics(self) -> Dict[str, Any]:
        """Get Neo4j statistics."""
        return await self.neo4j.get_statistics()


class VectorSearchService:
    """Service for vector search operations."""

    def __init__(self, qdrant_client: QdrantClient, embedding_service: EmbeddingService):
        self.qdrant = qdrant_client
        self.embedding = embedding_service

    def is_ready(self) -> bool:
        """Check if service is ready."""
        return (
            self.qdrant is not None
            and getattr(self.qdrant, "client", None) is not None
            and self.embedding is not None
            and getattr(self.embedding, "model", None) is not None
        )

    async def semantic_search(
        self,
        query: str,
        configuration: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Perform semantic search."""
        if not self.is_ready():
            raise RuntimeError("Vector search service not available")

        # Generate query embedding
        query_text = query[:MAX_SEMANTIC_QUERY_LENGTH]
        query_vector = self.embedding.encode(query_text)
        if not query_vector:
            raise RuntimeError("Unable to generate embedding for query")

        # Search in Qdrant
        results = self.qdrant.search_code(
            query_vector=query_vector,
            config_filter=configuration,
            limit=limit,
        )

        logger.info(
            "Semantic search completed",
            extra={
                "query_length": len(query),
                "configuration": configuration,
                "limit": limit,
                "results_count": len(results),
            },
        )
        return results

    async def get_statistics(self) -> Dict[str, Any]:
        """Get Qdrant statistics."""
        return self.qdrant.get_statistics()
