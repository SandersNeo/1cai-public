"""
DevOps Domain Models

Pydantic модели для DevOps модуля согласно Clean Architecture.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PipelineStage(str, Enum):
    """Стадии CI/CD pipeline"""
    BUILD = "build"
    TEST = "test"
    DEPLOY = "deploy"
    ALL = "all"


class OptimizationEffort(str, Enum):
    """Уровень усилий для оптимизации"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class OptimizationPriority(str, Enum):
    """Приоритет оптимизации"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PipelineConfig(BaseModel):
    """Конфигурация CI/CD pipeline"""
    total_duration: int = Field(..., description="Общая длительность в секундах")
    build_time: Optional[int] = Field(None, description="Время сборки в секундах")
    test_time: Optional[int] = Field(None, description="Время тестирования в секундах")
    deploy_time: Optional[int] = Field(None, description="Время деплоя в секундах")
    success_rate: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Процент успешных запусков")

    @field_validator('total_duration', 'build_time', 'test_time', 'deploy_time')
    @classmethod
    def validate_positive(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("Duration must be positive")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_duration": 1500,
                "build_time": 300,
                "test_time": 900,
                "deploy_time": 300,
                "success_rate": 0.95
            }
        }
    )


class PipelineOptimization(BaseModel):
    """Рекомендация по оптимизации pipeline"""

    optimization: str = Field(..., description="Название оптимизации")
    stage: PipelineStage = Field(..., description="Стадия pipeline")
    description: str = Field(..., description="Описание оптимизации")
    implementation: str = Field(..., description="Как реализовать")
    expected_speedup_percent: int = Field(..., ge=0,
                                          le=100, description="Ожидаемое ускорение в %")
    effort: OptimizationEffort = Field(..., description="Уровень усилий")
    priority: int = Field(..., ge=0, le=10, description="Приоритет (0-10)")

    class Config:
        json_schema_extra = {
            "example": {
                "optimization": "Docker Layer Caching",
                "stage": "build",
                "description": "Use Docker layer caching to speed up builds",
                "implementation": "Add cache-from and cache-to flags",
                "expected_speedup_percent": 45,
                "effort": "low",
                "priority": 8
            }
        }


class LogSeverity(str, Enum):
    """Уровень серьезности в логах"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogCategory(str, Enum):
    """Категория ошибки в логах"""
    MEMORY = "memory"
    NETWORK = "network"
    DATABASE = "database"
    SECURITY = "security"
    CODE = "code"
    UNKNOWN = "unknown"


class LogError(BaseModel):
    """Ошибка в логах"""

    line: str = Field(..., description="Строка лога с ошибкой")
    category: LogCategory = Field(..., description="Категория ошибки")
    severity: LogSeverity = Field(..., description="Уровень серьезности")
    diagnosis: str = Field(..., description="Диагноз проблемы")


class LogAnomaly(BaseModel):
    """Аномалия в логах"""

    type: str = Field(..., description="Тип аномалии")
    timestamp: str = Field(..., description="Время обнаружения")
    severity: LogSeverity = Field(..., description="Уровень серьезности")
    metric: Optional[str] = Field(None, description="Метрика аномалии")
    possible_cause: str = Field(..., description="Возможная причина")


class LogAnalysisResult(BaseModel):
    """Результат анализа логов"""

    summary: Dict[str, Any] = Field(..., description="Сводка анализа")
    errors_by_category: Dict[str, int] = Field(
        default_factory=dict, description="Ошибки по категориям")
    anomalies: List[LogAnomaly] = Field(
        default_factory=list, description="Обнаруженные аномалии")
    patterns: List[Dict[str, Any]] = Field(
        default_factory=list, description="Паттерны в логах")
    recommendations: List[str] = Field(default_factory=list, description="Рекомендации")
    timestamp: str = Field(default_factory=lambda: datetime.now(
    ).isoformat(), description="Время анализа")

    class Config:
        json_schema_extra = {
            "example": {
                "summary": {
                    "errors_found": 45,
                    "warnings_found": 120,
                    "anomalies_found": 2
                },
                "errors_by_category": {
                    "memory": 15,
                    "network": 20,
                    "database": 10
                },
                "anomalies": [],
                "patterns": [],
                "recommendations": ["Investigate memory usage"]
            }
        }


