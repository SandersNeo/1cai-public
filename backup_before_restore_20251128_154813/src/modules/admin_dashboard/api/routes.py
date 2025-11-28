import asyncpg
from fastapi import APIRouter, Depends

from src.modules.admin_dashboard.services.admin_service import AdminDashboardService

router = APIRouter(tags=["Admin Dashboard"])


def get_db_pool():
    from src.database import get_pool

    return get_pool()


def get_admin_service(
    db_pool: asyncpg.Pool = Depends(get_db_pool),
) -> AdminDashboardService:
    return AdminDashboardService(db_pool)


@router.get("/stats")
async def get_platform_stats(
    service: AdminDashboardService = Depends(get_admin_service),
):
    """Platform statistics."""
    return await service.get_platform_stats()


@router.get("/tenants/{tenant_id}")
async def get_tenant_details(
    tenant_id: str, service: AdminDashboardService = Depends(get_admin_service)
):
    """Tenant details."""
    return await service.get_tenant_details(tenant_id)
