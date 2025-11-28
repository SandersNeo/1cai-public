"""
QA Engineer Domain Models

Pydantic модели для QA Engineer модуля согласно Clean Architecture.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class TestType(str, Enum):
    """Тип теста"""
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    PERFORMANCE = "performance"


class TestFramework(str, Enum):
    """Фреймворк тестирования"""
    YAXUNIT = "yaxunit"
    VANESSA = "vanessa"
    UNITTEST = "unittest"


class CoverageGrade(str, Enum):
    """Оценка покрытия"""
    A = "A"  # 90-100%
    B = "B"  # 80-89%
    C = "C"  # 70-79%
    D = "D"  # 60-69%
    F = "F"  # <60%


class TestParameter(BaseModel):
    """Параметр теста"""
    name: str = Field(..., description="Название параметра")
    type: str = Field(..., description="Тип параметра")
    default_value: Optional[str] = Field(
        None,
        description="Значение по умолчанию"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "СуммаДокумента",
                "type": "Число",
                "default_value": "1000"
            }
        }
    )


class TestCase(BaseModel):
    """Тест-кейс"""
    name: str = Field(..., description="Название теста")
    type: TestType = Field(..., description="Тип теста")
    code: str = Field(..., description="Код теста")
    description: str = Field(..., description="Описание теста")
    expected_result: str = Field(..., description="Ожидаемый результат")
    parameters: List[TestParameter] = Field(
        default_factory=list,
        description="Параметры теста"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Тест_СозданиеДокумента_ПоложительныйСценарий",
                "type": "unit",
                "code": "Процедура Тест_СозданиеДокумента()...",
                "description": "Проверка создания документа с корректными данными",
                "expected_result": "Документ создан успешно",
                "parameters": []
            }
        }
    )


class TestGenerationResult(BaseModel):
    """Результат генерации тестов"""
    positive_tests: List[TestCase] = Field(
        default_factory=list,
        description="Позитивные тесты"
    )
    negative_tests: List[TestCase] = Field(
        default_factory=list,
        description="Негативные тесты"
    )
    edge_case_tests: List[TestCase] = Field(
        default_factory=list,
        description="Граничные случаи"
    )
    coverage_estimate: str = Field(
        ...,
        description="Оценка покрытия (например, '85%')"
    )
    complexity: int = Field(
        ...,
        ge=1,
        le=10,
        description="Цикломатическая сложность (1-10)"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Timestamp генерации"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "positive_tests": [],
                "negative_tests": [],
                "edge_case_tests": [],
                "coverage_estimate": "85%",
                "complexity": 3,
                "timestamp": "2025-11-27T10:00:00"
            }
        }
    )


class CoverageReport(BaseModel):
    """Отчет о покрытии тестами"""
    total_coverage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Общее покрытие (%)"
    )
    line_coverage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Покрытие строк (%)"
    )
    branch_coverage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Покрытие ветвлений (%)"
    )
    function_coverage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Покрытие функций (%)"
    )
    grade: CoverageGrade = Field(..., description="Оценка покрытия")
    recommendations: List[str] = Field(
        default_factory=list,
        description="Рекомендации по улучшению"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Timestamp анализа"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_coverage": 85.5,
                "line_coverage": 87.0,
                "branch_coverage": 82.0,
                "function_coverage": 90.0,
                "grade": "B",
                "recommendations": [
                    "Добавить тесты для модуля Документы",
                    "Увеличить покрытие ветвлений"
                ],
                "timestamp": "2025-11-27T10:00:00"
            }
        }
    )


class TestTemplate(BaseModel):
    """Шаблон теста"""
    name: str = Field(..., description="Название шаблона")
    framework: TestFramework = Field(..., description="Фреймворк")
    template_code: str = Field(..., description="Код шаблона")
    parameters: List[str] = Field(
        default_factory=list,
        description="Параметры шаблона"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "YAxUnit_BasicTest",
                "framework": "yaxunit",
                "template_code": "Процедура {test_name}()...",
                "parameters": ["test_name", "module_name"]
            }
        }
    )


__all__ = [
    "TestType",
    "TestFramework",
    "CoverageGrade",
    "TestParameter",
    "TestCase",
    "TestGenerationResult",
    "CoverageReport",
    "TestTemplate",
]
