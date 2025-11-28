from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies import (get_embedding_service, get_neo4j_client,
                                  get_postgres_client, get_qdrant_client)
from src.db.neo4j_client import Neo4jClient
from src.db.postgres_saver import PostgreSQLSaver
from src.db.qdrant_client import QdrantClient
from src.modules.graph_api.domain.models import (FunctionDependenciesRequest,
                                                 GraphQueryRequest,
                                                 SemanticSearchRequest)
from src.modules.graph_api.services.graph_service import (GraphService,
                                                          VectorSearchService)
from src.services.embedding_service import EmbeddingService

router = APIRouter(tags=["graph"])


def get_graph_service(
    neo4j_client: Optional[Neo4jClient] = Depends(get_neo4j_client),
) -> GraphService:
    if not neo4j_client:
        raise HTTPException(status_code=503, detail="Neo4j not available")
    return GraphService(neo4j_client)


def get_vector_search_service(
    qdrant_client: Optional[QdrantClient] = Depends(get_qdrant_client),
    embedding_service: Optional[EmbeddingService] = Depends(get_embedding_service),
) -> VectorSearchService:
    if not qdrant_client or not embedding_service:
        raise HTTPException(
            status_code=503,
            detail="Vector search not available")
    return VectorSearchService(qdrant_client, embedding_service)


@router.post("/graph/query")
async def execute_graph_query(
    request: GraphQueryRequest,
    service: GraphService = Depends(get_graph_service),
):
    """Execute custom Cypher query."""
    try:


@router.get("/graph/configurations")
async def get_configurations(
    service: GraphService = Depends(get_graph_service),
):
    """Get all configurations."""
    try:


@router.get("/stats/overview")
async def get_stats_overview(
    neo4j_client: Optional[Neo4jClient] = Depends(get_neo4j_client),
    qdrant_client: Optional[QdrantClient] = Depends(get_qdrant_client),
    pg_client: Optional[PostgreSQLSaver] = Depends(get_postgres_client),
):
    """Get overall statistics."""
    stats = {}

    try:
