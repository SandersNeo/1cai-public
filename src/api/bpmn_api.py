"""
BPMN API
Backend for BPMN diagram management
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
import asyncpg
from src.utils.structured_logging import StructuredLogger

from src.database import get_db_pool

logger = StructuredLogger(__name__).logger

router = APIRouter(prefix="/api/bpmn", tags=["BPMN"])


class BPMNDiagram(BaseModel):
    id: str
    name: str
    description: str
    xml: str
    project_id: str | None = None


class SaveDiagramRequest(BaseModel):
    name: str
    description: str
    xml: str
    project_id: str | None = None


@router.get("/diagrams")
async def list_diagrams(
    project_id: str | None = None,
    db_pool: asyncpg.Pool = Depends(get_db_pool)
) -> List[Dict[str, Any]]:
    """
    List all BPMN diagrams
    
    Optionally filter by project
    """
    
    try:
        async with db_pool.acquire() as conn:
            tenant_id = await conn.fetchval("SELECT id FROM tenants LIMIT 1")
            
            if not tenant_id:
                return []
            
            if project_id:
                diagrams = await conn.fetch(
                    """
                    SELECT id, name, description, created_at, updated_at
                    FROM bpmn_diagrams
                    WHERE tenant_id = $1 AND project_id = $2
                    ORDER BY updated_at DESC
                    """,
                    tenant_id, project_id
                )
            else:
                diagrams = await conn.fetch(
                    """
                    SELECT id, name, description, created_at, updated_at
                    FROM bpmn_diagrams
                    WHERE tenant_id = $1
                    ORDER BY updated_at DESC
                    LIMIT 50
                    """,
                    tenant_id
                )
            
            return [
                {
                    "id": str(row["id"]),
                    "name": row["name"],
                    "description": row["description"],
                    "created_at": row["created_at"].isoformat(),
                    "updated_at": row["updated_at"].isoformat()
                }
                for row in diagrams
            ]
    
    except Exception as e:
        logger.error(
            "Error listing diagrams",
            extra={
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/diagrams/{diagram_id}")
async def get_diagram(
    diagram_id: str,
    db_pool: asyncpg.Pool = Depends(get_db_pool)
) -> Dict[str, Any]:
    """Get specific BPMN diagram"""
    
    try:
        async with db_pool.acquire() as conn:
            diagram = await conn.fetchrow(
                """
                SELECT id, name, description, xml_content, project_id, created_at, updated_at
                FROM bpmn_diagrams
                WHERE id = $1
                """,
                diagram_id
            )
            
            if not diagram:
                raise HTTPException(status_code=404, detail="Diagram not found")
            
            return {
                "id": str(diagram["id"]),
                "name": diagram["name"],
                "description": diagram["description"],
                "xml": diagram["xml_content"],
                "project_id": str(diagram["project_id"]) if diagram["project_id"] else None,
                "created_at": diagram["created_at"].isoformat(),
                "updated_at": diagram["updated_at"].isoformat()
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting diagram",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "diagram_id": diagram_id if 'diagram_id' in locals() else None
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/diagrams")
async def save_diagram(
    request: SaveDiagramRequest,
    db_pool: asyncpg.Pool = Depends(get_db_pool)
) -> Dict[str, Any]:
    """Save new or update existing BPMN diagram"""
    
    try:
        async with db_pool.acquire() as conn:
            tenant_id = await conn.fetchval("SELECT id FROM tenants LIMIT 1")
            
            if not tenant_id:
                raise HTTPException(status_code=400, detail="No tenant found")
            
            # Insert diagram
            diagram_id = await conn.fetchval(
                """
                INSERT INTO bpmn_diagrams 
                (tenant_id, name, description, xml_content, project_id, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
                RETURNING id
                """,
                tenant_id,
                request.name,
                request.description,
                request.xml,
                request.project_id
            )
            
            logger.info(
                "Saved BPMN diagram",
                extra={"diagram_id": str(diagram_id)}
            )
            
            return {
                "id": str(diagram_id),
                "message": "Diagram saved successfully"
            }
    
    except Exception as e:
        logger.error(
            "Error saving diagram",
            extra={
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/diagrams/{diagram_id}")
async def update_diagram(
    diagram_id: str,
    request: SaveDiagramRequest,
    db_pool: asyncpg.Pool = Depends(get_db_pool)
) -> Dict[str, Any]:
    """Update existing BPMN diagram"""
    
    try:
        async with db_pool.acquire() as conn:
            updated = await conn.execute(
                """
                UPDATE bpmn_diagrams
                SET name = $1,
                    description = $2,
                    xml_content = $3,
                    updated_at = NOW()
                WHERE id = $4
                """,
                request.name,
                request.description,
                request.xml,
                diagram_id
            )
            
            if updated == "UPDATE 0":
                raise HTTPException(status_code=404, detail="Diagram not found")
            
            return {
                "id": diagram_id,
                "message": "Diagram updated successfully"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error updating diagram",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "diagram_id": diagram_id if 'diagram_id' in locals() else None
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/diagrams/{diagram_id}")
async def delete_diagram(
    diagram_id: str,
    db_pool: asyncpg.Pool = Depends(get_db_pool)
) -> Dict[str, Any]:
    """Delete BPMN diagram"""
    
    try:
        async with db_pool.acquire() as conn:
            deleted = await conn.execute(
                "DELETE FROM bpmn_diagrams WHERE id = $1",
                diagram_id
            )
            
            if deleted == "DELETE 0":
                raise HTTPException(status_code=404, detail="Diagram not found")
            
            return {"message": "Diagram deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error deleting diagram",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "diagram_id": diagram_id if 'diagram_id' in locals() else None
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


