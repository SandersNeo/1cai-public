"""
Marketplace API
REST API для marketplace плагинов
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel, Field
from enum import Enum

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/marketplace", tags=["marketplace"])


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


# ==================== In-Memory Storage (замените на PostgreSQL) ====================

# Временное хранилище (в production → PostgreSQL)
plugins_db: Dict[str, Dict[str, Any]] = {}
reviews_db: Dict[str, Dict[str, Any]] = {}


# ==================== Endpoints ====================

@router.post("/plugins", response_model=PluginResponse, status_code=201)
async def submit_plugin(plugin: PluginSubmitRequest):
    """
    Публикация нового плагина
    
    Процесс:
    1. Валидация данных
    2. Создание записи с статусом PENDING
    3. Отправка на модерацию
    4. После одобрения → APPROVED
    """
    try:
        # Генерируем ID
        plugin_id = f"plugin_{len(plugins_db) + 1}"
        
        # Создаем запись
        plugin_data = {
            "id": plugin_id,
            **plugin.model_dump(),
            "status": PluginStatus.PENDING,
            "downloads": 0,
            "rating": 0.0,
            "ratings_count": 0,
            "installs": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "published_at": None,
            "featured": False,
            "verified": False,
            "download_url": f"/marketplace/plugins/{plugin_id}/download"
        }
        
        # Сохраняем
        plugins_db[plugin_id] = plugin_data
        
        logger.info(f"Plugin submitted: {plugin_id} ({plugin.name})")
        
        return PluginResponse(**plugin_data)
        
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
    page_size: int = 20
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
        # Фильтрация
        filtered = []
        
        for plugin in plugins_db.values():
            # Только одобренные и публичные
            if plugin["status"] != PluginStatus.APPROVED:
                continue
            if plugin["visibility"] != PluginVisibility.PUBLIC:
                continue
            
            # Фильтры
            if category and plugin["category"] != category:
                continue
            
            if author and plugin["author"] != author:
                continue
            
            if query:
                search_text = f"{plugin['name']} {plugin['description']} {' '.join(plugin['keywords'])}".lower()
                if query.lower() not in search_text:
                    continue
            
            filtered.append(plugin)
        
        # Сортировка
        reverse = (order == "desc")
        
        if sort_by == "rating":
            filtered.sort(key=lambda x: x["rating"], reverse=reverse)
        elif sort_by == "downloads":
            filtered.sort(key=lambda x: x["downloads"], reverse=reverse)
        elif sort_by == "updated":
            filtered.sort(key=lambda x: x["updated_at"], reverse=reverse)
        elif sort_by == "name":
            filtered.sort(key=lambda x: x["name"], reverse=not reverse)
        
        # Пагинация
        total = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = filtered[start:end]
        
        total_pages = (total + page_size - 1) // page_size
        
        return PluginSearchResponse(
            plugins=[PluginResponse(**p) for p in paginated],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Plugin search error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/plugins/{plugin_id}", response_model=PluginResponse)
async def get_plugin(plugin_id: str):
    """Получить информацию о плагине"""
    
    if plugin_id not in plugins_db:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    plugin = plugins_db[plugin_id]
    
    return PluginResponse(**plugin)


@router.put("/plugins/{plugin_id}", response_model=PluginResponse)
async def update_plugin(plugin_id: str, update: PluginUpdateRequest):
    """
    Обновление плагина
    
    Только автор может обновлять свой плагин
    TODO: Добавить проверку авторизации
    """
    
    if plugin_id not in plugins_db:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    plugin = plugins_db[plugin_id]
    
    # Обновляем поля
    update_data = update.model_dump(exclude_unset=True)
    plugin.update(update_data)
    plugin["updated_at"] = datetime.utcnow()
    
    # Если изменилась версия - обновляем статус на PENDING
    if "version" in update_data and update_data["version"] != plugin.get("version"):
        plugin["status"] = PluginStatus.PENDING
        logger.info(f"Plugin {plugin_id} version updated, status → PENDING")
    
    plugins_db[plugin_id] = plugin
    
    logger.info(f"Plugin updated: {plugin_id}")
    
    return PluginResponse(**plugin)


@router.delete("/plugins/{plugin_id}")
async def delete_plugin(plugin_id: str):
    """
    Удаление плагина
    
    Мягкое удаление - статус → REMOVED
    TODO: Добавить проверку прав (только автор или админ)
    """
    
    if plugin_id not in plugins_db:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    # Мягкое удаление
    plugins_db[plugin_id]["status"] = PluginStatus.REMOVED
    plugins_db[plugin_id]["updated_at"] = datetime.utcnow()
    
    logger.info(f"Plugin removed: {plugin_id}")
    
    return {"status": "removed", "plugin_id": plugin_id}


@router.post("/plugins/{plugin_id}/install")
async def install_plugin(plugin_id: str, user_id: str):
    """
    Установка плагина
    
    Увеличивает счетчики downloads и installs
    """
    
    if plugin_id not in plugins_db:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    plugin = plugins_db[plugin_id]
    
    # Увеличиваем счетчики
    plugin["downloads"] += 1
    plugin["installs"] += 1
    
    logger.info(f"Plugin installed: {plugin_id} by user {user_id}")
    
    return {
        "status": "installed",
        "plugin_id": plugin_id,
        "download_url": plugin["download_url"]
    }


@router.post("/plugins/{plugin_id}/uninstall")
async def uninstall_plugin(plugin_id: str, user_id: str):
    """Удаление плагина"""
    
    if plugin_id not in plugins_db:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    plugin = plugins_db[plugin_id]
    
    # Уменьшаем счетчик активных установок
    plugin["installs"] = max(0, plugin["installs"] - 1)
    
    logger.info(f"Plugin uninstalled: {plugin_id} by user {user_id}")
    
    return {"status": "uninstalled", "plugin_id": plugin_id}


@router.get("/plugins/{plugin_id}/stats", response_model=PluginStatsResponse)
async def get_plugin_stats(plugin_id: str):
    """Получить статистику плагина"""
    
    if plugin_id not in plugins_db:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    plugin = plugins_db[plugin_id]
    
    # Получаем отзывы для этого плагина
    plugin_reviews = [r for r in reviews_db.values() if r["plugin_id"] == plugin_id]
    
    # Распределение рейтингов
    rating_dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for review in plugin_reviews:
        rating = review["rating"]
        rating_dist[rating] = rating_dist.get(rating, 0) + 1
    
    # TODO: Реальная статистика из БД
    stats = PluginStatsResponse(
        plugin_id=plugin_id,
        downloads_total=plugin["downloads"],
        downloads_last_30_days=plugin["downloads"] // 2,  # Mock
        installs_active=plugin["installs"],
        rating_average=plugin["rating"],
        rating_distribution=rating_dist,
        reviews_count=len(plugin_reviews),
        favorites_count=0,  # TODO
        downloads_trend="stable",
        rating_trend="stable"
    )
    
    return stats


@router.post("/plugins/{plugin_id}/reviews", response_model=PluginReviewResponse)
async def submit_review(plugin_id: str, review: PluginReviewRequest, user_id: str = "user_123"):
    """
    Отзыв на плагин
    
    TODO: Добавить проверку что пользователь установил плагин
    """
    
    if plugin_id not in plugins_db:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    # Генерируем ID отзыва
    review_id = f"review_{len(reviews_db) + 1}"
    
    # Создаем отзыв
    review_data = {
        "id": review_id,
        "plugin_id": plugin_id,
        "user_id": user_id,
        "user_name": f"User {user_id[-4:]}",  # Mock
        **review.model_dump(),
        "helpful_count": 0,
        "created_at": datetime.utcnow()
    }
    
    reviews_db[review_id] = review_data
    
    # Обновляем рейтинг плагина
    _update_plugin_rating(plugin_id)
    
    logger.info(f"Review submitted: {review_id} for plugin {plugin_id}")
    
    return PluginReviewResponse(**review_data)


@router.get("/plugins/{plugin_id}/reviews")
async def get_plugin_reviews(
    plugin_id: str,
    page: int = 1,
    page_size: int = 10
) -> Dict[str, Any]:
    """Получить отзывы о плагине"""
    
    if plugin_id not in plugins_db:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    # Фильтруем отзывы
    plugin_reviews = [r for r in reviews_db.values() if r["plugin_id"] == plugin_id]
    
    # Сортируем по дате (новые первыми)
    plugin_reviews.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Пагинация
    total = len(plugin_reviews)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = plugin_reviews[start:end]
    
    return {
        "reviews": [PluginReviewResponse(**r) for r in paginated],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.get("/plugins/{plugin_id}/download")
async def download_plugin(plugin_id: str):
    """
    Скачать плагин
    
    TODO: Вернуть файл плагина
    Формат: ZIP архив с manifest.json + код
    """
    
    if plugin_id not in plugins_db:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    plugin = plugins_db[plugin_id]
    
    if plugin["status"] != PluginStatus.APPROVED:
        raise HTTPException(status_code=403, detail="Plugin not approved yet")
    
    # Увеличиваем счетчик скачиваний
    plugin["downloads"] += 1
    
    # TODO: Вернуть реальный файл
    # return FileResponse(path=plugin_file_path, filename=f"{plugin['name']}.zip")
    
    return {
        "message": "Download started",
        "plugin_id": plugin_id,
        "version": plugin["version"],
        "download_url": f"/files/plugins/{plugin_id}.zip"  # Mock
    }


@router.get("/categories")
async def get_categories():
    """Получить список категорий с количеством плагинов"""
    
    # Подсчет плагинов по категориям
    category_counts = {}
    
    for plugin in plugins_db.values():
        if plugin["status"] == PluginStatus.APPROVED:
            cat = plugin["category"]
            category_counts[cat] = category_counts.get(cat, 0) + 1
    
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
async def get_featured_plugins(limit: int = 6):
    """Получить избранные плагины"""
    
    # Фильтруем featured плагины
    featured = [
        p for p in plugins_db.values()
        if p["status"] == PluginStatus.APPROVED and p.get("featured", False)
    ]
    
    # Сортируем по рейтингу
    featured.sort(key=lambda x: x["rating"], reverse=True)
    
    return {
        "plugins": [PluginResponse(**p) for p in featured[:limit]]
    }


@router.get("/trending")
async def get_trending_plugins(
    period: str = "week",  # day | week | month
    limit: int = 10
):
    """
    Получить трендовые плагины
    
    Критерии:
    - Рост скачиваний за период
    - Новые плагины с хорошим рейтингом
    - Активность (обновления, отзывы)
    """
    
    # Mock: просто топ по скачиваниям
    approved = [
        p for p in plugins_db.values()
        if p["status"] == PluginStatus.APPROVED
    ]
    
    approved.sort(key=lambda x: x["downloads"], reverse=True)
    
    return {
        "plugins": [PluginResponse(**p) for p in approved[:limit]],
        "period": period
    }


@router.post("/plugins/{plugin_id}/favorite")
async def add_to_favorites(plugin_id: str, user_id: str = "user_123"):
    """Добавить в избранное"""
    
    if plugin_id not in plugins_db:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    # TODO: Сохранить в БД user_favorites
    
    logger.info(f"Plugin {plugin_id} added to favorites by user {user_id}")
    
    return {"status": "added", "plugin_id": plugin_id}


@router.delete("/plugins/{plugin_id}/favorite")
async def remove_from_favorites(plugin_id: str, user_id: str = "user_123"):
    """Удалить из избранного"""
    
    if plugin_id not in plugins_db:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    # TODO: Удалить из БД user_favorites
    
    logger.info(f"Plugin {plugin_id} removed from favorites by user {user_id}")
    
    return {"status": "removed", "plugin_id": plugin_id}


@router.post("/plugins/{plugin_id}/report")
async def report_plugin(
    plugin_id: str,
    reason: str,
    details: Optional[str] = None,
    user_id: str = "user_123"
):
    """
    Пожаловаться на плагин
    
    Причины:
    - malware: Вредоносный код
    - spam: Спам
    - inappropriate: Неприемлемый контент
    - copyright: Нарушение авторских прав
    - other: Другое
    """
    
    if plugin_id not in plugins_db:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    # TODO: Сохранить жалобу в БД
    # TODO: Отправить уведомление модераторам
    
    logger.warning(f"Plugin {plugin_id} reported by user {user_id}: {reason}")
    
    return {
        "status": "reported",
        "plugin_id": plugin_id,
        "message": "Thank you for your report. We will review it shortly."
    }


# ==================== Helper Functions ====================

def _update_plugin_rating(plugin_id: str):
    """Пересчитать рейтинг плагина на основе отзывов"""
    
    if plugin_id not in plugins_db:
        return
    
    # Получаем все отзывы
    plugin_reviews = [r for r in reviews_db.values() if r["plugin_id"] == plugin_id]
    
    if not plugin_reviews:
        return
    
    # Средний рейтинг
    total_rating = sum(r["rating"] for r in plugin_reviews)
    avg_rating = total_rating / len(plugin_reviews)
    
    # Обновляем плагин
    plugins_db[plugin_id]["rating"] = round(avg_rating, 2)
    plugins_db[plugin_id]["ratings_count"] = len(plugin_reviews)
    
    logger.info(f"Plugin {plugin_id} rating updated: {avg_rating:.2f} ({len(plugin_reviews)} reviews)")


# ==================== Admin Endpoints ====================

@router.post("/admin/plugins/{plugin_id}/approve")
async def approve_plugin(plugin_id: str, admin_id: str = "admin"):
    """
    Одобрить плагин (только админы)
    
    TODO: Добавить проверку прав админа
    """
    
    if plugin_id not in plugins_db:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    plugin = plugins_db[plugin_id]
    
    plugin["status"] = PluginStatus.APPROVED
    plugin["published_at"] = datetime.utcnow()
    plugin["updated_at"] = datetime.utcnow()
    
    logger.info(f"Plugin approved by admin {admin_id}: {plugin_id}")
    
    return {"status": "approved", "plugin_id": plugin_id}


@router.post("/admin/plugins/{plugin_id}/reject")
async def reject_plugin(
    plugin_id: str,
    reason: str,
    admin_id: str = "admin"
):
    """Отклонить плагин (только админы)"""
    
    if plugin_id not in plugins_db:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    plugin = plugins_db[plugin_id]
    
    plugin["status"] = PluginStatus.REJECTED
    plugin["updated_at"] = datetime.utcnow()
    # TODO: Отправить уведомление автору с причиной
    
    logger.info(f"Plugin rejected by admin {admin_id}: {plugin_id} (reason: {reason})")
    
    return {"status": "rejected", "plugin_id": plugin_id, "reason": reason}


@router.post("/admin/plugins/{plugin_id}/feature")
async def feature_plugin(plugin_id: str, featured: bool = True, admin_id: str = "admin"):
    """Добавить/убрать из избранных (только админы)"""
    
    if plugin_id not in plugins_db:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    plugins_db[plugin_id]["featured"] = featured
    plugins_db[plugin_id]["updated_at"] = datetime.utcnow()
    
    logger.info(f"Plugin {plugin_id} featured={featured} by admin {admin_id}")
    
    return {"status": "updated", "plugin_id": plugin_id, "featured": featured}


@router.post("/admin/plugins/{plugin_id}/verify")
async def verify_plugin(plugin_id: str, verified: bool = True, admin_id: str = "admin"):
    """Верифицировать плагин (только админы)"""
    
    if plugin_id not in plugins_db:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    plugins_db[plugin_id]["verified"] = verified
    plugins_db[plugin_id]["updated_at"] = datetime.utcnow()
    
    logger.info(f"Plugin {plugin_id} verified={verified} by admin {admin_id}")
    
    return {"status": "updated", "plugin_id": plugin_id, "verified": verified}

