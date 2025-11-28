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

router = APIRouter(prefix="/api/knowledge-base", tags=["Knowledge Base Import"])

kb = get_knowledge_base()
logger = StructuredLogger(__name__).logger


# Модели данных
class ImportRequest(BaseModel):
    """Запрос на импорт данных"""

    config_name: str = Field(..., description="Название конфигурации")
    source: str = Field(default="manual", description="Источник данных")
    overwrite: bool = Field(
        default=False, description="Перезаписать существующие данные")


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
async def import_from_json(config_name: str, file: UploadFile = File(...), overwrite: bool = False):
    """Импорт данных из JSON файла"""
    try:
        content = await file.read()
        data = json.loads(content)

        modules_count = 0
        practices_count = 0

        if "modules" in data:
            for module in data["modules"]:
                kb.add_module_documentation(
                    config_name=config_name, module_name=module.get("name", ""), documentation=module
                )
                modules_count += 1

        if "best_practices" in data:
            for practice in data["best_practices"]:
                kb.add_best_practice(
                    config_name=config_name, category=practice.get("category", "general"), practice=practice
                )
                practices_count += 1

        return {"success": True, "modules_imported": modules_count, "best_practices_imported": practices_count}
    except Exception as e:
        logger.error(f"Error importing from JSON: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/csv")
async def import_from_csv(config_name: str, file: UploadFile = File(...), type: str = "modules"):
    """Импорт данных из CSV файла"""
    try:
        content = await file.read()
        decoded = content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(decoded))

        count = 0
        for row in reader:
            if type == "modules":
                kb.add_module_documentation(
                    config_name=config_name, module_name=row.get("name", ""), documentation=row)
            elif type == "best_practices":
                kb.add_best_practice(config_name=config_name, category=row.get(
                    "category", "general"), practice=row)
            count += 1

        return {"success": True, "imported": count}
    except Exception as e:
        logger.error(f"Error importing from CSV: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/bulk")
async def bulk_import(request: BulkImportRequest):
    """Массовый импорт модулей и best practices"""
    try:
        modules_count = 0
        for module in request.modules:
            kb.add_module_documentation(
                config_name=request.config_name, module_name=module.name, documentation=module.model_dump()
            )
            modules_count += 1

        practices_count = 0
        for practice in request.best_practices:
            kb.add_best_practice(
                config_name=request.config_name, category=practice.category, practice=practice.model_dump()
            )
            practices_count += 1

        return {"success": True, "modules_imported": modules_count, "best_practices_imported": practices_count}
    except Exception as e:
        logger.error(f"Error in bulk import: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/json")
async def download_json_template():
    """Скачать шаблон JSON для импорта"""
    template = {
        "modules": [
            {"name": "ОбщийМодуль_Пример", "description": "Описание модуля",
                "code": "// Код модуля", "functions": []}
        ],
        "best_practices": [
            {
                "title": "Название практики",
                "description": "Описание",
                "category": "performance",
                "code_examples": [],
                "tags": [],
            }
        ],
    }

    json_str = json.dumps(template, ensure_ascii=False, indent=2)
    return StreamingResponse(
        io.BytesIO(json_str.encode("utf-8")),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=template.json"},
    )


@router.get("/templates/csv")
async def download_csv_template(type: str = "modules"):
    """Скачать шаблон CSV для импорта"""
    if type == "modules":
        csv_content = "name,description,code,object_type,object_name\n"
        csv_content += "ОбщийМодуль_Пример,Описание,// Код,CommonModule,Пример\n"
    else:
        csv_content = "title,description,category\n"
        csv_content += "Название практики,Описание,performance\n"

    return StreamingResponse(
        io.BytesIO(csv_content.encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=template_{type}.csv"},
    )
