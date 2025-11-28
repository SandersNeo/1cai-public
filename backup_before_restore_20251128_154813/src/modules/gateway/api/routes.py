"""
Gateway API Routes
"""
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, Request

from src.infrastructure.logging.structured_logging import StructuredLogger
from src.modules.gateway.domain.config import SERVICES_CONFIG
from src.modules.gateway.domain.models import (GatewayHealthResponse,
                                               GatewayMetrics, ServiceRequest)
from src.modules.gateway.services.health_checker import ServiceHealthChecker
from src.modules.gateway.services.middleware.auth import \
    AuthenticationMiddleware
from src.modules.gateway.services.proxy_service import ProxyService

logger = StructuredLogger(__name__).logger

router = APIRouter(tags=["Gateway"])

# Initialize services
health_checker = ServiceHealthChecker()
proxy_service = ProxyService()


@router.get("/health", response_model=GatewayHealthResponse)
async def get_gateway_health():
    """Get gateway health status"""
    services_health = await health_checker.check_all_services()

    # Determine overall status
    overall_status = "healthy"
    for status in services_health.values():
        if status.status != "healthy":
            overall_status = "degraded"
            break

    return GatewayHealthResponse(
        gateway_status=overall_status,
        timestamp=datetime.now(),
        version="2.1.0",
        services={
            name: status.dict() for name,
            status in services_health.items()},
    )


@router.post("/proxy")
async def proxy_request(request: ServiceRequest):
    """Proxy request to a microservice"""
    return await proxy_service.proxy_request(
        service=request.service,
        endpoint=request.endpoint,
        method=request.method,
        headers=request.headers,
        data=request.data,
        params=request.params,
    )


@router.api_route("/{service}/{path:path}",
                  methods=["GET",
                           "POST",
                           "PUT",
                           "DELETE",
                           "PATCH",
                           "HEAD",
                           "OPTIONS"])
async def proxy_path(
    service: str,
    path: str,
    request: Request,
):
    """Dynamic proxy endpoint"""
    # Extract body if present
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
