"""
Metrics API Routes
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.infrastructure.logging.structured_logging import StructuredLogger
from src.modules.metrics.domain.models import MetricCollectionRequest
from src.modules.metrics.services.metrics_service import MetricsService

logger = StructuredLogger(__name__).logger

router = APIRouter(tags=["Metrics"])
limiter = Limiter(key_func=get_remote_address)


# Dependency
def get_metrics_service() -> MetricsService:
    return MetricsService()


@router.get("/health", summary="Check API health")
async def health_check():
    """Check Metrics API health"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "version": "1.0.0",
    }


@router.post("/collect", summary="Collect metrics")
@limiter.limit("100/minute")
async def collect_metrics(
    request: MetricCollectionRequest,
    service: MetricsService = Depends(get_metrics_service),
):
    """
    Collect metrics from services
    """
    try:
