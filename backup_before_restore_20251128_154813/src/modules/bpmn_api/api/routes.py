from typing import Any, Dict, List

import asyncpg
from fastapi import APIRouter, Depends, HTTPException

from src.database import get_db_pool
from src.modules.bpmn_api.domain.models import SaveDiagramRequest
from src.modules.bpmn_api.services.bpmn_service import BPMNService

router = APIRouter(tags=["BPMN"])


def get_bpmn_service(
    db_pool: asyncpg.Pool = Depends(get_db_pool),
) -> BPMNService:
    return BPMNService(db_pool)


@router.get("/diagrams")
async def list_diagrams(
    project_id: str | None = None, service: BPMNService = Depends(get_bpmn_service)
) -> List[Dict[str, Any]]:
    """List all BPMN diagrams."""
    try:


@router.post("/diagrams")
async def save_diagram(request: SaveDiagramRequest, service: BPMNService = Depends(
        get_bpmn_service)) -> Dict[str, Any]:
    """Save new BPMN diagram."""
    try:


@router.put("/diagrams/{diagram_id}")
async def update_diagram(
    diagram_id: str,
    request: SaveDiagramRequest,
    service: BPMNService = Depends(get_bpmn_service),
) -> Dict[str, Any]:
    """Update existing BPMN diagram."""
    try:


@router.delete("/diagrams/{diagram_id}")
async def delete_diagram(diagram_id: str, service: BPMNService = Depends(
        get_bpmn_service)) -> Dict[str, Any]:
    """Delete BPMN diagram."""
    try:
