from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from src.services.common_dependencies import (
    get_postgres_client,
    get_qdrant_client,
)
from src.db.neo4j_client import Neo4jClient, get_neo4j_client
from src.db.postgres_saver import PostgreSQLSaver
from src.db.qdrant_client import QdrantClient
from src.modules.graph_api.domain.models import (
    FunctionDependenciesRequest,
    GraphQueryRequest,
    SemanticSearchRequest,
)
from src.modules.graph_api.services.graph_service import (
    GraphService,
    VectorSearchService,
)
from src.modules.graph_api.dependencies import (
    get_graph_service,
    get_vector_search_service,
)

router = APIRouter(tags=["graph"])





@router.post("/graph/query")
async def execute_graph_query(
    request: GraphQueryRequest,
    service: GraphService = Depends(get_graph_service),
) -> Dict[str, Any]:
    """Execute custom Cypher query."""
    try:
        records = await service.execute_query(request.query, request.parameters)
        return {"results": records}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")


@router.get("/graph/configurations")
async def get_configurations(
    service: GraphService = Depends(get_graph_service),
) -> Dict[str, Any]:
    """Get all configurations."""
    try:
        configs = await service.get_configurations()
        return {"configurations": configs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph/objects/{config_name}")
async def get_objects(
    config_name: str,
    object_type: Optional[str] = Query(
        None, max_length=100, description="Filter by object type"),
    service: GraphService = Depends(get_graph_service),
) -> Dict[str, Any]:
    """Get objects of a configuration."""
    if not config_name or len(config_name) > 200:
        raise HTTPException(status_code=400, detail="Invalid config_name")

    try:
        objects = await service.get_objects(config_name, object_type)
        return {"objects": objects}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve objects: {str(e)}")


@router.post("/graph/dependencies")
async def get_function_dependencies(
    request: FunctionDependenciesRequest,
    service: GraphService = Depends(get_graph_service),
) -> Any:
    """Get function call graph."""
    try:
        result = await service.get_function_dependencies(request.module_name, request.function_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/semantic")
async def semantic_search(
    request: SemanticSearchRequest,
    service: VectorSearchService = Depends(get_vector_search_service),
) -> Dict[str, Any]:
    """Semantic code search using Qdrant."""
    try:
        results = await service.semantic_search(request.query, request.configuration, request.limit)
        return {"results": results}
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/stats/overview")
async def get_stats_overview(
    neo4j_client: Optional[Neo4jClient] = Depends(get_neo4j_client),
    qdrant_client: Optional[QdrantClient] = Depends(get_qdrant_client),
    pg_client: Optional[PostgreSQLSaver] = Depends(get_postgres_client),
) -> Dict[str, Any]:
    """Get overall statistics."""
    stats = {}

    try:
        if neo4j_client:
            graph_service = GraphService(neo4j_client)
            stats["neo4j"] = await graph_service.get_statistics()

        if qdrant_client:
            stats["qdrant"] = qdrant_client.get_statistics()

        if pg_client:
            stats["postgresql"] = pg_client.get_statistics()

        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
