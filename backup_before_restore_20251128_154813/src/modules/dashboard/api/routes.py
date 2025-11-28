"""
Dashboard API Routes
FastAPI endpoints for all dashboard types
"""
from typing import Any, Dict

import asyncpg
from fastapi import APIRouter, Depends, HTTPException

from src.database import get_db_pool
from src.infrastructure.logging.structured_logging import StructuredLogger
from src.modules.dashboard.services.ba_service import BAService
from src.modules.dashboard.services.developer_service import DeveloperService
from src.modules.dashboard.services.executive_service import ExecutiveService
from src.modules.dashboard.services.owner_service import OwnerService
from src.modules.dashboard.services.pm_service import PMService
from src.modules.dashboard.services.team_lead_service import TeamLeadService

logger = StructuredLogger(__name__).logger

# Create router
router = APIRouter(tags=["Dashboards"])

# Initialize services
executive_service = ExecutiveService()
pm_service = PMService()
developer_service = DeveloperService()
team_lead_service = TeamLeadService()
ba_service = BAService()
owner_service = OwnerService()


@router.get("/executive")
async def get_executive_dashboard(
    db_pool: asyncpg.Pool = Depends(get_db_pool),
) -> Dict[str, Any]:
    """
    Executive Dashboard Data

    Returns high-level KPIs and business metrics
    """
    try:
