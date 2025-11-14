"""
Graph API - FastAPI endpoints for Neo4j, Qdrant, PostgreSQL
Версия: 2.1.0

Улучшения:
- Input validation и sanitization
- Structured logging
- Улучшена обработка ошибок
- Защита от Cypher injection
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
import logging
import re

from src.db.neo4j_client import Neo4jClient
from src.db.qdrant_client import QdrantClient
from src.db.postgres_saver import PostgreSQLSaver
from src.services.embedding_service import EmbeddingService
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

app = FastAPI(
    title="1C AI Assistant API",
    description="Enterprise 1C AI Development Stack API",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080"
    ],  # Only allow specific origins for security
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Clients
neo4j_client = None
qdrant_client = None
pg_client = None
embedding_service = None


# Models
class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="Search query")
    configuration: Optional[str] = Field(None, max_length=200, description="Configuration filter")
    limit: int = Field(10, ge=1, le=100, description="Maximum results")
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Sanitize query to prevent injection"""
        # Remove potentially dangerous characters
        v = re.sub(r'[<>"\']', '', v)
        return v.strip()
    
    @field_validator('configuration')
    @classmethod
    def validate_configuration(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize configuration name"""
        if v:
            # Prevent path traversal
            v = v.replace('..', '').replace('/', '').replace('\\', '')
            return v.strip()
        return v


class GraphQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=5000, description="Cypher query")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Query parameters")
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Basic validation for Cypher query (prevent dangerous operations)"""
        v = v.strip()
        
        # Block dangerous operations
        dangerous_patterns = [
            r'\bDROP\b',
            r'\bDELETE\b',
            r'\bDETACH\b',
            r'\bREMOVE\b',
            r'\bCREATE\s+INDEX\b',
            r'\bCREATE\s+CONSTRAINT\b'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError(f"Dangerous operation detected in query: {pattern}")
        
        return v


class FunctionDependenciesRequest(BaseModel):
    module_name: str = Field(..., min_length=1, max_length=200, description="Module name")
    function_name: str = Field(..., min_length=1, max_length=200, description="Function name")
    
    @field_validator('module_name', 'function_name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Sanitize name to prevent injection"""
        # Allow only alphanumeric, underscore, dot, dash
        if not re.match(r'^[a-zA-Z0-9_.-]+$', v):
            raise ValueError("Invalid characters in name")
        return v.strip()


# Startup/Shutdown
@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    global neo4j_client, qdrant_client, pg_client, embedding_service
    
    try:
        # Neo4j
        neo4j_client = Neo4jClient()
        neo4j_client.connect()
        
        # Qdrant
        qdrant_client = QdrantClient()
        qdrant_client.connect()
        
        # PostgreSQL
        pg_client = PostgreSQLSaver()
        pg_client.connect()
        
        # Embeddings
        embedding_service = EmbeddingService()
        
        logger.info(
            "All services initialized",
            extra={
                "neo4j": neo4j_client is not None,
                "qdrant": qdrant_client is not None,
                "postgres": pg_client is not None,
                "embeddings": embedding_service is not None
            }
        )
    except Exception as e:
        logger.error(
            f"Startup error: {e}",
            extra={"error_type": type(e).__name__},
            exc_info=True
        )


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if neo4j_client:
        neo4j_client.disconnect()
    if pg_client:
        pg_client.disconnect()


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "neo4j": neo4j_client is not None,
            "qdrant": qdrant_client is not None,
            "postgres": pg_client is not None
        }
    }


# Graph API endpoints
@app.post("/api/graph/query")
async def execute_graph_query(request: GraphQueryRequest):
    """
    Execute custom Cypher query
    
    Security: Only SELECT/MATCH queries allowed, dangerous operations blocked
    """
    if not neo4j_client:
        logger.warning("Neo4j not available for graph query")
        raise HTTPException(status_code=503, detail="Neo4j not available")
    
    try:
        # Additional validation: ensure query starts with MATCH or RETURN
        query_upper = request.query.strip().upper()
        if not (query_upper.startswith('MATCH') or query_upper.startswith('RETURN')):
            logger.warning(
                "Invalid query type attempted",
                extra={"query_preview": request.query[:100]}
            )
            raise HTTPException(
                status_code=400,
                detail="Only MATCH and RETURN queries are allowed"
            )
        
        with neo4j_client.driver.session() as session:
            result = session.run(request.query, request.parameters)
            records = [dict(record) for record in result]
        
        logger.info(
            "Graph query executed successfully",
            extra={
                "query_length": len(request.query),
                "results_count": len(records),
                "has_parameters": bool(request.parameters)
            }
        )
        return {"results": records}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Graph query error: {e}",
            extra={
                "query_length": len(request.query),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Query execution failed: {str(e)}"
        )


@app.get("/api/graph/configurations")
async def get_configurations():
    """Get all configurations"""
    if not neo4j_client:
        raise HTTPException(status_code=503, detail="Neo4j not available")
    
    try:
        with neo4j_client.driver.session() as session:
            result = session.run("""
                MATCH (c:Configuration)
                RETURN c.name as name, c.full_name as full_name, c.version as version
                ORDER BY c.name
            """)
            configs = [dict(record) for record in result]
        return {"configurations": configs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/graph/objects/{config_name}")
async def get_objects(
    config_name: str,
    object_type: Optional[str] = Query(None, max_length=100, description="Filter by object type")
):
    """
    Get objects of a configuration
    
    Security: Input sanitization to prevent injection
    """
    # Input validation
    if not config_name or len(config_name) > 200:
        raise HTTPException(status_code=400, detail="Invalid config_name")
    
    # Sanitize config_name (prevent injection)
    config_name = re.sub(r'[^a-zA-Z0-9_.-]', '', config_name)
    
    if object_type:
        # Sanitize object_type
        object_type = re.sub(r'[^a-zA-Z0-9_.-]', '', object_type)
    
    if not neo4j_client:
        logger.warning("Neo4j not available for get_objects")
        raise HTTPException(status_code=503, detail="Neo4j not available")
    
    try:
        if object_type:
            objects = neo4j_client.search_objects_by_type(object_type, config_name)
        else:
            with neo4j_client.driver.session() as session:
                result = session.run("""
                    MATCH (c:Configuration {name: $config})-[:HAS_OBJECT]->(o:Object)
                    RETURN o.type as type, o.name as name, o.description as description
                    ORDER BY o.type, o.name
                """, config=config_name)
                objects = [dict(record) for record in result]
        
        logger.info(
            "Objects retrieved successfully",
            extra={
                "config_name": config_name,
                "object_type": object_type,
                "objects_count": len(objects)
            }
        )
        return {"objects": objects}
    except Exception as e:
        logger.error(
            f"Error getting objects: {e}",
            extra={
                "config_name": config_name,
                "object_type": object_type,
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Failed to retrieve objects: {str(e)}")


@app.post("/api/graph/dependencies")
async def get_function_dependencies(request: FunctionDependenciesRequest):
    """Get function call graph"""
    if not neo4j_client:
        raise HTTPException(status_code=503, detail="Neo4j not available")
    
    try:
        dependencies = neo4j_client.get_function_dependencies(
            request.module_name,
            request.function_name
        )
        
        callers = neo4j_client.get_function_callers(
            request.module_name,
            request.function_name
        )
        
        return {
            "function": {
                "module": request.module_name,
                "name": request.function_name
            },
            "calls_to": dependencies,
            "called_by": callers
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Vector search endpoints
@app.post("/api/search/semantic")
async def semantic_search(request: SemanticSearchRequest):
    """
    Semantic code search using Qdrant
    
    Security: Input validation and sanitization
    """
    if not qdrant_client or not embedding_service:
        logger.warning("Vector search not available")
        raise HTTPException(status_code=503, detail="Vector search not available")
    
    try:
        # Generate query embedding
        query_vector = embedding_service.encode(request.query)
        
        # Search in Qdrant
        results = qdrant_client.search_code(
            query_vector=query_vector,
            config_filter=request.configuration,
            limit=request.limit
        )
        
        logger.info(
            "Semantic search completed",
            extra={
                "query_length": len(request.query),
                "configuration": request.configuration,
                "limit": request.limit,
                "results_count": len(results)
            }
        )
        return {"results": results}
    except Exception as e:
        logger.error(
            f"Semantic search error: {e}",
            extra={
                "query_length": len(request.query),
                "configuration": request.configuration,
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


# Statistics endpoints
@app.get("/api/stats/overview")
async def get_stats_overview():
    """Get overall statistics"""
    stats = {}
    
    try:
        if neo4j_client:
            stats['neo4j'] = neo4j_client.get_statistics()
        
        if qdrant_client:
            stats['qdrant'] = qdrant_client.get_statistics()
        
        if pg_client:
            stats['postgresql'] = pg_client.get_statistics()
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)







