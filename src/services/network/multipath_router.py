# [NEXUS IDENTITY] ID: 4118869023884388007 | DATE: 2025-11-19

"""
Multi-Path Router - Маршрутизация с несколькими путями
Версия: 1.0.0

Поддержка:
- Несколько сетевых путей одновременно
- Автоматический failover
- Балансировка нагрузки
- Адаптивный выбор пути
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Awaitable
import httpx

try:
    from src.monitoring.prometheus_metrics import (
        network_path_health,
        network_path_latency_ms,
        network_failover_total,
    )
except ImportError:
    # Fallback для случаев когда prometheus_metrics не доступен
    network_path_health = None
    network_path_latency_ms = None
    network_failover_total = None

logger = logging.getLogger(__name__)


class PathStatus(str, Enum):
    """Статус сетевого пути"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class NetworkPath:
    """Сетевой путь"""

    path_id: str
    path_type: str  # primary, backup, vpn, proxy, etc.
    endpoint: str  # URL или IP
    enabled: bool = True
    priority: int = 0  # Чем меньше, тем выше приоритет
    timeout: float = 5.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PathMetrics:
    """Метрики сетевого пути"""

    path_id: str
    status: PathStatus
    latency_ms: float = 0.0
    success_count: int = 0
    failure_count: int = 0
    last_check: Optional[datetime] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0


class MultiPathRouter:
    """
    Маршрутизатор с поддержкой нескольких путей.

    Особенности:
    - Несколько путей одновременно
    - Автоматический failover
    - Балансировка нагрузки
    - Адаптивный выбор пути
    """

    def __init__(
        self,
        paths: Optional[List[NetworkPath]] = None,
        health_check_interval: float = 60.0,
        failure_threshold: int = 3,
    ):
        """
        Args:
            paths: Список сетевых путей
            health_check_interval: Интервал проверки здоровья в секундах
            failure_threshold: Количество последовательных ошибок для пометки как unhealthy
        """
        self.paths = paths or []
        self.health_check_interval = health_check_interval
        self.failure_threshold = failure_threshold

        self.path_metrics: Dict[str, PathMetrics] = {}
        self._health_check_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

        # Инициализация метрик
        for path in self.paths:
            self.path_metrics[path.path_id] = PathMetrics(
                path_id=path.path_id, status=PathStatus.UNKNOWN
            )

    async def start_health_monitoring(self):
        """Запустить мониторинг здоровья путей"""
        if self._health_check_task and not self._health_check_task.done():
            return

        self._stop_event.clear()
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("Multi-path router health monitoring started")

    async def stop_health_monitoring(self):
        """Остановить мониторинг"""
        self._stop_event.set()
        if self._health_check_task:
            await self._health_check_task
        logger.info("Multi-path router health monitoring stopped")

    async def _health_check_loop(self):
        """Цикл проверки здоровья"""
        while not self._stop_event.is_set():
            try:
                await self._check_all_paths()
            except Exception as e:
                logger.error(f"Error in health check loop: {e}", exc_info=True)

            try:
                await asyncio.wait_for(
                    self._stop_event.wait(), timeout=self.health_check_interval
                )
            except asyncio.TimeoutError:
                continue

    async def _check_all_paths(self):
        """Проверить все пути"""
        tasks = []
        for path in self.paths:
            if path.enabled:
                tasks.append(self._check_path(path))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _check_path(self, path: NetworkPath):
        """Проверить один путь"""
        metrics = self.path_metrics.get(path.path_id)
        if not metrics:
            return

        try:
            start_time = time.time()
            # Простая проверка доступности
            async with httpx.AsyncClient(timeout=path.timeout) as client:
                # Пробуем HEAD запрос для проверки
                response = await client.head(path.endpoint, follow_redirects=True)
                latency_ms = (time.time() - start_time) * 1000

                is_healthy = response.status_code < 400

                metrics.latency_ms = latency_ms
                metrics.last_check = datetime.utcnow()

                if is_healthy:
                    metrics.success_count += 1
                    metrics.consecutive_successes += 1
                    metrics.consecutive_failures = 0

                    # Определяем статус
                    if latency_ms > 5000:  # > 5 секунд = degraded
                        metrics.status = PathStatus.DEGRADED
                    else:
                        metrics.status = PathStatus.HEALTHY
                else:
                    metrics.failure_count += 1
                    metrics.consecutive_failures += 1
                    metrics.consecutive_successes = 0

                    if metrics.consecutive_failures >= self.failure_threshold:
                        metrics.status = PathStatus.UNHEALTHY
                    else:
                        metrics.status = PathStatus.DEGRADED

                # Обновляем метрики Prometheus
                if network_path_health:
                    network_path_health.labels(
                        path_id=path.path_id, path_type=path.path_type
                    ).set(1.0 if metrics.status == PathStatus.HEALTHY else 0.5)

                if network_path_latency_ms:
                    network_path_latency_ms.labels(
                        path_id=path.path_id, path_type=path.path_type
                    ).set(latency_ms)

        except Exception as e:
            metrics.failure_count += 1
            metrics.consecutive_failures += 1
            metrics.consecutive_successes = 0
            metrics.last_check = datetime.utcnow()

            if metrics.consecutive_failures >= self.failure_threshold:
                metrics.status = PathStatus.UNHEALTHY
            else:
                metrics.status = PathStatus.DEGRADED

            if network_path_health:
                network_path_health.labels(
                    path_id=path.path_id, path_type=path.path_type
                ).set(0.0)

            logger.debug(f"Path {path.path_id} health check failed: {e}")

    async def send_request(
        self, request_func: Callable[..., Awaitable[Any]], *args, **kwargs
    ) -> Any:
        """
        Отправить запрос через лучший доступный путь.

        Args:
            request_func: Функция для выполнения запроса
            *args: Аргументы функции
            **kwargs: Ключевые аргументы функции

        Returns:
            Результат запроса
        """
        # Сортируем пути по приоритету и статусу
        sorted_paths = sorted(
            [p for p in self.paths if p.enabled],
            key=lambda x: (
                (
                    0
                    if self.path_metrics.get(
                        x.path_id, PathMetrics(x.path_id, PathStatus.UNKNOWN)
                    ).status
                    == PathStatus.HEALTHY
                    else 1
                ),
                x.priority,
            ),
        )

        last_error: Optional[Exception] = None

        for path in sorted_paths:
            metrics = self.path_metrics.get(path.path_id)
            if metrics and metrics.status == PathStatus.UNHEALTHY:
                continue

            try:
                # Выполняем запрос через этот путь
                result = await request_func(*args, **kwargs)

                # Успешный запрос
                metrics.success_count += 1
                metrics.consecutive_successes += 1
                metrics.consecutive_failures = 0

                return result

            except Exception as e:
                last_error = e
                logger.warning(f"Path {path.path_id} failed: {e}")

                # Обновляем метрики
                metrics.failure_count += 1
                metrics.consecutive_failures += 1
                metrics.consecutive_successes = 0

                # Записываем failover
                if (
                    path != sorted_paths[-1] and network_failover_total
                ):  # Не последний путь
                    next_path = sorted_paths[sorted_paths.index(path) + 1]
                    network_failover_total.labels(
                        from_path=path.path_id,
                        to_path=next_path.path_id,
                        reason=str(type(e).__name__),
                    ).inc()

                # Продолжаем к следующему пути
                continue

        # Все пути недоступны
        raise AllPathsFailedError(f"All network paths failed: {last_error}")

    def get_healthy_paths(self) -> List[NetworkPath]:
        """Получить список здоровых путей"""
        return [
            path
            for path in self.paths
            if path.enabled
            and self.path_metrics.get(
                path.path_id, PathMetrics(path.path_id, PathStatus.UNKNOWN)
            ).status
            == PathStatus.HEALTHY
        ]

    def get_path_metrics(self) -> Dict[str, PathMetrics]:
        """Получить метрики всех путей"""
        return self.path_metrics.copy()


class AllPathsFailedError(Exception):
    """Все сетевые пути недоступны"""
