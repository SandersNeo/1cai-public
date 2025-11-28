# [NEXUS IDENTITY] ID: -2577113494422445642 | DATE: 2025-11-19

"""
Debug Endpoints (Development Only)
Iteration 2 Quick Win #5: Easier troubleshooting
"""

import os
from typing import Any, Dict

import psutil
from fastapi import APIRouter, Depends, HTTPException

from src.config import settings
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

router = APIRouter(prefix="/debug", tags=["Debug"])


async def verify_dev_environment():
    """Ensure debug endpoints only work in development"""
    if settings.environment != "development":
        raise HTTPException(
            status_code=403,
            detail="Debug endpoints are only available in development mode",
        )


@router.get("/config")
async def get_config(_=Depends(verify_dev_environment)) -> Dict[str, Any]:
    """
    Show current configuration (sanitized)

    Available only in development mode
    """
    return {
        "environment": settings.environment,
        "database_url": (
            settings.database_url.split("@")[1]
            if "@" in settings.database_url
            else "***"
        ),  # Hide credentials
        "redis_url": (
            settings.redis_url.split("@")[1]
            if "@" in settings.redis_url
            else settings.redis_url
        ),
        "cors_origins": settings.get_cors_origins(),
        "log_level": "INFO",
        "jwt_configured": bool(settings.jwt_secret_key),
        "openai_configured": bool(
            settings.openai_api_key and settings.openai_api_key != "test"
        ),
    }


@router.get("/state")
async def get_app_state(_=Depends(verify_dev_environment)) -> Dict[str, Any]:
    """
    Get current application state

    Useful for debugging
    """

    # System resources
    memory = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=0.1)
    disk = psutil.disk_usage("/")

    # Process info
    process = psutil.Process()

    return {
        "system": {
            "cpu_percent": cpu,
            "memory_percent": memory.percent,
            "memory_available_gb": round(memory.available / 1024**3, 2),
            "disk_percent": disk.percent,
            "disk_free_gb": round(disk.free / 1024**3, 2),
        },
        "process": {
            "cpu_percent": process.cpu_percent(),
            "memory_mb": round(process.memory_info().rss / 1024**2, 2),
            "threads": process.num_threads(),
            "open_files": len(process.open_files()),
        },
        "environment": {
            "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}",
            "platform": os.sys.platform,
        },
    }


@router.get("/routes")
async def list_routes(_=Depends(verify_dev_environment)) -> Dict[str, Any]:
    """List all registered API routes"""

    from src.main import app

    routes = []
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            routes.append(
                {
                    "path": route.path,
                    "methods": list(route.methods),
                    "name": route.name,
                }
            )

    return {
        "total_routes": len(routes),
        "routes": sorted(routes, key=lambda x: x["path"]),
    }


@router.post("/cache/clear")
async def clear_cache(_=Depends(verify_dev_environment)) -> Dict[str, str]:
    """Clear all caches"""

    try:
