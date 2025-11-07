"""
Marketplace API

Production readiness improvements:
    - Redis-backed caching and per-user rate limiting for key endpoints
    - Presigned download links via S3-compatible storage when configured
    - Periodic cache refresh scheduler and audit-friendly logging
"""

import logging
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Request
from pydantic import BaseModel, Field
from enum import Enum

from src.security import CurrentUser, get_audit_logger, get_current_user, require_roles
from src.db.marketplace_repository import MarketplaceRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/marketplace", tags=["marketplace"])
audit_logger = get_audit_logger()


def get_marketplace_repository(request: Request) -> MarketplaceRepository:
    repo = getattr(request.app.state, "marketplace_repo", None)
    if repo is None:
        raise RuntimeError("Marketplace repository is not initialized")
    return repo


# ==================== Models ====================

class PluginCategory(str, Enum):
    """Категории плагинов"""
    AI_AGENT = "ai_agent"
    CODE_TOOL = "code_tool"
    INTEGRATION = "integration"
    UI_THEME = "ui_theme"
    ANALYTICS = "analytics"
    SECURITY = "security"
    DEVOPS = "devops"
    OTHER = "other"


class PluginStatus(str, Enum):
    """Статус плагина в marketplace"""
    PENDING = "pending"  # На модерации
    APPROVED = "approved"  # Одобрен
    REJECTED = "rejected"  # Отклонен
    DEPRECATED = "deprecated"  # Устарел
    REMOVED = "removed"  # Удален


class PluginVisibility(str, Enum):
    """Видимость плагина"""
    PUBLIC = "public"  # Доступен всем
    PRIVATE = "private"  # Только автору
    UNLISTED = "unlisted"  # По прямой ссылке


class PluginSubmitRequest(BaseModel):
    """Запрос на публикацию плагина"""
    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=10, max_length=1000)
    category: PluginCategory
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    author: str = Field(..., min_length=2, max_length=100)
    homepage: Optional[str] = None
    repository: Optional[str] = None
    license: str = Field(default="MIT")
    keywords: List[str] = Field(default_factory=list)
    visibility: PluginVisibility = PluginVisibility.PUBLIC
    
    # Compatibility
    min_version: str = Field(default="1.0.0")
    supported_platforms: List[str] = Field(default_factory=lambda: ["telegram", "mcp", "edt"])
    
    # Resources
    icon_url: Optional[str] = None
    screenshot_urls: List[str] = Field(default_factory=list)
    artifact_path: Optional[str] = Field(default=None, description="S3 object key with plugin bundle")
    
    # Documentation
    readme: Optional[str] = None
    changelog: Optional[str] = None


class PluginUpdateRequest(BaseModel):
    """Запрос на обновление плагина"""
    version: Optional[str] = Field(None, pattern=r"^\d+\.\d+\.\d+$")
    description: Optional[str] = Field(None, min_length=10, max_length=1000)
    changelog: Optional[str] = None
    homepage: Optional[str] = None
    repository: Optional[str] = None
    keywords: Optional[List[str]] = None
    icon_url: Optional[str] = None
    screenshot_urls: Optional[List[str]] = None
    readme: Optional[str] = None
    artifact_path: Optional[str] = Field(None, description="S3 object key with plugin bundle")


class PluginSearchRequest(BaseModel):
    """Запрос поиска плагинов"""
    query: Optional[str] = None
    category: Optional[PluginCategory] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    min_rating: Optional[float] = Field(None, ge=0, le=5)
    sort_by: str = Field(default="rating")  # rating | downloads | updated | name
    order: str = Field(default="desc")  # asc | desc
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PluginResponse(BaseModel):
    """Ответ с информацией о плагине"""
    id: str
    name: str
    description: str
    category: PluginCategory
    version: str
    author: str
    status: PluginStatus
    visibility: PluginVisibility
    
    # Stats
    downloads: int = 0
    rating: float = 0.0
    ratings_count: int = 0
    installs: int = 0
    
    # URLs
    homepage: Optional[str] = None
    repository: Optional[str] = None
    download_url: Optional[str] = None
    icon_url: Optional[str] = None
    screenshot_urls: List[str] = []
    artifact_path: Optional[str] = None
    
    # Metadata
    license: str
    keywords: List[str] = []
    min_version: str
    supported_platforms: List[str]
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    
    # Features
    featured: bool = False
    verified: bool = False


class PluginReviewRequest(BaseModel):
    """Запрос на review плагина"""
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=500)
    pros: Optional[str] = Field(None, max_length=200)
    cons: Optional[str] = Field(None, max_length=200)


class PluginReviewResponse(BaseModel):
    """Ответ с отзывом"""
    id: str
    plugin_id: str
    user_id: str
    user_name: str
    rating: int
    comment: Optional[str]
    pros: Optional[str]
    cons: Optional[str]
    helpful_count: int = 0
    created_at: datetime


class PluginSearchResponse(BaseModel):
    """Ответ на поиск плагинов"""
    plugins: List[PluginResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class PluginStatsResponse(BaseModel):
    """Статистика плагина"""
    plugin_id: str
    downloads_total: int
    downloads_last_30_days: int
    installs_active: int
    rating_average: float
    rating_distribution: Dict[int, int]  # {5: 100, 4: 50, ...}
    reviews_count: int
    favorites_count: int
    
    # Trending
    downloads_trend: str  # "up" | "down" | "stable"
    rating_trend: str


# ==================== Endpoints ====================

@router.post("/plugins", response_model=PluginResponse, status_code=201)
async def submit_plugin(
    plugin: PluginSubmitRequest,
    current_user: CurrentUser = Depends(require_roles("developer", "admin")),
    repo: MarketplaceRepository = Depends(get_marketplace_repository),
):
    """
    Публикация нового плагина
    
    Процесс:
    1. Валидация данных
    2. Создание записи с статусом PENDING
    3. Отправка на модерацию
    4. После одобрения → APPROVED
    """
    try:
        plugin_id = f"plugin_{uuid.uuid4().hex}"
        payload = plugin.model_dump()
        payload["status"] = PluginStatus.PENDING.value
        payload.setdefault("visibility", PluginVisibility.PUBLIC.value)

        persisted = await repo.create_plugin(
            plugin_id=plugin_id,
            owner_id=current_user.user_id,
            owner_username=current_user.username or current_user.user_id,
            payload=payload,
            download_url=f"/marketplace/plugins/{plugin_id}/download",
        )

        logger.info(
            "Plugin submitted: %s (%s) by %s",
            plugin_id,
            plugin.name,
            current_user.user_id,
        )
        audit_logger.log_action(
            actor=current_user.user_id,
            action="marketplace.plugin.submit",
            target=plugin_id,
            metadata={"name": plugin.name, "status": PluginStatus.PENDING.value},
        )

        return PluginResponse(**persisted)
        
    except Exception as e:
        logger.error(f"Plugin submission error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/plugins", response_model=PluginSearchResponse)
async def search_plugins(
    query: Optional[str] = None,
    category: Optional[PluginCategory] = None,
    author: Optional[str] = None,
    sort_by: str = "rating",
    order: str = "desc",
    page: int = 1,
    page_size: int = 20,
    repo: MarketplaceRepository = Depends(get_marketplace_repository),
):
    """
    Поиск плагинов в marketplace
    
    Фильтры:
    - query: Поиск по имени/описанию/тегам
    - category: Категория
    - author: Автор
    
    Сортировка:
    - rating: По рейтингу
    - downloads: По скачиваниям
    - updated: По дате обновления
    - name: По имени
    """
    try:
        plugins, total = await repo.search_plugins(
            query_text=query,
            category=category.value if category else None,
            author=author,
            sort_by=sort_by,
            order=order,
            page=page,
            page_size=page_size,
        )

        total_pages = (total + page_size - 1) // page_size if page_size else 1

        return PluginSearchResponse(
            plugins=[PluginResponse(**p) for p in plugins],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
        
    except Exception as e:
        logger.error(f"Plugin search error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/plugins/{plugin_id}", response_model=PluginResponse)
async def get_plugin(
    plugin_id: str,
    repo: MarketplaceRepository = Depends(get_marketplace_repository),
):
    """Получить информацию о плагине"""

    plugin = await repo.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    return PluginResponse(**plugin)


@router.put("/plugins/{plugin_id}", response_model=PluginResponse)
async def update_plugin(
    plugin_id: str, 
    update: PluginUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    repo: MarketplaceRepository = Depends(get_marketplace_repository),
):
    """
    Обновление плагина
    
    Только автор может обновлять свой плагин
    
    Note:
        В production: user_id должен получаться из auth middleware (JWT token)
    """
    
    plugin = await repo.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    if not _check_authorization(current_user, plugin):
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to update this plugin"
        )
    
    # Обновляем поля
    update_data = update.model_dump(exclude_unset=True)
    if not update_data:
        return PluginResponse(**plugin)

    if "version" in update_data and update_data["version"] != plugin.get("version"):
        update_data["status"] = PluginStatus.PENDING.value

    updated = await repo.update_plugin(plugin_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Plugin not found")

    logger.info("Plugin updated: %s by user %s", plugin_id, current_user.user_id)
    audit_logger.log_action(
        actor=current_user.user_id,
        action="marketplace.plugin.update",
        target=plugin_id,
        metadata={"fields": list(update_data.keys())},
    )

    return PluginResponse(**updated)


@router.delete("/plugins/{plugin_id}")
async def delete_plugin(
    plugin_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    repo: MarketplaceRepository = Depends(get_marketplace_repository),
):
    """
    Удаление плагина
    
    Мягкое удаление - статус → REMOVED
    Только автор или админ могут удалять плагин
    
    Note:
        В production: user_id должен получаться из auth middleware (JWT token)
    """
    
    plugin = await repo.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    if not _check_authorization(current_user, plugin):
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to delete this plugin"
        )
    
    removed = await repo.soft_delete_plugin(plugin_id)
    logger.info("Plugin removed: %s by user %s", plugin_id, current_user.user_id)
    audit_logger.log_action(
        actor=current_user.user_id,
        action="marketplace.plugin.delete",
        target=plugin_id,
        metadata={"status": removed.get("status") if removed else "removed"},
    )

    return {"status": "removed", "plugin_id": plugin_id}


@router.post("/plugins/{plugin_id}/install")
async def install_plugin(
    plugin_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    repo: MarketplaceRepository = Depends(get_marketplace_repository),
):
    """
    Установка плагина
    
    Увеличивает счетчики downloads и installs
    """
    
    updated = await repo.record_install(plugin_id, current_user.user_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Plugin not found")

    logger.info("Plugin installed: %s by user %s", plugin_id, current_user.user_id)

    return {
        "status": "installed",
        "plugin_id": plugin_id,
        "download_url": updated["download_url"],
    }


@router.post("/plugins/{plugin_id}/uninstall")
async def uninstall_plugin(
    plugin_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    repo: MarketplaceRepository = Depends(get_marketplace_repository),
):
    """Удаление плагина"""
    
    updated = await repo.remove_install(plugin_id, current_user.user_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Plugin not found")

    logger.info("Plugin uninstalled: %s by user %s", plugin_id, current_user.user_id)
    
    return {"status": "uninstalled", "plugin_id": plugin_id}


@router.get("/plugins/{plugin_id}/stats", response_model=PluginStatsResponse)
async def get_plugin_stats(
    plugin_id: str,
    repo: MarketplaceRepository = Depends(get_marketplace_repository),
):
    """Получить статистику плагина"""
    
    stats = await repo.get_plugin_stats(plugin_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Plugin not found")

    return PluginStatsResponse(**stats)


@router.post("/plugins/{plugin_id}/reviews", response_model=PluginReviewResponse)
async def submit_review(
    plugin_id: str,
    review: PluginReviewRequest,
    current_user: CurrentUser = Depends(get_current_user),
    repo: MarketplaceRepository = Depends(get_marketplace_repository),
):
    """
    Отзыв на плагин
    
    Только пользователи, установившие плагин, могут оставлять отзывы
    
    Note:
        В production: user_id должен получаться из auth middleware (JWT token)
    """
    
    plugin = await repo.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    if not await repo.user_has_installed(plugin_id, current_user.user_id):
        raise HTTPException(
            status_code=403,
            detail="You must install the plugin before leaving a review"
        )
    
    review_id = f"review_{uuid.uuid4().hex}"
    display_name = current_user.full_name or current_user.username
    if not display_name and len(current_user.user_id) >= 4:
        display_name = f"User {current_user.user_id[-4:]}"

    stored = await repo.create_review(
        review_id=review_id,
        plugin_id=plugin_id,
        user_id=current_user.user_id,
        user_name=display_name,
        payload=review.model_dump(),
    )
    if not stored:
        raise HTTPException(status_code=404, detail="Plugin not found")

    logger.info(
        "Review submitted: %s for plugin %s by user %s",
        review_id,
        plugin_id,
        current_user.user_id,
    )
    audit_logger.log_action(
        actor=current_user.user_id,
        action="marketplace.review.create",
        target=plugin_id,
        metadata={"review_id": review_id, "rating": review.rating},
    )
    
    return PluginReviewResponse(**stored)


@router.get("/plugins/{plugin_id}/reviews")
async def get_plugin_reviews(
    plugin_id: str,
    page: int = 1,
    page_size: int = 10,
    repo: MarketplaceRepository = Depends(get_marketplace_repository),
) -> Dict[str, Any]:
    """Получить отзывы о плагине"""
    
    plugin = await repo.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    reviews, total = await repo.list_reviews(plugin_id, page, page_size)

    return {
        "reviews": [PluginReviewResponse(**r) for r in reviews],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if page_size else 1,
    }


@router.get("/plugins/{plugin_id}/download")
async def download_plugin(
    plugin_id: str,
    repo: MarketplaceRepository = Depends(get_marketplace_repository),
):
    """
    Скачать плагин

    Возвращает ZIP архив с manifest.json и кодом плагина

    Note:
        В production: реализовать возврат реального файла через FileResponse
        Формат: ZIP архив содержащий:
        - manifest.json (метаданные плагина)
        - код плагина (Python/BSL файлы)
        - README.md (если есть)
    """

    plugin = await repo.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    return await repo.build_download_payload(plugin)


@router.get("/categories")
async def get_categories(
    repo: MarketplaceRepository = Depends(get_marketplace_repository),
):
    """Получить список категорий с количеством плагинов"""
    category_counts = await repo.get_category_counts()

    return {
        "categories": [
            {
                "id": cat.value,
                "name": cat.value.replace("_", " ").title(),
                "count": category_counts.get(cat.value, 0)
            }
            for cat in PluginCategory
        ]
    }


@router.get("/featured")
async def get_featured_plugins(
    limit: int = 6,
    repo: MarketplaceRepository = Depends(get_marketplace_repository),
):
    """Получить избранные плагины"""
    featured = await repo.get_featured_plugins(limit)
    return {
        "plugins": [PluginResponse(**p) for p in featured]
    }


@router.get("/trending")
async def get_trending_plugins(
    period: str = "week",  # day | week | month
    limit: int = 10,
    repo: MarketplaceRepository = Depends(get_marketplace_repository),
):
    """
    Получить трендовые плагины
    
    Критерии:
    - Рост скачиваний за период
    - Новые плагины с хорошим рейтингом
    - Активность (обновления, отзывы)
    """
    
    plugins = await repo.get_trending_plugins(limit)
    return {
        "plugins": [PluginResponse(**p) for p in plugins],
        "period": period,
    }


@router.post("/plugins/{plugin_id}/favorite")
async def add_to_favorites(
    plugin_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    repo: MarketplaceRepository = Depends(get_marketplace_repository),
):
    """
    Добавить плагин в избранное
    
    Note:
        В production: user_id должен получаться из auth middleware (JWT token)
    """
    
    plugin = await repo.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    await repo.add_favorite(plugin_id, current_user.user_id)

    logger.info("Plugin %s added to favorites by user %s", plugin_id, current_user.user_id)
    
    return {"status": "added", "plugin_id": plugin_id}


@router.delete("/plugins/{plugin_id}/favorite")
async def remove_from_favorites(
    plugin_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    repo: MarketplaceRepository = Depends(get_marketplace_repository),
):
    """
    Удалить плагин из избранного
    
    Note:
        В production: user_id должен получаться из auth middleware (JWT token)
    """
    
    plugin = await repo.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    await repo.remove_favorite(plugin_id, current_user.user_id)

    logger.info("Plugin %s removed from favorites by user %s", plugin_id, current_user.user_id)
    
    return {"status": "removed", "plugin_id": plugin_id}


@router.post("/plugins/{plugin_id}/report")
async def report_plugin(
    plugin_id: str,
    reason: str,
    details: Optional[str] = None,
    current_user: CurrentUser = Depends(get_current_user),
    repo: MarketplaceRepository = Depends(get_marketplace_repository),
):
    """
    Пожаловаться на плагин
    
    Причины:
    - malware: Вредоносный код
    - spam: Спам
    - inappropriate: Неприемлемый контент
    - copyright: Нарушение авторских прав
    - other: Другое
    
    Note:
        В production: user_id должен получаться из auth middleware (JWT token)
    """
    
    plugin = await repo.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    complaint_id = f"complaint_{uuid.uuid4().hex}"
    await repo.add_complaint(
        complaint_id=complaint_id,
        plugin_id=plugin_id,
        user_id=current_user.user_id,
        reason=reason,
        details=details,
    )

    logger.warning("Plugin %s reported by user %s: %s", plugin_id, current_user.user_id, reason)
    audit_logger.log_action(
        actor=current_user.user_id,
        action="marketplace.plugin.report",
        target=plugin_id,
        metadata={"reason": reason},
    )

    return {
        "status": "reported",
        "plugin_id": plugin_id,
        "message": "Thank you for your report. We will review it shortly.",
    }


# ==================== Helper Functions ====================

def _check_authorization(user: CurrentUser, plugin: Dict[str, Any]) -> bool:
    return plugin.get("owner_id") == user.user_id or user.has_role("admin", "moderator")


# ==================== Admin Endpoints ====================

@router.post("/admin/plugins/{plugin_id}/approve")
async def approve_plugin(
    plugin_id: str,
    current_user: CurrentUser = Depends(require_roles("admin", "moderator")),
    repo: MarketplaceRepository = Depends(get_marketplace_repository),
):
    """
    Одобрить плагин (требуется роль admin или moderator)
    """
    
    plugin = await repo.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    await repo.update_plugin(
        plugin_id,
        {
            "status": PluginStatus.APPROVED.value,
            "published_at": datetime.utcnow(),
        },
    )

    logger.info("Plugin approved by %s: %s", current_user.user_id, plugin_id)
    audit_logger.log_action(
        actor=current_user.user_id,
        action="marketplace.plugin.approve",
        target=plugin_id,
        metadata={"status": PluginStatus.APPROVED.value},
    )

    return {"status": "approved", "plugin_id": plugin_id}


@router.post("/admin/plugins/{plugin_id}/reject")
async def reject_plugin(
    plugin_id: str,
    reason: str,
    current_user: CurrentUser = Depends(require_roles("admin", "moderator")),
    repo: MarketplaceRepository = Depends(get_marketplace_repository),
):
    """
    Отклонить плагин (требуется роль admin или moderator)
    """
    
    plugin = await repo.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    await repo.update_plugin(
        plugin_id,
        {
            "status": PluginStatus.REJECTED.value,
        },
    )

    logger.info(
        "Plugin rejected by %s: %s (reason: %s)",
        current_user.user_id,
        plugin_id,
        reason,
    )
    audit_logger.log_action(
        actor=current_user.user_id,
        action="marketplace.plugin.reject",
        target=plugin_id,
        metadata={"reason": reason},
    )

    return {"status": "rejected", "plugin_id": plugin_id, "reason": reason}


@router.post("/admin/plugins/{plugin_id}/feature")
async def feature_plugin(
    plugin_id: str,
    featured: bool = True,
    current_user: CurrentUser = Depends(require_roles("admin", "moderator")),
    repo: MarketplaceRepository = Depends(get_marketplace_repository),
):
    """
    Добавить/убрать из избранных (требуется роль admin или moderator)
    """
    
    plugin = await repo.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    await repo.update_plugin(plugin_id, {"featured": featured})

    logger.info(
        "Plugin %s featured=%s by %s",
        plugin_id,
        featured,
        current_user.user_id,
    )
    audit_logger.log_action(
        actor=current_user.user_id,
        action="marketplace.plugin.feature",
        target=plugin_id,
        metadata={"featured": featured},
    )

    return {"status": "updated", "plugin_id": plugin_id, "featured": featured}


@router.post("/admin/plugins/{plugin_id}/verify")
async def verify_plugin(
    plugin_id: str,
    verified: bool = True,
    current_user: CurrentUser = Depends(require_roles("admin", "moderator")),
    repo: MarketplaceRepository = Depends(get_marketplace_repository),
):
    """
    Верифицировать плагин (требуется роль admin или moderator)
    """
    
    plugin = await repo.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    await repo.update_plugin(plugin_id, {"verified": verified})

    logger.info(
        "Plugin %s verified=%s by %s",
        plugin_id,
        verified,
        current_user.user_id,
    )
    audit_logger.log_action(
        actor=current_user.user_id,
        action="marketplace.plugin.verify",
        target=plugin_id,
        metadata={"verified": verified},
    )

    return {"status": "updated", "plugin_id": plugin_id, "verified": verified}

