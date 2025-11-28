"""
Metrics Service
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.infrastructure.logging.structured_logging import StructuredLogger
from src.modules.metrics.domain.models import (AggregatedMetrics,
                                               MetricCollectionRequest,
                                               MetricRecord)

logger = StructuredLogger(__name__).logger


class MetricsService:
    """Service for metrics management (Singleton)"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MetricsService, cls).__new__(cls)
            # Global storage (in-memory)
            cls._instance.metrics_storage: List[MetricRecord] = []
            cls._instance.performance_metrics: Dict[str, List[float]] = {}
        return cls._instance

    def collect_metrics(
            self, request: MetricCollectionRequest) -> Dict[str, Any]:
        """Collect metrics from services"""
        try:
