"""
API маршруты Wiki.

Предоставляет базовую функциональность вики.
"""

from typing import Any, Dict

from fastapi import APIRouter

router = APIRouter(tags=["Wiki"])


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Проверка здоровья сервиса Wiki.

    Returns:
        Dict[str, Any]: Статус здоровья и информация о сервисе.
    """
    return {
        "status": "healthy",
        "service": "wiki",
        "version": "1.0.0",
    }


@router.get("/")
async def list_pages() -> Dict[str, Any]:
    """Получает список всех вики-страниц.

    Returns:
        Dict[str, Any]: Список страниц и метаданные.
    """
    return {
        "pages": [],
        "total": 0,
        "message": "Wiki service is operational",
    }