class CostOptimization(BaseModel):
    """Рекомендация по оптимизации затрат"""

    resource: str = Field(..., description="Ресурс для оптимизации")
    current: str = Field(..., description="Текущее состояние")
    recommended: str = Field(..., description="Рекомендуемое состояние")
    current_cost: float = Field(..., ge=0, description="Текущая стоимость")
    optimized_cost: float = Field(..., ge=0, description="Оптимизированная стоимость")
    savings_month: float = Field(..., ge=0, description="Экономия в месяц")
    savings_percent: int = Field(..., ge=0, le=100, description="Процент экономии")
    reason: str = Field(..., description="Причина оптимизации")
    risk: str = Field(..., description="Уровень риска (low/medium/high)")
    effort: OptimizationEffort = Field(..., description="Уровень усилий")


class CostOptimizationResult(BaseModel):
    """Результат оптимизации затрат"""

    current_cost_month: float = Field(..., ge=0,
                                      description="Текущая стоимость в месяц")
    optimized_cost_month: float = Field(..., ge=0,
                                        description="Оптимизированная стоимость")
    total_savings_month: float = Field(..., ge=0, description="Общая экономия в месяц")
    savings_percent: int = Field(..., ge=0, le=100, description="Процент экономии")
    optimizations: List[CostOptimization] = Field(
        default_factory=list, description="Список оптимизаций")
    annual_savings: float = Field(..., ge=0, description="Годовая экономия")
    timestamp: str = Field(default_factory=lambda: datetime.now(
    ).isoformat(), description="Время анализа")

    class Config:
        json_schema_extra = {
            "example": {
                "current_cost_month": 2500.0,
                "optimized_cost_month": 1600.0,
                "total_savings_month": 900.0,
                "savings_percent": 36,
                "optimizations": [],
                "annual_savings": 10800.0
            }
        }


class InfrastructureConfig(BaseModel):
    """Конфигурация инфраструктуры"""

    provider: str = Field(..., description="Cloud provider (aws/azure/gcp)")
    instance_type: str = Field(..., description="Тип инстанса")
    instance_count: int = Field(default=1, ge=1, description="Количество инстансов")
    pricing_model: str = Field(default="on_demand", description="Модель оплаты")
    region: Optional[str] = Field(None, description="Регион")

    class Config:
        json_schema_extra = {
            "example": {
                "provider": "aws",
                "instance_type": "m5.2xlarge",
                "instance_count": 3,
                "pricing_model": "on_demand",
                "region": "eu-west-1"
            }
        }


class UsageMetrics(BaseModel):
    """Метрики использования ресурсов"""

    cpu_avg: float = Field(..., ge=0, le=100, description="Средняя загрузка CPU в %")
    memory_avg: float = Field(..., ge=0, le=100,
                              description="Средняя загрузка памяти в %")
    storage_iops: Optional[int] = Field(None, ge=0, description="IOPS хранилища")
    network_throughput: Optional[float] = Field(
        None, ge=0, description="Пропускная способность сети")

    class Config:
        json_schema_extra = {
            "example": {
                "cpu_avg": 35.5,
                "memory_avg": 45.2,
                "storage_iops": 800,
                "network_throughput": 150.5
            }
        }


__all__ = [
    # Enums
    "PipelineStage",
    "OptimizationEffort",
    "OptimizationPriority",
    "LogSeverity",
    "LogCategory",
    # Models
    "PipelineConfig",
    "PipelineMetrics",
    "PipelineOptimization",
    "LogError",
    "LogAnomaly",
    "LogAnalysisResult",
    "CostOptimization",
    "CostOptimizationResult",
    "InfrastructureConfig",
    "UsageMetrics",
]
