# [NEXUS IDENTITY] ID: -2939309114614425990 | DATE: 2025-11-19

"""
API endpoints для работы с базой знаний по конфигурациям 1С
Версия: 1.0.0
"""

from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.infrastructure.logging.structured_logging import StructuredLogger
from src.services.configuration_knowledge_base import get_knowledge_base

logger = StructuredLogger(__name__).logger
router = APIRouter()


# ==================== МОДЕЛИ ДАННЫХ ====================


class ConfigurationRequest(BaseModel):
    """Запрос информации о конфигурации"""

    configName: Literal["erp", "ut", "zup", "buh", "holding", "buhbit", "do", "ka"] = Field(
        ..., description="Название конфигурации"
    )


class ModuleDocumentationRequest(BaseModel):
    """Запрос на добавление документации модуля"""

    configName: str
    moduleName: str
    documentation: dict


class BestPracticeRequest(BaseModel):
    """Запрос на добавление best practice"""

    configName: str
    category: str
    practice: dict


class PatternSearchRequest(BaseModel):
    """Запрос на поиск паттернов"""

    configName: Optional[str] = None
    patternType: Optional[str] = None
    query: Optional[str] = None


class CodeRecommendationRequest(BaseModel):
    """Запрос рекомендаций на основе кода"""

    code: str = Field(..., description="Код для анализа",
                      max_length=100000)  # Limit length
    configName: Optional[str] = Field(
    None,
    description="Название конфигурации (опционально)",
     max_length=50)


# ==================== API ENDPOINTS ====================


@router.get(
    "/configurations",
    tags=["Knowledge Base"],
    summary="Список поддерживаемых конфигураций",
    description="Получение списка всех поддерживаемых типовых конфигураций 1С",
)
async def get_configurations():
    """Список конфигураций"""
    kb = get_knowledge_base()

    configurations = []
    for config_key in kb.SUPPORTED_CONFIGURATIONS:
        info = kb.get_configuration_info(config_key)
        if info:
            configurations.append(
                {
                    "id": config_key,
                    "name": info.get("name", config_key),
                    "modules_count": len(info.get("modules", [])),
                    "best_practices_count": len(info.get("best_practices", [])),
                    "patterns_count": len(info.get("common_patterns", [])),
                }
            )

    return {"configurations": configurations, "total": len(configurations)}


@router.get(
    "/configurations/{config_name}",
    tags=["Knowledge Base"],
    summary="Информация о конфигурации",
    description="Получение подробной информации о конкретной конфигурации",
)
async def get_configuration_info(config_name: str):
    """
    Информация о конфигурации с валидацией входных данных

    Best practices:
    - Sanitization имени конфигурации
    - Защита от path traversal
    """
    # Input validation and sanitization (best practice)
    sanitized_name = config_name.strip().lower()[
    :50]  # Limit length and normalize
    if not sanitized_name:
        raise HTTPException(status_code=400,
     detail="Configuration name cannot be empty")

    # Prevent path traversal and dangerous characters
    if ".." in sanitized_name or "/" in sanitized_name or "\\" in sanitized_name:
        raise HTTPException(
    status_code=400,
     detail="Invalid configuration name")

    kb = get_knowledge_base()
    info = kb.get_configuration_info(sanitized_name)

    if not info:
        raise HTTPException(
    status_code=404,
     detail=f"Конфигурация {sanitized_name} не найдена")

    return info


@router.post(
    "/recommendations",
    tags=["Knowledge Base"],
    summary="Рекомендации на основе кода",
    description="Получение рекомендаций на основе анализа кода и базы знаний",
)
async def get_recommendations(request: CodeRecommendationRequest):
    """
    Рекомендации на основе кода с валидацией входных данных

    Best practices:
    - Валидация длины кода
    - Sanitization имени конфигурации
    - Улучшенная обработка ошибок
    """
    try:
            "Unexpected error getting recommendations",
            extra = {
                "error": str(e),
                "error_type": type(e).__name__,
                "code_length": len(request.code) if hasattr(request, "code") else 0,
                "config_name": (request.configName if hasattr(request, "configName") else None),
            },
            exc_info = True,
        )
        raise HTTPException(status_code=500, detail="An error occurred while getting recommendations")


@router.post(
    "/patterns/search",
    tags=["Knowledge Base"],
    summary="Поиск паттернов",
    description="Поиск паттернов в базе знаний",
)
async def search_patterns(request: PatternSearchRequest):
    """
    Поиск паттернов с валидацией входных данных

    Best practices:
    - Sanitization входных данных
    - Защита от path traversal
    - Улучшенная обработка ошибок
    """
    try:
            "Unexpected error searching patterns",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "config_name": (request.configName if hasattr(request, "configName") else None),
                "pattern_type": (request.patternType if hasattr(request, "patternType") else None),
            },
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="An error occurred while searching patterns")


@router.post(
    "/modules",
    tags=["Knowledge Base"],
    summary="Добавление документации модуля",
    description="Добавление документации модуля в базу знаний",
)
async def add_module_documentation(request: ModuleDocumentationRequest):
    """
    Добавление документации модуля с валидацией входных данных

    Best practices:
    - Sanitization имен конфигурации и модуля
    - Защита от path traversal
    - Улучшенная обработка ошибок
    """
    try:
            "Unexpected error adding module documentation",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "config_name": (request.configName if hasattr(request, "configName") else None),
                "module_name": (request.moduleName if hasattr(request, "moduleName") else None),
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="An error occurred while adding module documentation",
        )


@router.post(
    "/best-practices",
    tags=["Knowledge Base"],
    summary="Добавление best practice",
    description="Добавление best practice в базу знаний",
)
async def add_best_practice(request: BestPracticeRequest):
    """Добавление best practice"""
    try:
            "Ошибка добавления best practice",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "config_name": (request.configName if hasattr(request, "configName") else None),
            },
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Ошибка добавления best practice")


@router.post(
    "/load-from-directory",
    tags=["Knowledge Base"],
    summary="Загрузка конфигураций из директории",
    description="Загрузка конфигураций 1С из указанной директории",
)
async def load_from_directory(directory_path: str):
    """Загрузка конфигураций из директории"""
    try: