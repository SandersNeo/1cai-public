# [NEXUS IDENTITY] ID: 8105445309231271486 | DATE: 2025-11-19

"""
Admin Dashboard API
API для админ панели SaaS платформы
"""

import logging
from datetime import datetime
from typing import Dict

import asyncpg
from fastapi import APIRouter, Depends, HTTPException

from src.monitoring.performance_monitor import performance_monitor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin")


class AdminDashboardService:
    """Сервис для admin dashboard"""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db = db_pool

    async def get_platform_stats(self) -> Dict:
        """
        Статистика всей платформы

        Returns:
            {
                'tenants': {...},
                'users': {...},
                'revenue': {...},
                'usage': {...}
            }
        """

        async with self.db.acquire() as conn:
            # Tenants stats
            tenants_stats = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'trial') as trial,
                    COUNT(*) FILTER (WHERE status = 'active') as active,
                    COUNT(*) FILTER (WHERE status = 'suspended') as suspended,
                    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '30 days') as new_last_30d
                FROM tenants
            """
            )

            # Users stats
            users_stats = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as total,
                    COUNT(DISTINCT tenant_id) as active_tenants,
                    COUNT(*) FILTER (WHERE last_login_at >= NOW() - INTERVAL '7 days') as active_7d
                FROM users
            """
            )

            # Revenue stats (упрощенно)
            revenue_stats = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as total_subscriptions,
                    COUNT(*) FILTER (WHERE plan = 'starter') as starter_count,
                    COUNT(*) FILTER (WHERE plan = 'professional') as pro_count,
                    COUNT(*) FILTER (WHERE plan = 'enterprise') as ent_count
                FROM tenants
                WHERE status = 'active'
            """
            )

            # Calculate MRR (Monthly Recurring Revenue)
            mrr = (
                revenue_stats["starter_count"] * 99
                + revenue_stats["pro_count"] * 299
                + revenue_stats["ent_count"] * 999
            )

            # Usage stats
            usage_stats = await conn.fetchrow(
                """
                SELECT
                    SUM(api_calls) as total_api_calls,
                    SUM(ai_tokens_used) as total_tokens,
                    AVG(storage_used_mb) as avg_storage_mb
                FROM usage_tracking
                WHERE date >= DATE_TRUNC('month', CURRENT_DATE)
            """
            )

        return {
            "tenants": dict(tenants_stats),
            "users": dict(users_stats),
            "revenue": {
                "mrr": mrr,
                "arr": mrr * 12,
                "by_plan": {
                    "starter": revenue_stats["starter_count"],
                    "professional": revenue_stats["pro_count"],
                    "enterprise": revenue_stats["ent_count"],
                },
            },
            "usage": dict(usage_stats) if usage_stats["total_api_calls"] else {},
            "performance": performance_monitor.get_metrics(),
            "generated_at": datetime.now().isoformat(),
        }

    async def get_tenant_details(self, tenant_id: str) -> Dict:
        """Детальная информация о tenant"""

        async with self.db.acquire() as conn:
            # Tenant info
            tenant = await conn.fetchrow(
                """
                SELECT * FROM tenants WHERE id = $1
            """,
                tenant_id,
            )

            if not tenant:
                raise HTTPException(status_code=404, detail="Tenant not found")

            # Users
            users = await conn.fetch(
                """
                SELECT id, email, name, role, last_login_at
                FROM users
                WHERE tenant_id = $1
            """,
                tenant_id,
            )

            # Usage (last 30 days)
            usage = await conn.fetch(
                """
                SELECT date, api_calls, ai_tokens_used, storage_used_mb
                FROM usage_tracking
                WHERE tenant_id = $1
                  AND date >= CURRENT_DATE - INTERVAL '30 days'
                ORDER BY date DESC
            """,
                tenant_id,
            )

            # Billing events
            billing = await conn.fetch(
                """
                SELECT event_type, amount_cents, currency, created_at
                FROM billing_events
                WHERE tenant_id = $1
                ORDER BY created_at DESC
                LIMIT 20
            """,
                tenant_id,
            )

        return {
            "tenant": dict(tenant),
            "users": [dict(u) for u in users],
            "usage_history": [dict(u) for u in usage],
            "billing_history": [dict(b) for b in billing],
        }


# FastAPI endpoints


@router.get("/stats")
async def get_platform_stats(db_pool: asyncpg.Pool = Depends(lambda: get_db_pool())):
    """Общая статистика платформы"""

    service = AdminDashboardService(db_pool)
    stats = await service.get_platform_stats()

    return stats


@router.get("/tenants/{tenant_id}")
async def get_tenant_details(
    tenant_id: str, db_pool: asyncpg.Pool = Depends(lambda: get_db_pool())
):
    """Детали конкретного tenant"""

    service = AdminDashboardService(db_pool)
    details = await service.get_tenant_details(tenant_id)

    return details


def get_db_pool():
    """Dependency injection для DB pool"""
    from src.database import get_pool

    return get_pool()
