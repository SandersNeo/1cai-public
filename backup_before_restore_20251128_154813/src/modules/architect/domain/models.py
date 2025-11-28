"""
Architect Domain Models

Pydantic модели для Architect модуля согласно Clean Architecture.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field


class AntiPatternType(str, Enum):
    """Тип anti-pattern"""

    GOD_OBJECT = "god_object"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    TIGHT_COUPLING = "tight_coupling"
    LOW_COHESION = "low_cohesion"
    ORPHAN_MODULE = "orphan_module"


class Severity(str, Enum):
    """Серьезность проблемы"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Effort(str, Enum):
    """Усилия на рефакторинг"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class HealthStatus(str, Enum):
    """Статус здоровья архитектуры"""

    EXCELLENT = "excellent"  # 9-10
    GOOD = "good"  # 7-8
    ACCEPTABLE = "acceptable"  # 5-6
    POOR = "poor"  # 3-4
    CRITICAL = "critical"  # 1-2


class ADRStatus(str, Enum):
    """Статус Architecture Decision Record"""

    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"


class ArchitectureMetrics(BaseModel):
    """Метрики архитектуры"""

    modules_count: int = Field(..., ge=0, description="Количество модулей")
    coupling_score: float = Field(
        ..., ge=0.0, le=1.0, description="Coupling score (0-1, lower is better)"
    )
    cohesion_score: float = Field(
        ..., ge=0.0, le=1.0, description="Cohesion score (0-1, higher is better)"
    )
    cyclic_dependencies_count: int = Field(
        ..., ge=0, description="Количество циклических зависимостей"
    )
    god_objects_count: int = Field(..., ge=0, description="Количество God Objects")
    orphan_modules_count: int = Field(
        ..., ge=0, description="Количество изолированных модулей"
    )
    overall_score: float = Field(
        ..., ge=1.0, le=10.0, description="Общая оценка архитектуры (1-10)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "modules_count": 45,
                "coupling_score": 0.35,
                "cohesion_score": 0.72,
                "cyclic_dependencies_count": 2,
                "god_objects_count": 1,
                "orphan_modules_count": 3,
                "overall_score": 7.5,
            }
        }
    )


class AntiPattern(BaseModel):
    """Anti-pattern в архитектуре"""

    type: AntiPatternType = Field(..., description="Тип anti-pattern")
    severity: Severity = Field(..., description="Серьезность")
    location: str = Field(..., description="Местоположение (модуль/файл)")
    metrics: Dict[str, Any] = Field(
        default_factory=dict, description="Метрики проблемы"
    )
    recommendation: str = Field(..., description="Рекомендация по исправлению")
    refactoring_effort: Effort = Field(..., description="Усилия на рефакторинг")
    estimated_days: int = Field(..., ge=1, description="Оценка времени (дни)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "god_object",
                "severity": "high",
                "location": "ПродажиСервер",
                "metrics": {"functions_count": 75, "dependencies": 25},
                "recommendation": "Разделить на несколько модулей",
                "refactoring_effort": "high",
                "estimated_days": 10,
            }
        }
    )


class ArchitectureAnalysisResult(BaseModel):
    """Результат анализа архитектуры"""

    metrics: ArchitectureMetrics = Field(..., description="Метрики")
    anti_patterns: List[AntiPattern] = Field(
        default_factory=list, description="Обнаруженные anti-patterns"
    )
    recommendations: List[str] = Field(
        default_factory=list, description="Рекомендации по улучшению"
    )
    health_status: HealthStatus = Field(..., description="Статус здоровья")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Timestamp анализа",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "metrics": {},
                "anti_patterns": [],
                "recommendations": [
                    "Уменьшить coupling между модулями",
                    "Рефакторить God Objects",
                ],
                "health_status": "good",
                "timestamp": "2025-11-27T10:00:00",
            }
        }
    )


class Alternative(BaseModel):
    """Альтернатива в ADR"""

    name: str = Field(..., description="Название альтернативы")
    pros: List[str] = Field(default_factory=list, description="Преимущества")
    cons: List[str] = Field(default_factory=list, description="Недостатки")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Микросервисная архитектура",
                "pros": ["Масштабируемость", "Независимое развертывание"],
                "cons": ["Сложность", "Overhead"],
            }
        }
    )


class Consequences(BaseModel):
    """Последствия решения в ADR"""

    positive: List[str] = Field(
        default_factory=list, description="Позитивные последствия"
    )
    negative: List[str] = Field(
        default_factory=list, description="Негативные последствия"
    )
    risks: List[str] = Field(default_factory=list, description="Риски")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "positive": ["Улучшенная масштабируемость"],
                "negative": ["Увеличенная сложность"],
                "risks": ["Проблемы с производительностью"],
            }
        }
    )


class ADR(BaseModel):
    """Architecture Decision Record"""

    id: str = Field(..., description="ID решения (ADR-001)")
    title: str = Field(..., description="Название решения")
    status: ADRStatus = Field(..., description="Статус")
    context: str = Field(..., description="Контекст принятия решения")
    problem: str = Field(..., description="Проблема/вызов")
    decision: str = Field(..., description="Принятое решение")
    alternatives: List[Alternative] = Field(
        default_factory=list, description="Рассмотренные альтернативы"
    )
    consequences: Consequences = Field(..., description="Последствия")
    created_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(), description="Дата создания"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "ADR-001",
                "title": "Переход на микросервисную архитектуру",
                "status": "accepted",
                "context": "Монолитная архитектура не масштабируется",
                "problem": "Невозможность независимого развертывания",
                "decision": "Разделить на микросервисы",
                "alternatives": [],
                "consequences": {},
                "created_at": "2025-11-27T10:00:00",
            }
        }
    )


__all__ = [
    "AntiPatternType",
    "Severity",
    "Effort",
    "HealthStatus",
    "ADRStatus",
    "ArchitectureMetrics",
    "AntiPattern",
    "ArchitectureAnalysisResult",
    "Alternative",
    "Consequences",
    "ADR",
]
