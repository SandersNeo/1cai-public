"""
Alert Manager Service

Сервис для управления алертами.
"""

from datetime import datetime
from typing import List

from src.modules.ras_monitor.domain.models import (
    AlertSeverity,
    ResourceAlert,
    ResourceType,
    ResourceUsage,
)
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class AlertManager:
    """
    Сервис управления алертами

    Features:
    - Alert generation
    - Threshold monitoring
    - Alert prioritization
    - Notification management
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

    async def generate_alerts(
        self,
        resources: List[ResourceUsage]
    ) -> List[ResourceAlert]:
        """
        Генерация алертов

        Args:
            resources: Список ресурсов

        Returns:
            Список ResourceAlert
        """
        logger.info("Generating alerts")

        alerts = []

        for resource in resources:
            # Get threshold
            threshold_key = f"{resource.resource_type.value}_percent"
            threshold = self.monitoring_repository.get_threshold(
                threshold_key
            )

            # Check if threshold exceeded
            if resource.usage_percent > threshold:
                severity = self._determine_severity(
                    resource.usage_percent
                )

                alert = ResourceAlert(
                    resource_type=resource.resource_type,
                    severity=severity,
                    message=self._generate_message(
                        resource.resource_type,
                        resource.usage_percent
                    ),
                    current_value=resource.usage_percent,
                    threshold=threshold,
                    timestamp=datetime.now()
                )

                alerts.append(alert)

        return alerts

    def _determine_severity(self, usage_percent: float) -> AlertSeverity:
        """Определение severity"""
        if usage_percent >= 90:
            return AlertSeverity.CRITICAL
        elif usage_percent >= 80:
            return AlertSeverity.WARNING
        else:
            return AlertSeverity.INFO

    def _generate_message(
        self,
        resource_type: ResourceType,
        usage_percent: float
    ) -> str:
        """Генерация сообщения"""
        return (
            f"High {resource_type.value} usage detected: "
            f"{usage_percent:.1f}%"
        )

    async def prioritize_alerts(
        self,
        alerts: List[ResourceAlert]
    ) -> List[ResourceAlert]:
        """
        Приоритизация алертов

        Args:
            alerts: Список алертов

        Returns:
            Отсортированный список алертов
        """
        # Sort by severity (critical first)
        severity_order = {
            AlertSeverity.CRITICAL: 0,
            AlertSeverity.WARNING: 1,
            AlertSeverity.INFO: 2
        }

        return sorted(
            alerts,
            key=lambda a: (
                severity_order.get(a.severity, 3),
                -a.current_value
            )
        )

    async def should_notify(
        self,
        alert: ResourceAlert
    ) -> bool:
        """
        Проверка необходимости уведомления

        Args:
            alert: Алерт

        Returns:
            True если нужно уведомить
        """
        # Always notify for critical alerts
        if alert.severity == AlertSeverity.CRITICAL:
            return True

        # Notify for warnings if threshold significantly exceeded
        if alert.severity == AlertSeverity.WARNING:
            return alert.current_value > alert.threshold * 1.1

        # Don't notify for info alerts
        return False


__all__ = ["AlertManager"]
