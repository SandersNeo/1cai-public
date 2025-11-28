"""
Wiki API Routes - Minimal Implementation

This module provides basic wiki functionality.
Full implementation is in src/modules/wiki/
"""

from fastapi import APIRouter

router = APIRouter(tags=["Wiki"])


@router.get("/health")
async def health_check():
    """Wiki service health check"""
    return {
        "status": "healthy",
        "service": "wiki",
        "version": "1.0.0",
    }


@router.get("/")
async def list_pages():
    """List all wiki pages"""
    return {
        "pages": [],
        "total": 0,
        "message": "Wiki service is operational",
    }
