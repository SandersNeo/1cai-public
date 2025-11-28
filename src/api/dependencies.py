from typing import Optional

from fastapi import Depends, HTTPException

from src.db.neo4j_client import Neo4jClient
from src.db.postgres_saver import PostgreSQLSaver
from src.db.qdrant_client import QdrantClient

# Moved to avoid circular import - imported inside functions that need them:
# from src.exporters.archi_exporter import ArchiExporter
# from src.exporters.archi_importer import ArchiImporter
# from src.modules.graph_api.services.graph_service import GraphService
from src.services.embedding_service import EmbeddingService
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

# Global instances for dependency injection
_neo4j_client: Optional[Neo4jClient] = None
_graph_service: Optional["GraphService"] = None


class ServiceContainer:
    _neo4j_client: Optional[Neo4jClient] = None
    _qdrant_client: Optional[QdrantClient] = None
    _pg_client: Optional[PostgreSQLSaver] = None
    _embedding_service: Optional[EmbeddingService] = None

    @classmethod
    def initialize(cls):
        try:
            # Neo4j
            cls._neo4j_client = Neo4jClient()
            cls._neo4j_client.connect()

            # Qdrant
            cls._qdrant_client = QdrantClient()
            cls._qdrant_client.connect()

            # PostgreSQL
            cls._pg_client = PostgreSQLSaver()
            cls._pg_client.connect()

            # Embeddings
            cls._embedding_service = EmbeddingService()

            logger.info(
                "All services initialized in container",
                extra={
                    "neo4j": cls._neo4j_client is not None,
                    "qdrant": cls._qdrant_client is not None,
                    "postgres": cls._pg_client is not None,
                    "embeddings": cls._embedding_service is not None,
                },
            )
        except Exception as e:
            logger.error(
                f"Service initialization error: {e}",
                extra={"error_type": type(e).__name__},
                exc_info=True,
            )

    @classmethod
    def cleanup(cls):
        if cls._neo4j_client:
            cls._neo4j_client.disconnect()
        if cls._pg_client:
            cls._pg_client.disconnect()
        logger.info("Services cleaned up")

    @classmethod
    def get_neo4j(cls) -> Optional[Neo4jClient]:
        return cls._neo4j_client

    @classmethod
    def get_qdrant(cls) -> Optional[QdrantClient]:
        return cls._qdrant_client

    @classmethod
    def get_postgres(cls) -> Optional[PostgreSQLSaver]:
        return cls._pg_client

    @classmethod
    def get_embedding(cls) -> Optional[EmbeddingService]:
        return cls._embedding_service


def get_qdrant_client() -> QdrantClient:
    return QdrantClient()


def get_neo4j_client() -> Neo4jClient:
    """Get or create Neo4j client with connection validation"""
    global _neo4j_client

    if _neo4j_client is None:
        _neo4j_client = Neo4jClient()
        if not _neo4j_client.connect():
            logger.warning("Neo4j not available")
            raise HTTPException(
                status_code=503, detail="Neo4j database not available"
            )

    return _neo4j_client


def get_graph_service(
    neo4j_client: Neo4jClient = Depends(get_neo4j_client),
) -> "GraphService":
    """Get or create GraphService instance"""
    # Lazy import to avoid circular dependency
    from src.modules.graph_api.services.graph_service import GraphService

    global _graph_service

    if _graph_service is None:
        _graph_service = GraphService(neo4j_client)

    return _graph_service


def get_archi_exporter(
    graph_service: "GraphService" = Depends(get_graph_service),
) -> "ArchiExporter":
    """Get ArchiExporter with injected GraphService"""
    # Lazy import to avoid circular dependency
    from src.exporters.archi_exporter import ArchiExporter
    return ArchiExporter(graph_service)


def get_archi_importer(
    graph_service = Depends(get_graph_service),
):
    """Get ArchiImporter instance"""
    # Lazy import to avoid circular dependency
    from src.exporters.archi_importer import ArchiImporter

    return ArchiImporter(graph_service)


def get_postgres_client() -> Optional[PostgreSQLSaver]:
    return ServiceContainer.get_postgres()


def get_embedding_service() -> Optional[EmbeddingService]:
    return ServiceContainer.get_embedding()
