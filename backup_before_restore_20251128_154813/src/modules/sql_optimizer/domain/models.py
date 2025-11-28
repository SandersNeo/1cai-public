"""
SQL Optimizer Domain Models

Pydantic модели для SQL Optimizer модуля.
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class QueryComplexity(str, Enum):
    """Сложность запроса"""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


class OptimizationImpact(str, Enum):
    """Влияние оптимизации"""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IndexType(str, Enum):
    """Тип индекса"""

    BTREE = "btree"
    HASH = "hash"
    FULLTEXT = "fulltext"
    CLUSTERED = "clustered"


class SQLQuery(BaseModel):
    """SQL запрос"""

    query_text: str = Field(..., description="Текст запроса")
    query_type: str = Field(default="SELECT", description="Тип запроса")
    tables: List[str] = Field(default_factory=list, description="Таблицы")
    estimated_rows: Optional[int] = Field(default=None, description="Оценка строк")
    execution_time_ms: Optional[float] = Field(
        default=None, description="Время выполнения (мс)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query_text": "SELECT * FROM Users WHERE age > 25",
                "query_type": "SELECT",
                "tables": ["Users"],
                "estimated_rows": 1000,
                "execution_time_ms": 150.5,
            }
        }
    )


class QueryAnalysis(BaseModel):
    """Анализ запроса"""

    complexity: QueryComplexity = Field(..., description="Сложность")
    issues: List[str] = Field(default_factory=list, description="Проблемы")
    missing_indexes: List[str] = Field(
        default_factory=list, description="Отсутствующие индексы"
    )
    full_table_scans: int = Field(
        default=0, ge=0, description="Полные сканирования таблиц"
    )
    estimated_cost: float = Field(default=0.0, ge=0, description="Оценка стоимости")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "complexity": "moderate",
                "issues": ["Missing index on age column"],
                "missing_indexes": ["Users.age"],
                "full_table_scans": 1,
                "estimated_cost": 250.5,
            }
        }
    )


class IndexRecommendation(BaseModel):
    """Рекомендация по индексу"""

    table_name: str = Field(..., description="Таблица")
    column_names: List[str] = Field(..., description="Колонки")
    index_type: IndexType = Field(default=IndexType.BTREE, description="Тип индекса")
    impact: OptimizationImpact = Field(..., description="Влияние")
    reason: str = Field(..., description="Причина")
    estimated_improvement_percent: float = Field(
        ..., ge=0, le=100, description="Оценка улучшения %"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "table_name": "Users",
                "column_names": ["age"],
                "index_type": "btree",
                "impact": "high",
                "reason": "Frequently used in WHERE clause",
                "estimated_improvement_percent": 75.0,
            }
        }
    )


class OptimizedQuery(BaseModel):
    """Оптимизированный запрос"""

    original_query: str = Field(..., description="Оригинальный запрос")
    optimized_query: str = Field(..., description="Оптимизированный запрос")
    improvements: List[str] = Field(default_factory=list, description="Улучшения")
    estimated_speedup: float = Field(..., ge=1.0, description="Оценка ускорения (раз)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "original_query": "SELECT * FROM Users WHERE age > 25",
                "optimized_query": "SELECT id, name FROM Users WHERE age > 25",
                "improvements": ["Removed SELECT *", "Added index hint"],
                "estimated_speedup": 2.5,
            }
        }
    )


class PerformancePrediction(BaseModel):
    """Предсказание производительности"""

    query: str = Field(..., description="Запрос")
    predicted_time_ms: float = Field(..., ge=0, description="Время (мс)")
    predicted_rows: int = Field(..., ge=0, description="Строк")
    confidence: float = Field(..., ge=0, le=1, description="Уверенность")
    bottlenecks: List[str] = Field(default_factory=list, description="Узкие места")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "SELECT * FROM Users",
                "predicted_time_ms": 500.0,
                "predicted_rows": 10000,
                "confidence": 0.85,
                "bottlenecks": ["Full table scan"],
            }
        }
    )


class OptimizationResult(BaseModel):
    """Результат оптимизации"""

    query_analysis: QueryAnalysis = Field(..., description="Анализ")
    index_recommendations: List[IndexRecommendation] = Field(
        default_factory=list, description="Рекомендации по индексам"
    )
    optimized_query: Optional[OptimizedQuery] = Field(
        default=None, description="Оптимизированный запрос"
    )
    performance_prediction: Optional[PerformancePrediction] = Field(
        default=None, description="Предсказание производительности"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query_analysis": {},
                "index_recommendations": [],
                "optimized_query": None,
                "performance_prediction": None,
            }
        }
    )


__all__ = [
    "QueryComplexity",
    "OptimizationImpact",
    "IndexType",
    "SQLQuery",
    "QueryAnalysis",
    "IndexRecommendation",
    "OptimizedQuery",
    "PerformancePrediction",
    "OptimizationResult",
]
