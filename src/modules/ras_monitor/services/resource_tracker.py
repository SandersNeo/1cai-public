"""
Resource Tracker Service

Сервис для отслеживания ресурсов кластера.
"""

from typing import List

from src.modules.ras_monitor.domain.exceptions import ResourceMonitoringError
from src.modules.ras_monitor.domain.models import (
    ClusterMetrics,
    ResourceType,
    ResourceUsage,
)
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class ResourceTracker:
    """
    Сервис отслеживания ресурсов

    Features:
    - CPU monitoring
    - Memory monitoring
    - Connection tracking
    - Resource trends
    """

    def __init__(self, monitoring_repository=None):
        """
        Args:
            monitoring_repository: Repository для thresholds
        """
        if monitoring_repository is None:
            from src.modules.ras_monitor.repositories import MonitoringRepository
            monitoring_repository = MonitoringRepository()

        self.monitoring_repository = monitoring_repository

    async def track_resources(
        self,
        metrics: ClusterMetrics
    ) -> List[ResourceUsage]:
        """
        Отслеживание ресурсов

        Args:
            metrics: Метрики кластера

        Returns:
            Список ResourceUsage
        """
        try:
            logger.info("Tracking resources")

            resources = []

            # CPU
            cpu_max = self.monitoring_repository.get_max_value("cpu_percent")
            resources.append(
                ResourceUsage(
                    resource_type=ResourceType.CPU,
                    current_value=metrics.cpu_usage_percent,
                    max_value=cpu_max,
                    usage_percent=metrics.cpu_usage_percent,
                    trend=self._determine_trend(
                        metrics.cpu_usage_percent,
                        cpu_max
                    )
                )
            )

            # Memory
            memory_max = self.monitoring_repository.get_max_value(
                "memory_mb"
            )
            memory_percent = (
                metrics.memory_usage_mb / memory_max * 100
                if memory_max > 0 else 0
            )
            resources.append(
                ResourceUsage(
                    resource_type=ResourceType.MEMORY,
                    current_value=metrics.memory_usage_mb,
                    max_value=memory_max,
                    usage_percent=round(memory_percent, 2),
                    trend=self._determine_trend(
                        memory_percent,
                        100.0
                    )
                )
            )

            # Connections
            connections_max = self.monitoring_repository.get_max_value(
                "connections"
            )
            connections_percent = (
                metrics.total_connections / connections_max * 100
                if connections_max > 0 else 0
            )
            resources.append(
                ResourceUsage(
                    resource_type=ResourceType.CONNECTIONS,
                    current_value=float(metrics.total_connections),
                    max_value=float(connections_max),
                    usage_percent=round(connections_percent, 2),
                    trend=self._determine_trend(
                        connections_percent,
                        100.0
                    )
                )
            )

            return resources

        except Exception as e:
            logger.error("Failed to track resources: %s", e)
            raise ResourceMonitoringError(
                f"Failed to track resources: {e}",
                details={}
            )

    def _determine_trend(
        self,
        current_value: float,
        max_value: float
    ) -> str:
        """Определение тренда"""
        usage_percent = (
            current_value / max_value * 100
            if max_value > 0 else 0
        )

        if usage_percent > 80:
            return "up"
        elif usage_percent < 30:
            return "down"
        else:
            return "stable"

    async def predict_resource_exhaustion(
        self,
        resources: List[ResourceUsage]
    ) -> List[dict]:
        """
        Предсказание исчерпания ресурсов

        Args:
            resources: Список ресурсов

        Returns:
            Список предупреждений
        """
        warnings = []

        for resource in resources:
            if resource.usage_percent > 90:
                warnings.append({
                    "resource_type": resource.resource_type.value,
                    "severity": "critical",
                    "message": f"{resource.resource_type.value} usage is critical",
                    "current_percent": resource.usage_percent,
                    "estimated_time_to_exhaustion": "< 1 hour"
                })
            elif resource.usage_percent > 80:
                warnings.append({
                    "resource_type": resource.resource_type.value,
                    "severity": "warning",
                    "message": f"{resource.resource_type.value} usage is high",
                    "current_percent": resource.usage_percent,
                    "estimated_time_to_exhaustion": "< 4 hours"
                })

        return warnings


__all__ = ["ResourceTracker"]
