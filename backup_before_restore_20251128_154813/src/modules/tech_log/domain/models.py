"""
Tech Log Analyzer Domain Models

Pydantic модели для Tech Log Analyzer модуля.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Severity(str, Enum):
    """Severity levels"""

    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class EventType(str, Enum):
    """Tech log event types"""

    DBMSSQL = "DBMSSQL"
    SDBL = "SDBL"
    CALL = "CALL"
    EXCP = "EXCP"
    TLOCK = "TLOCK"
    TTIMEOUT = "TTIMEOUT"


class IssueType(str, Enum):
    """Performance issue types"""

    SLOW_QUERY = "slow_query"
    SLOW_METHOD = "slow_method"
    LOCK = "lock"
    EXCEPTION = "exception"
    MEMORY = "memory"


class TechLogEvent(BaseModel):
    """Событие технологического журнала"""

    timestamp: datetime = Field(..., description="Timestamp события")
    duration_ms: int = Field(..., ge=0, description="Длительность в мс")
    event_type: str = Field(..., description="Тип события")
    process: str = Field(..., description="Процесс")
    user: str = Field(default="", description="Пользователь")
    application: str = Field(default="", description="Приложение")
    event: str = Field(..., description="Событие")
    context: str = Field(default="", description="Контекст")
    sql: Optional[str] = Field(default=None, description="SQL запрос")
    method: Optional[str] = Field(default=None, description="Метод")
    error: Optional[str] = Field(default=None, description="Ошибка")
    severity: Severity = Field(default=Severity.INFO, description="Severity")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "timestamp": "2025-11-27T10:00:00",
                "duration_ms": 1500,
                "event_type": "DBMSSQL",
                "process": "rphost",
                "user": "User1",
                "application": "1CV8",
                "event": "Query",
                "context": "Document.Sales",
                "sql": "SELECT * FROM Document",
                "severity": "warning",
            }
        }
    )


class PerformanceIssue(BaseModel):
    """Проблема производительности"""

    issue_type: IssueType = Field(..., description="Тип проблемы")
    severity: Severity = Field(..., description="Severity")
    description: str = Field(..., description="Описание")
    location: str = Field(..., description="Локация")
    metric_value: float = Field(..., description="Значение метрики")
    threshold: float = Field(..., description="Порог")
    occurrences: int = Field(..., ge=1, description="Количество вхождений")
    recommendation: str = Field(..., description="Рекомендация")
    auto_fix_available: bool = Field(default=False, description="Доступен auto-fix")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "issue_type": "slow_query",
                "severity": "warning",
                "description": "Slow SQL query detected",
                "location": "Document.Sales",
                "metric_value": 2500.0,
                "threshold": 1000.0,
                "occurrences": 15,
                "recommendation": "Add index on field X",
                "auto_fix_available": True,
            }
        }
    )


class LogAnalysisResult(BaseModel):
    """Результат анализа логов"""

    total_events: int = Field(..., ge=0, description="Всего событий")
    time_period_start: datetime = Field(..., description="Начало периода")
    time_period_end: datetime = Field(..., description="Конец периода")
    events_by_type: dict = Field(default_factory=dict, description="События по типам")
    events_by_severity: dict = Field(
        default_factory=dict, description="События по severity"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_events": 1000,
                "time_period_start": "2025-11-27T00:00:00",
                "time_period_end": "2025-11-27T23:59:59",
                "events_by_type": {"DBMSSQL": 500, "CALL": 300},
                "events_by_severity": {"warning": 50, "info": 950},
            }
        }
    )


class PerformanceAnalysisResult(BaseModel):
    """Результат анализа производительности"""

    performance_issues: List[PerformanceIssue] = Field(
        default_factory=list, description="Проблемы производительности"
    )
    top_slow_queries: List[dict] = Field(
        default_factory=list, description="Топ медленных запросов"
    )
    top_slow_methods: List[dict] = Field(
        default_factory=list, description="Топ медленных методов"
    )
    errors_by_type: dict = Field(default_factory=dict, description="Ошибки по типам")
    locks_analysis: dict = Field(default_factory=dict, description="Анализ блокировок")
    ai_recommendations: List[str] = Field(
        default_factory=list, description="AI рекомендации"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "performance_issues": [],
                "top_slow_queries": [],
                "top_slow_methods": [],
                "errors_by_type": {},
                "locks_analysis": {},
                "ai_recommendations": [],
            }
        }
    )


__all__ = [
    "Severity",
    "EventType",
    "IssueType",
    "TechLogEvent",
    "PerformanceIssue",
    "LogAnalysisResult",
    "PerformanceAnalysisResult",
]
