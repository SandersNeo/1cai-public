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
        async with db_pool.acquire() as conn:
            return await executive_service.get_dashboard(conn)
    except Exception as e:
        logger.error(
            "Error fetching executive dashboard",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pm")
async def get_pm_dashboard(
    db_pool: asyncpg.Pool = Depends(get_db_pool),
) -> Dict[str, Any]:
    """
    PM Dashboard Data

    Returns projects, timeline, team workload
    """
    try:
        async with db_pool.acquire() as conn:
            return await pm_service.get_dashboard(conn)
    except Exception as e:
        logger.error(
            "Error fetching PM dashboard",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/developer")
async def get_developer_dashboard() -> Dict[str, Any]:
    """
    Developer Dashboard Data

    Returns assigned tasks, code reviews, build status
    """
    try:
        return await developer_service.get_dashboard()
    except Exception as e:
        logger.error(
            "Error fetching developer dashboard",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/team-lead")
async def get_team_lead_dashboard(
    db_pool: asyncpg.Pool = Depends(get_db_pool),
) -> Dict[str, Any]:
    """
    Team Lead Dashboard

    Shows team performance, code quality, velocity, technical debt
    """
    try:
        async with db_pool.acquire() as conn:
            return await team_lead_service.get_dashboard(conn)
    except Exception as e:
        logger.error(
            "Error fetching team lead dashboard",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ba")
async def get_ba_dashboard(
    db_pool: asyncpg.Pool = Depends(get_db_pool),
) -> Dict[str, Any]:
    """
    Business Analyst Dashboard

    Shows requirements, traceability, gap analysis, process diagrams
    """
    try:
        async with db_pool.acquire() as conn:
            return await ba_service.get_dashboard(conn)
    except Exception as e:
        logger.error(
            "Error fetching BA dashboard",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/owner")
async def get_owner_dashboard(
    db_pool: asyncpg.Pool = Depends(get_db_pool),
) -> Dict[str, Any]:
    """
    Owner Dashboard

    Returns simple business metrics in plain language
    """
    try:
        async with db_pool.acquire() as conn:
            return await owner_service.get_dashboard(conn)
    except Exception as e:
        logger.error(
            "Error fetching owner dashboard",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))
