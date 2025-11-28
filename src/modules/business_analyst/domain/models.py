"""
Business Analyst Domain Models

Pydantic модели для Business Analyst модуля согласно Clean Architecture.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class RequirementType(str, Enum):
    """Тип требования"""
    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"
    CONSTRAINT = "constraint"


class Priority(str, Enum):
    """Приоритет"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Impact(str, Enum):
    """Уровень влияния"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Effort(str, Enum):
    """Уровень усилий"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class UserStory(BaseModel):
    """User Story"""
    id: str = Field(..., description="ID user story")
    role: str = Field(..., description="Роль пользователя")
    goal: str = Field(..., description="Цель")
    benefit: str = Field(..., description="Выгода")
    acceptance_criteria: List[str] = Field(
        default_factory=list,
        description="Критерии приемки"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "US-001",
                "role": "Менеджер",
                "goal": "создать заказ",
                "benefit": "ускорить процесс продаж",
                "acceptance_criteria": [
                    "Форма заказа открывается за < 2 сек",
                    "Все обязательные поля валидируются"
                ]
            }
        }
    )


class Requirement(BaseModel):
    """Требование"""
    id: str = Field(..., description="ID требования")
    type: RequirementType = Field(..., description="Тип требования")
    title: str = Field(..., description="Название")
    description: str = Field(..., description="Описание")
    priority: Priority = Field(..., description="Приоритет")
    source: str = Field(..., description="Источник (раздел документа)")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Уверенность в извлечении (0-1)"
    )
    stakeholders: List[str] = Field(
        default_factory=list,
        description="Заинтересованные стороны"
    )
    acceptance_criteria: List[str] = Field(
        default_factory=list,
        description="Критерии приемки"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "FR-001",
                "type": "functional",
                "title": "Создание заказов",
                "description": "Система должна позволять создавать заказы",
                "priority": "high",
                "source": "Section 2.1, Page 3",
                "confidence": 0.92,
                "stakeholders": ["Менеджер", "Склад"],
                "acceptance_criteria": ["Форма заказа", "Валидация"]
            }
        }
    )


class RequirementExtractionResult(BaseModel):
    """Результат извлечения требований"""
    functional_requirements: List[Requirement] = Field(
        default_factory=list,
        description="Функциональные требования"
    )
    non_functional_requirements: List[Requirement] = Field(
        default_factory=list,
        description="Нефункциональные требования"
    )
    constraints: List[Requirement] = Field(
        default_factory=list,
        description="Ограничения"
    )
    stakeholders: List[str] = Field(
        default_factory=list,
        description="Заинтересованные стороны"
    )
    user_stories: List[UserStory] = Field(
        default_factory=list,
        description="User stories"
    )
    summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Сводка по требованиям"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Timestamp анализа"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "functional_requirements": [],
                "non_functional_requirements": [],
                "constraints": [],
                "stakeholders": ["Менеджер", "Склад"],
                "user_stories": [],
                "summary": {
                    "total_requirements": 15,
                    "functional": 10,
                    "non_functional": 3,
                    "constraints": 2
                },
                "timestamp": "2025-11-27T10:00:00"
            }
        }
    )


class DecisionPoint(BaseModel):
    """Точка принятия решения в процессе"""
    condition: str = Field(..., description="Условие")
    true_path: str = Field(..., description="Путь при истине")
    false_path: str = Field(..., description="Путь при лжи")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "condition": "Товар в наличии?",
                "true_path": "Отгрузка",
                "false_path": "Заказ поставщику"
            }
        }
    )


