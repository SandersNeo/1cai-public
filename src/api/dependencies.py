from typing import Optional

from src.db.neo4j_client import Neo4jClient
from src.db.postgres_saver import PostgreSQLSaver
from src.db.qdrant_client import QdrantClient
from src.services.embedding_service import EmbeddingService
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


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


def get_neo4j_client() -> Optional[Neo4jClient]:
    return ServiceContainer.get_neo4j()


def get_qdrant_client() -> Optional[QdrantClient]:
    return ServiceContainer.get_qdrant()


def get_postgres_client() -> Optional[PostgreSQLSaver]:
    return ServiceContainer.get_postgres()


def get_embedding_service() -> Optional[EmbeddingService]:
    return ServiceContainer.get_embedding()
