"""
Cluster Monitor Service

Сервис для мониторинга кластера 1С.
"""

from typing import List

from src.modules.ras_monitor.domain.exceptions import ClusterConnectionError
from src.modules.ras_monitor.domain.models import (
    ClusterInfo,
    ClusterMetrics,
    Session,
    SessionState,
)
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class ClusterMonitor:
    """
    Сервис мониторинга кластера

    Features:
    - Cluster connection management
    - Metrics collection
    - Health checks
    - Performance monitoring
    """

    def __init__(self, monitoring_repository=None):
        """
        Args:
            monitoring_repository: Repository для thresholds
                                 (опционально, для dependency injection)
        """
        if monitoring_repository is None:
            from src.modules.ras_monitor.repositories import MonitoringRepository
            monitoring_repository = MonitoringRepository()

        self.monitoring_repository = monitoring_repository

    async def get_cluster_info(
        self,
        host: str,
        port: int = 1541
    ) -> ClusterInfo:
        """
        Получение информации о кластере

        Args:
            host: Хост кластера
            port: Порт кластера

        Returns:
            ClusterInfo
        """
        try:
            logger.info(
                "Getting cluster info",
                extra={"host": host, "port": port}
            )

            # Simulate cluster connection (в production: реальное подключение)
            cluster_info = ClusterInfo(
                cluster_id=f"cluster-{host}-{port}",
                name=f"Cluster at {host}",
                host=host,
                port=port,
                version="8.3.22"
            )

            return cluster_info

        except Exception as e:
            logger.error("Failed to get cluster info: %s", e)
            raise ClusterConnectionError(
                f"Failed to connect to cluster at {host}:{port}",
                details={"host": host, "port": port}
            )

    async def collect_metrics(
        self,
        cluster_id: str,
        sessions: List[Session]
    ) -> ClusterMetrics:
        """
        Сбор метрик кластера

        Args:
            cluster_id: ID кластера
            sessions: Список сессий

        Returns:
            ClusterMetrics
        """
        try:
            logger.info(
                "Collecting cluster metrics",
                extra={"cluster_id": cluster_id}
            )

            # Calculate metrics
            total_sessions = len(sessions)
            active_sessions = len([
                s for s in sessions
                if s.state == SessionState.ACTIVE
            ])

            total_connections = sum(
                s.connections_count for s in sessions
            )

            # CPU usage (weighted average)
            if sessions:
                total_cpu_time = sum(s.cpu_time_ms for s in sessions)
                cpu_usage_percent = min(
                    100.0,
                    (total_cpu_time / (total_sessions * 1000)) * 100
                )
            else:
                cpu_usage_percent = 0.0

            # Memory usage
            memory_usage_mb = sum(s.memory_mb for s in sessions)

            # Average response time (simplified)
            avg_response_time_ms = 150.0  # Placeholder

            return ClusterMetrics(
                total_sessions=total_sessions,
                active_sessions=active_sessions,
                total_connections=total_connections,
                cpu_usage_percent=round(cpu_usage_percent, 2),
                memory_usage_mb=round(memory_usage_mb, 2),
                avg_response_time_ms=avg_response_time_ms
            )

        except Exception as e:
            logger.error("Failed to collect metrics: %s", e)
            raise

    async def check_health(
        self,
        metrics: ClusterMetrics
    ) -> dict:
        """
        Проверка здоровья кластера

        Args:
            metrics: Метрики кластера

        Returns:
            Health status
        """
        health = {
            "status": "healthy",
            "issues": []
        }

        # Check CPU
        cpu_threshold = self.monitoring_repository.get_threshold("cpu_percent")
        if metrics.cpu_usage_percent > cpu_threshold:
            health["status"] = "warning"
            health["issues"].append(
                f"High CPU usage: {metrics.cpu_usage_percent}%"
            )

        # Check memory
        memory_threshold = self.monitoring_repository.get_threshold(
            "memory_mb"
        )
        if metrics.memory_usage_mb > memory_threshold:
            health["status"] = "warning"
            health["issues"].append(
                f"High memory usage: {metrics.memory_usage_mb} MB"
            )

        # Check response time
        response_threshold = self.monitoring_repository.get_threshold(
            "response_time_ms"
        )
        if metrics.avg_response_time_ms > response_threshold:
            health["status"] = "warning"
            health["issues"].append(
                f"Slow response time: {metrics.avg_response_time_ms} ms"
            )

        return health


__all__ = ["ClusterMonitor"]
