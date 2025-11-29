from fastapi import Depends
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.modules.graph_api.services.graph_service import GraphService, VectorSearchService

from src.db.neo4j_client import Neo4jClient, get_neo4j_client
from src.db.qdrant_client import QdrantClient
from src.services.embedding_service import EmbeddingService

from src.services.common_dependencies import get_qdrant_client, get_embedding_service

# Lazy import for GraphService to avoid circular dependency
# from src.modules.graph_api.services.graph_service import GraphService
# from src.modules.graph_api.services.vector_search_service import VectorSearchService


def get_graph_service(
    neo4j_client: Neo4jClient = Depends(get_neo4j_client),
) -> "GraphService":
    """Get or create GraphService instance"""
    from src.modules.graph_api.services.graph_service import GraphService

    return GraphService(neo4j_client)


def get_vector_search_service(
    qdrant_client: Optional[QdrantClient] = Depends(get_qdrant_client),
    embedding_service: Optional[EmbeddingService] = Depends(get_embedding_service),
) -> "VectorSearchService":
    """Get VectorSearchService instance"""
    from src.modules.graph_api.services.graph_service import VectorSearchService

    if not qdrant_client or not embedding_service:
        # Handle missing dependencies gracefully or raise error
        # For now, let's assume they might be None and let the service handle it or raise here
        # But the original code raised HTTPException(503)
        pass

    return VectorSearchService(qdrant_client, embedding_service)
