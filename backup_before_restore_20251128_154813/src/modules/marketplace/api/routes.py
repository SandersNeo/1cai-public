from typing import Any, Dict, List, Optional

from fastapi import (APIRouter, Depends, File, HTTPException, Query, Response,
                     UploadFile)
from starlette.requests import Request

from src.db.marketplace_repository import MarketplaceRepository
from src.middleware.rate_limiter import limiter
from src.modules.marketplace.domain.models import (PluginCategory,
                                                   PluginResponse,
                                                   PluginReviewRequest,
                                                   PluginReviewResponse,
                                                   PluginSearchResponse,
                                                   PluginStatsResponse,
                                                   PluginSubmitRequest,
                                                   PluginUpdateRequest)
from src.modules.marketplace.services.marketplace_service import \
    MarketplaceService
from src.security import CurrentUser, get_current_user, require_roles

router = APIRouter(prefix="/marketplace", tags=["marketplace"])


def get_marketplace_repository(request: Request) -> MarketplaceRepository:
    repo = getattr(request.app.state, "marketplace_repo", None)
    if repo is None:
        raise RuntimeError("Marketplace repository is not initialized")
    return repo


def get_marketplace_service(
    repo: MarketplaceRepository = Depends(get_marketplace_repository),
) -> MarketplaceService:
    return MarketplaceService(repo)


@router.post(
    "/plugins",
    response_model=PluginResponse,
    status_code=201,
    summary="Submit a new plugin",
)
@limiter.limit("5/minute")
async def submit_plugin(
    request: Request,
    response: Response,
    plugin: PluginSubmitRequest,
    current_user: CurrentUser = Depends(require_roles("developer", "admin")),
    service: MarketplaceService = Depends(get_marketplace_service),
):
    try:


@router.post("/plugins/{plugin_id}/artifact",
             response_model=PluginResponse, status_code=201)
@limiter.limit("10/minute")
async def upload_plugin_artifact(
    request: Request,
    response: Response,
    plugin_id: str,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    service: MarketplaceService = Depends(get_marketplace_service),
):
    try:
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to store artifact")


@router.delete("/plugins/{plugin_id}")
async def delete_plugin(
    plugin_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: MarketplaceService = Depends(get_marketplace_service),
):
    try:


@router.get("/plugins/{plugin_id}/reviews")
async def get_plugin_reviews(
    plugin_id: str,
    page: int = 1,
    page_size: int = 10,
    service: MarketplaceService = Depends(get_marketplace_service),
) -> Dict[str, Any]:
    try:
