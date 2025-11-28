# [NEXUS IDENTITY] ID: -3078919085858154681 | DATE: 2025-11-19

"""
LLM Provider Health Monitor
Версия: 1.0.0

Мониторинг состояния LLM провайдеров с автоматическим переключением.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional

import httpx

from .llm_provider_manager import LLMProviderManager, ProviderConfig

logger = logging.getLogger(__name__)


class ProviderHealthStatus(str, Enum):
    """Статус здоровья провайдера"""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    DEGRADED = "degraded"  # Работает, но медленно


@dataclass
class ProviderHealth:
    """Информация о здоровье провайдера"""

    provider_name: str
    status: ProviderHealthStatus
    last_check: datetime
    latency_ms: Optional[float] = None
    failure_count: int = 0
    success_count: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class LLMHealthMonitor:
    """
    Мониторинг здоровья LLM провайдеров с автоматическим переключением.

    Особенности:
    - Периодическая проверка доступности провайдеров
    - Отслеживание latency и error rate
    - Автоматическое определение нездоровых провайдеров
    - Callback для уведомлений об изменении статуса
    """

    def __init__(
        self,
        manager: LLMProviderManager,
        check_interval_seconds: int = 60,
        failure_threshold: int = 3,
        recovery_threshold: int = 2,
        timeout_seconds: float = 5.0,
        degraded_latency_ms: float = 5000.0,  # > 5 секунд = degraded
    ):
        """
        Args:
            manager: LLM Provider Manager
            check_interval_seconds: Интервал проверки в секундах
            failure_threshold: Количество последовательных ошибок для пометки как unhealthy
            recovery_threshold: Количество успешных проверок для восстановления
            timeout_seconds: Timeout для health check запросов
            degraded_latency_ms: Latency выше этого значения = degraded
        """
        self.manager = manager
        self.check_interval = check_interval_seconds
        self.failure_threshold = failure_threshold
        self.recovery_threshold = recovery_threshold
        self.timeout = timeout_seconds
        self.degraded_latency_ms = degraded_latency_ms

        self.health_status: Dict[str, ProviderHealth] = {}
        self._monitoring_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        self._status_callbacks: list[
            Callable[[str, ProviderHealthStatus, ProviderHealthStatus], None]
        ] = []

        # Инициализация статусов для всех провайдеров
        for provider in self.manager.providers.values():
            if provider.enabled:
                self.health_status[provider.name] = ProviderHealth(
                    provider_name=provider.name,
                    status=ProviderHealthStatus.UNKNOWN,
                    last_check=datetime.utcnow(),
                )

    def add_status_callback(
        self,
        callback: Callable[[str, ProviderHealthStatus, ProviderHealthStatus], None],
    ) -> None:
        """Добавить callback для уведомлений об изменении статуса"""
        self._status_callbacks.append(callback)

    async def start_monitoring(self) -> None:
        """Запустить периодический мониторинг"""
        if self._monitoring_task and not self._monitoring_task.done():
            logger.warning("Health monitoring already running")
            return

        self._stop_event.clear()
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("LLM Health Monitor started")

    async def stop_monitoring(self) -> None:
        """Остановить мониторинг"""
        self._stop_event.set()
        if self._monitoring_task:
            await self._monitoring_task
        logger.info("LLM Health Monitor stopped")

    async def _monitoring_loop(self) -> None:
        """Основной цикл мониторинга"""
        while not self._stop_event.is_set():
            try:
