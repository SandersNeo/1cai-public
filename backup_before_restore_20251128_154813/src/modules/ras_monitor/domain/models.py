"""
RAS Monitor Domain Models

Pydantic модели для RAS Monitor модуля (мониторинг кластера 1С).
"""

from datetime import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class SessionState(str, Enum):
    """Состояние сессии"""

    ACTIVE = "active"
    SLEEPING = "sleeping"
    BLOCKED = "blocked"
    TERMINATED = "terminated"


class AlertSeverity(str, Enum):
    """Severity алертов"""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class ResourceType(str, Enum):
    """Тип ресурса"""

    CPU = "cpu"
    MEMORY = "memory"
    CONNECTIONS = "connections"
    LOCKS = "locks"


class ClusterInfo(BaseModel):
    """Информация о кластере"""

    cluster_id: str = Field(..., description="ID кластера")
    name: str = Field(..., description="Название кластера")
    host: str = Field(..., description="Хост")
    port: int = Field(..., ge=1, le=65535, description="Порт")
    version: str = Field(..., description="Версия платформы")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cluster_id": "cluster-001",
                "name": "Production Cluster",
                "host": "localhost",
                "port": 1541,
                "version": "8.3.22",
            }
        }
    )


class Session(BaseModel):
    """Сессия пользователя"""

    session_id: str = Field(..., description="ID сессии")
    user_name: str = Field(..., description="Имя пользователя")
    application: str = Field(..., description="Приложение")
    started_at: datetime = Field(..., description="Время начала")
    state: SessionState = Field(..., description="Состояние")
    cpu_time_ms: int = Field(..., ge=0, description="CPU время (мс)")
    memory_mb: float = Field(..., ge=0, description="Память (МБ)")
    connections_count: int = Field(..., ge=0, description="Количество соединений")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "session-123",
                "user_name": "User1",
                "application": "1CV8C",
                "started_at": "2025-11-27T10:00:00",
                "state": "active",
                "cpu_time_ms": 5000,
                "memory_mb": 256.5,
                "connections_count": 2,
            }
        }
    )


class ClusterMetrics(BaseModel):
    """Метрики кластера"""

    total_sessions: int = Field(..., ge=0, description="Всего сессий")
    active_sessions: int = Field(..., ge=0, description="Активных сессий")
    total_connections: int = Field(..., ge=0, description="Всего соединений")
    cpu_usage_percent: float = Field(..., ge=0, le=100, description="CPU %")
    memory_usage_mb: float = Field(..., ge=0, description="Память (МБ)")
    avg_response_time_ms: float = Field(..., ge=0, description="Avg response (мс)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_sessions": 50,
                "active_sessions": 30,
                "total_connections": 100,
                "cpu_usage_percent": 65.5,
                "memory_usage_mb": 2048.0,
                "avg_response_time_ms": 150.0,
            }
        }
    )


class ResourceAlert(BaseModel):
    """Алерт по ресурсам"""

    resource_type: ResourceType = Field(..., description="Тип ресурса")
    severity: AlertSeverity = Field(..., description="Severity")
    message: str = Field(..., description="Сообщение")
    current_value: float = Field(..., description="Текущее значение")
    threshold: float = Field(..., description="Порог")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "resource_type": "cpu",
                "severity": "warning",
                "message": "High CPU usage detected",
                "current_value": 85.0,
                "threshold": 80.0,
                "timestamp": "2025-11-27T10:00:00",
            }
        }
    )


class SessionAnalysis(BaseModel):
    """Анализ сессий"""

    total_sessions: int = Field(..., ge=0)
    sessions_by_state: dict = Field(default_factory=dict)
    top_cpu_sessions: List[Session] = Field(default_factory=list)
    top_memory_sessions: List[Session] = Field(default_factory=list)
    long_running_sessions: List[Session] = Field(default_factory=list)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_sessions": 50,
                "sessions_by_state": {"active": 30, "sleeping": 20},
                "top_cpu_sessions": [],
                "top_memory_sessions": [],
                "long_running_sessions": [],
            }
        }
    )


class ResourceUsage(BaseModel):
    """Использование ресурсов"""

    resource_type: ResourceType = Field(..., description="Тип ресурса")
    current_value: float = Field(..., description="Текущее значение")
    max_value: float = Field(..., description="Максимальное значение")
    usage_percent: float = Field(..., ge=0, le=100, description="% использования")
    trend: str = Field(default="stable", description="Тренд (up/down/stable)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "resource_type": "memory",
                "current_value": 2048.0,
                "max_value": 4096.0,
                "usage_percent": 50.0,
                "trend": "stable",
            }
        }
    )


__all__ = [
    "SessionState",
    "AlertSeverity",
    "ResourceType",
    "ClusterInfo",
    "Session",
    "ClusterMetrics",
    "ResourceAlert",
    "SessionAnalysis",
    "ResourceUsage",
]
