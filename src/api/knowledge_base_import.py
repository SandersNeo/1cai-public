"""
API для импорта данных в базу знаний из различных источников
Версия: 1.0.0
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import json
import csv
import io
from pathlib import Path

from src.services.configuration_knowledge_base import get_knowledge_base
from src.utils.structured_logging import StructuredLogger

router = APIRouter(prefix="/api/knowledge-base", tags=["Knowledge Base Import"])

kb = get_knowledge_base()
logger = StructuredLogger(__name__).logger


class ImportRequest(BaseModel):
    """Запрос на импорт данных"""
    config_name: str = Field(..., description="Название конфигурации")
    source: str = Field(default="manual", description="Источник данных")
    overwrite: bool = Field(default=False, description="Перезаписать существующие данные")


class ModuleImport(BaseModel):
    """Импорт модуля"""
    name: str
    description: str = ""
    code: str = ""
    functions: List[Dict[str, Any]] = []
    object_type: Optional[str] = None
    object_name: Optional[str] = None
    module_type: Optional[str] = None


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


@router.post("/import/json", summary="Импорт из JSON")
async def import_from_json(
    config_name: str,
    file: UploadFile = File(...),
    overwrite: bool = False
):
    """
    Импорт данных из JSON файла
    
    Формат JSON:
    {
        "modules": [
            {
                "name": "ОбщийМодуль_РаботаСКлиентами",
                "description": "...",
                "code": "...",
                "functions": [...]
            }
        ],
        "best_practices": [
            {
                "title": "...",
                "description": "...",
                "category": "performance"
            }
        ]
    }
    """
    try:
        # Читаем файл
        content = await file.read()
        data = json.loads(content.decode('utf-8'))
        
        imported_modules = 0
        imported_practices = 0
        
        # Импортируем модули
        for module_data in data.get("modules", []):
            try:
                kb.add_module_documentation(
                    config_name=config_name.lower(),
                    module_name=module_data.get("name", "Unknown"),
                    documentation={
                        "description": module_data.get("description", ""),
                        "code": module_data.get("code", ""),
                        "functions": module_data.get("functions", []),
                        "object_type": module_data.get("object_type"),
                        "object_name": module_data.get("object_name"),
                        "module_type": module_data.get("module_type"),
                        "source": data.get("source", "json_import")
                    }
                )
                imported_modules += 1
            except Exception as e:
                logger.error(
                    "Ошибка импорта модуля",
                    extra={
                        "error": str(e),
                        "error_type": type(e).__name__
                    },
                    exc_info=True
                )
        
        # Импортируем best practices
        for practice_data in data.get("best_practices", []):
            try:
                kb.add_best_practice(
                    config_name=config_name.lower(),
                    category=practice_data.get("category", "general"),
                    practice={
                        "title": practice_data.get("title", ""),
                        "description": practice_data.get("description", ""),
                        "code_examples": practice_data.get("code_examples", []),
                        "tags": practice_data.get("tags", []),
                        "source": data.get("source", "json_import")
                    }
                )
                imported_practices += 1
            except Exception as e:
                logger.error(
                    "Ошибка импорта practice",
                    extra={
                        "error": str(e),
                        "error_type": type(e).__name__
                    },
                    exc_info=True
                )
        
        return {
            "status": "success",
            "imported": {
                "modules": imported_modules,
                "best_practices": imported_practices
            },
            "config_name": config_name
        }
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Ошибка парсинга JSON: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка импорта: {e}")


@router.post("/import/csv", summary="Импорт из CSV")
async def import_from_csv(
    config_name: str,
    file: UploadFile = File(...),
    type: str = "modules"  # modules или best_practices
):
    """
    Импорт данных из CSV файла
    
    Для модулей колонки: name, description, code, object_type, object_name
    Для best_practices колонки: title, description, category
    """
    try:
        # Читаем файл
        content = await file.read()
        csv_content = content.decode('utf-8-sig')  # Поддержка BOM
        
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)
        
        imported = 0
        
        if type == "modules":
            for row in rows:
                try:
                    kb.add_module_documentation(
                        config_name=config_name.lower(),
                        module_name=row.get("name", "Unknown"),
                        documentation={
                            "description": row.get("description", ""),
                            "code": row.get("code", ""),
                            "object_type": row.get("object_type"),
                            "object_name": row.get("object_name"),
                            "module_type": row.get("module_type"),
                            "source": "csv_import"
                        }
                    )
                    imported += 1
                except Exception as e:
                    logger.error(
                        "Ошибка импорта модуля",
                        extra={
                            "error": str(e),
                            "error_type": type(e).__name__
                        },
                        exc_info=True
                    )
        
        elif type == "best_practices":
            for row in rows:
                try:
                    kb.add_best_practice(
                        config_name=config_name.lower(),
                        category=row.get("category", "general"),
                        practice={
                            "title": row.get("title", ""),
                            "description": row.get("description", ""),
                            "code_examples": [row.get("code_example", "")] if row.get("code_example") else [],
                            "tags": row.get("tags", "").split(",") if row.get("tags") else [],
                            "source": "csv_import"
                        }
                    )
                    imported += 1
                except Exception as e:
                    logger.error(
                        "Ошибка импорта practice",
                        extra={
                            "error": str(e),
                            "error_type": type(e).__name__
                        },
                        exc_info=True
                    )
        
        return {
            "status": "success",
            "imported": imported,
            "type": type,
            "config_name": config_name
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка импорта CSV: {e}")


@router.post("/import/bulk", summary="Массовый импорт")
async def bulk_import(request: BulkImportRequest):
    """
    Массовый импорт модулей и best practices
    
    Удобно для программного наполнения базы знаний
    """
    try:
        imported_modules = 0
        imported_practices = 0
        
        # Импортируем модули
        for module in request.modules:
            try:
                kb.add_module_documentation(
                    config_name=request.config_name.lower(),
                    module_name=module.name,
                    documentation={
                        "description": module.description,
                        "code": module.code,
                        "functions": module.functions,
                        "object_type": module.object_type,
                        "object_name": module.object_name,
                        "module_type": module.module_type,
                        "source": request.source
                    }
                )
                imported_modules += 1
            except Exception as e:
                logger.error(
                    "Ошибка импорта модуля",
                    extra={
                        "module_name": module.name,
                        "error": str(e),
                        "error_type": type(e).__name__
                    },
                    exc_info=True
                )
        
        # Импортируем best practices
        for practice in request.best_practices:
            try:
                kb.add_best_practice(
                    config_name=request.config_name.lower(),
                    category=practice.category,
                    practice={
                        "title": practice.title,
                        "description": practice.description,
                        "code_examples": practice.code_examples,
                        "tags": practice.tags,
                        "source": request.source
                    }
                )
                imported_practices += 1
            except Exception as e:
                logger.error(
                    "Ошибка импорта practice",
                    extra={
                        "practice_title": practice.title,
                        "error": str(e),
                        "error_type": type(e).__name__
                    },
                    exc_info=True
                )
        
        return {
            "status": "success",
            "imported": {
                "modules": imported_modules,
                "best_practices": imported_practices
            },
            "config_name": request.config_name
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка массового импорта: {e}")


@router.get("/export/template/json", summary="Скачать шаблон JSON")
async def download_json_template():
    """Скачать шаблон JSON для импорта"""
    template = {
        "source": "manual_import",
        "modules": [
            {
                "name": "ОбщийМодуль_РаботаСКлиентами",
                "description": "Модуль для работы с клиентами",
                "code": "// Пример кода\nФункция ПолучитьКлиента(ИмяКлиента)\n\tВозврат Неопределено;\nКонецФункции",
                "functions": [
                    {
                        "name": "ПолучитьКлиента",
                        "type": "Функция",
                        "params": ["ИмяКлиента"],
                        "description": "Получает клиента по имени"
                    }
                ],
                "object_type": "CommonModule",
                "object_name": "РаботаСКлиентами",
                "module_type": "Module"
            }
        ],
        "best_practices": [
            {
                "title": "Оптимизация запросов",
                "description": "Используйте индексы и ограничивайте количество записей",
                "category": "performance",
                "code_examples": [
                    "Запрос.УстановитьПараметр(\"Лимит\", 100);"
                ],
                "tags": ["performance", "query", "optimization"]
            }
        ]
    }
    
    return template


@router.get("/export/template/csv", summary="Скачать шаблон CSV")
async def download_csv_template(type: str = "modules"):
    """Скачать шаблон CSV для импорта"""
    if type == "modules":
        # Возвращаем пример CSV для модулей
        template = "name,description,code,object_type,object_name,module_type\n"
        template += "ОбщийМодуль_РаботаСКлиентами,Модуль для работы с клиентами,\"// Пример кода\",CommonModule,РаботаСКлиентами,Module\n"
    else:
        # Шаблон для best practices
        template = "title,description,category,code_example,tags\n"
        template += "Оптимизация запросов,Используйте индексы,performance,\"Запрос.УстановитьПараметр(\\\"Лимит\\\", 100)\",\"performance,query\"\n"
    
    return {"template": template, "type": type}