class BPMNDiagram(BaseModel):
    """BPMN диаграмма"""
    bpmn_xml: str = Field(..., description="BPMN 2.0 XML")
    diagram_svg: Optional[str] = Field(
        None,
        description="SVG представление (опционально)"
    )
    mermaid: str = Field(..., description="Mermaid diagram")
    actors: List[str] = Field(
        default_factory=list,
        description="Участники процесса"
    )
    activities: List[str] = Field(
        default_factory=list,
        description="Активности"
    )
    decision_points: List[DecisionPoint] = Field(
        default_factory=list,
        description="Точки принятия решений"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "bpmn_xml": "<?xml version='1.0'?>...",
                "diagram_svg": None,
                "mermaid": "graph TD\nA[Start]-->B[Process]",
                "actors": ["Менеджер", "Склад"],
                "activities": ["Создание заказа", "Отгрузка"],
                "decision_points": []
            }
        }
    )


class Gap(BaseModel):
    """Gap между текущим и желаемым состоянием"""
    area: str = Field(..., description="Область")
    current: str = Field(..., description="Текущее состояние")
    desired: str = Field(..., description="Желаемое состояние")
    impact: Impact = Field(..., description="Уровень влияния")
    effort: Effort = Field(..., description="Уровень усилий")
    priority: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Приоритет (0-10)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "area": "Автоматизация продаж",
                "current": "Ручной ввод заказов",
                "desired": "Автоматический импорт из CRM",
                "impact": "high",
                "effort": "medium",
                "priority": 8.5
            }
        }
    )


class RoadmapItem(BaseModel):
    """Элемент дорожной карты"""
    phase: str = Field(..., description="Фаза (Phase 1, 2, 3)")
    gaps: List[str] = Field(..., description="Gap IDs в этой фазе")
    duration: str = Field(..., description="Длительность")
    dependencies: List[str] = Field(
        default_factory=list,
        description="Зависимости от других фаз"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "phase": "Phase 1",
                "gaps": ["gap-1", "gap-2"],
                "duration": "2 months",
                "dependencies": []
            }
        }
    )


class GapAnalysisResult(BaseModel):
    """Результат gap analysis"""
    gaps: List[Gap] = Field(default_factory=list, description="Gaps")
    roadmap: List[RoadmapItem] = Field(
        default_factory=list,
        description="Дорожная карта"
    )
    estimated_timeline: str = Field(..., description="Оценка времени")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Timestamp анализа"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "gaps": [],
                "roadmap": [],
                "estimated_timeline": "6 months",
                "timestamp": "2025-11-27T10:00:00"
            }
        }
    )


class TraceabilityItem(BaseModel):
    """Элемент матрицы прослеживаемости"""
    requirement_id: str = Field(..., description="ID требования")
    test_cases: List[str] = Field(
        default_factory=list,
        description="Test case IDs"
    )
    coverage: str = Field(..., description="Покрытие (например, '100%')")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "requirement_id": "FR-001",
                "test_cases": ["TC-001", "TC-002", "TC-003"],
                "coverage": "100%"
            }
        }
    )


class CoverageSummary(BaseModel):
    """Сводка по покрытию"""
    total_requirements: int = Field(..., description="Всего требований")
    covered: int = Field(..., description="Покрыто тестами")
    coverage_percent: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Процент покрытия"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_requirements": 50,
                "covered": 48,
                "coverage_percent": 96.0
            }
        }
    )


class TraceabilityMatrix(BaseModel):
    """Матрица прослеживаемости"""
    matrix: List[TraceabilityItem] = Field(
        default_factory=list,
        description="Матрица"
    )
    coverage_summary: CoverageSummary = Field(
        ...,
        description="Сводка по покрытию"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Timestamp анализа"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "matrix": [],
                "coverage_summary": {
                    "total_requirements": 50,
                    "covered": 48,
                    "coverage_percent": 96.0
                },
                "timestamp": "2025-11-27T10:00:00"
            }
        }
    )


__all__ = [
    "RequirementType",
    "Priority",
    "Impact",
    "Effort",
    "UserStory",
    "Requirement",
    "RequirementExtractionResult",
    "DecisionPoint",
    "BPMNDiagram",
    "Gap",
    "RoadmapItem",
    "GapAnalysisResult",
    "TraceabilityItem",
    "CoverageSummary",
    "TraceabilityMatrix",
]
