"""
Technical Writer Domain Models

Pydantic модели для Technical Writer модуля согласно Clean Architecture.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field


class HTTPMethod(str, Enum):
    """HTTP методы"""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class Audience(str, Enum):
    """Целевая аудитория"""

    END_USER = "end_user"
    DEVELOPER = "developer"
    ADMIN = "admin"


class DocumentationType(str, Enum):
    """Тип документации"""

    API = "api"
    USER_GUIDE = "user_guide"
    RELEASE_NOTES = "release_notes"
    CODE = "code"


class APIParameter(BaseModel):
    """Параметр API"""

    name: str = Field(..., description="Название параметра")
    type: str = Field(..., description="Тип параметра")
    required: bool = Field(..., description="Обязательный параметр")
    description: str = Field(..., description="Описание параметра")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "user_id",
                "type": "integer",
                "required": True,
                "description": "User ID",
            }
        }
    )


class APIEndpoint(BaseModel):
    """API endpoint"""

    method: HTTPMethod = Field(..., description="HTTP метод")
    path: str = Field(..., description="Путь endpoint")
    function_name: str = Field(..., description="Название функции")
    parameters: List[APIParameter] = Field(
        default_factory=list, description="Параметры"
    )
    description: str = Field(..., description="Описание endpoint")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "method": "GET",
                "path": "/api/users",
                "function_name": "GetUsers",
                "parameters": [],
                "description": "Get all users",
            }
        }
    )


class APIExample(BaseModel):
    """Пример использования API"""

    endpoint: str = Field(..., description="Endpoint")
    curl: str = Field(..., description="cURL команда")
    request: Dict[str, Any] = Field(..., description="Request данные")
    response: Dict[str, Any] = Field(..., description="Response данные")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "endpoint": "GET /api/users",
                "curl": "curl -X GET 'https://api.example.com/users'",
                "request": {"method": "GET", "url": "/api/users"},
                "response": {"status": 200, "body": {}},
            }
        }
    )


class APIDocumentation(BaseModel):
    """API документация"""

    openapi_spec: Dict[str, Any] = Field(..., description="OpenAPI спецификация")
    markdown_docs: str = Field(..., description="Markdown документация")
    examples: List[APIExample] = Field(
        default_factory=list, description="Примеры использования"
    )
    postman_collection: Dict[str, Any] = Field(
        default_factory=dict, description="Postman коллекция"
    )
    endpoints_count: int = Field(..., ge=0, description="Количество endpoints")
    generated_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Timestamp генерации",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "openapi_spec": {},
                "markdown_docs": "# API Documentation",
                "examples": [],
                "postman_collection": {},
                "endpoints_count": 5,
                "generated_at": "2025-11-27T10:00:00",
            }
        }
    )


class GuideSection(BaseModel):
    """Раздел руководства"""

    title: str = Field(..., description="Заголовок раздела")
    content: str = Field(..., description="Содержимое раздела")
    order: int = Field(..., ge=1, description="Порядок раздела")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Getting Started",
                "content": "To get started...",
                "order": 1,
            }
        }
    )


class FAQItem(BaseModel):
    """Элемент FAQ"""

    question: str = Field(..., description="Вопрос")
    answer: str = Field(..., description="Ответ")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"question": "How to install?", "answer": "Run pip install..."}
        }
    )


class UserGuide(BaseModel):
    """Руководство пользователя"""

    feature: str = Field(..., description="Название функции")
    target_audience: Audience = Field(..., description="Целевая аудитория")
    sections: List[GuideSection] = Field(
        default_factory=list, description="Разделы руководства"
    )
    faq: List[FAQItem] = Field(default_factory=list, description="FAQ")
    guide_markdown: str = Field(..., description="Markdown руководства")
    generated_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Timestamp генерации",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "feature": "User Management",
                "target_audience": "end_user",
                "sections": [],
                "faq": [],
                "guide_markdown": "# User Guide",
                "generated_at": "2025-11-27T10:00:00",
            }
        }
    )


class ReleaseNotes(BaseModel):
    """Release notes"""

    version: str = Field(..., description="Версия релиза")
    release_date: str = Field(..., description="Дата релиза")
    features: List[str] = Field(default_factory=list, description="Новые функции")
    fixes: List[str] = Field(default_factory=list, description="Исправления")
    breaking_changes: List[str] = Field(
        default_factory=list, description="Breaking changes"
    )
    markdown: str = Field(..., description="Markdown release notes")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "version": "v1.2.0",
                "release_date": "2025-11-27",
                "features": ["New feature 1", "New feature 2"],
                "fixes": ["Bug fix 1"],
                "breaking_changes": [],
                "markdown": "# Release Notes v1.2.0",
            }
        }
    )


class Parameter(BaseModel):
    """Параметр функции"""

    name: str = Field(..., description="Название параметра")
    type: str = Field(..., description="Тип параметра")
    description: str = Field(..., description="Описание параметра")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "UserID",
                "type": "Число",
                "description": "ID пользователя",
            }
        }
    )


class FunctionDocumentation(BaseModel):
    """Документация функции"""

    function_name: str = Field(..., description="Название функции")
    parameters: List[Parameter] = Field(
        default_factory=list, description="Параметры функции"
    )
    return_type: str = Field(..., description="Тип возвращаемого значения")
    description: str = Field(..., description="Описание функции")
    examples: List[str] = Field(
        default_factory=list, description="Примеры использования"
    )
    documented_code: str = Field(..., description="Документированный код")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "function_name": "GetUserByID",
                "parameters": [],
                "return_type": "Структура",
                "description": "Получение пользователя по ID",
                "examples": ["Result = GetUserByID(123);"],
                "documented_code": "// Documented code...",
            }
        }
    )


__all__ = [
    "HTTPMethod",
    "Audience",
    "DocumentationType",
    "APIParameter",
    "APIEndpoint",
    "APIExample",
    "APIDocumentation",
    "GuideSection",
    "FAQItem",
    "UserGuide",
    "ReleaseNotes",
    "Parameter",
    "FunctionDocumentation",
]
