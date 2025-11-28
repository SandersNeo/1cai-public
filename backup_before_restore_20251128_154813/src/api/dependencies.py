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
