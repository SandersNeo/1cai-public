# [NEXUS IDENTITY] ID: 962687204371806439 | DATE: 2025-11-19

"""
API для импорта данных в базу знаний из различных источников
Версия: 1.0.0
"""

import csv
import io
import json
from typing import Any, Dict, List

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse

from src.infrastructure.logging.structured_logging import StructuredLogger
from src.services.configuration_knowledge_base import get_knowledge_base

router = APIRouter(
    prefix="/api/knowledge-base",
    tags=["Knowledge Base Import"])

kb = get_knowledge_base()
logger = StructuredLogger(__name__).logger


# Модели данных
class ImportRequest(BaseModel):
    """Запрос на импорт данных"""

    config_name: str = Field(..., description="Название конфигурации")
    source: str = Field(default="manual", description="Источник данных")
    overwrite: bool = Field(
        default=False,
        description="Перезаписать существующие данные")


class ModuleImport(BaseModel):
    """Импорт модуля"""

    name: str
    description: str = ""
    code: str = ""
    functions: List[Dict[str, Any]] = []
    object_type: str | None = None
    object_name: str | None = None
    module_type: str | None = None


class BestPracticeImport(BaseModel):
    """Импорт best practice"""

    title: str
    description: str
    category: str = "general"
    code_examples: List[str] = []
    tags: List[str] = []


class BulkImportRequest(BaseModel):
    """Массовый импорт"""

    config_name: str
    modules: List[ModuleImport] = []
    best_practices: List[BestPracticeImport] = []
    source: str = "import"


# Эндпоинты
@router.post("/import/json")
async def import_from_json(
        config_name: str,
        file: UploadFile = File(...),
        overwrite: bool = False):
    """Импорт данных из JSON файла"""
    try:
