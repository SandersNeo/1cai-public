import asyncpg
from fastapi import APIRouter, Depends, HTTPException

from src.modules.tenant_management.domain.models import \
    TenantRegistrationRequest
from src.modules.tenant_management.services.tenant_service import \
    TenantManagementService

router = APIRouter(tags=["Tenant Management"])


def get_db_pool():
    """DB pool dependency."""
    from src.database import get_pool

    return get_pool()


def get_tenant_service(
    db_pool: asyncpg.Pool = Depends(get_db_pool),
) -> TenantManagementService:
    return TenantManagementService(db_pool)


@router.post("/register")
async def register_tenant(
    registration: TenantRegistrationRequest,
    service: TenantManagementService = Depends(get_tenant_service),
):
    """Register new tenant."""
    try:
