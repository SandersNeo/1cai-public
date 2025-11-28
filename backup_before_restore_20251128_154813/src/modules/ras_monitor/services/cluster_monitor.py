"""
Cluster Monitor Service

Сервис для мониторинга кластера 1С.
"""

from typing import List, Optional

from src.modules.ras_monitor.domain.exceptions import ClusterConnectionError
from src.modules.ras_monitor.domain.models import (ClusterInfo, ClusterMetrics,
                                                   Session, SessionState)
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
            from src.modules.ras_monitor.repositories import \
                MonitoringRepository
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
