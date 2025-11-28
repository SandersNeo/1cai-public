"""Performance Aggregator Service - Unified Interface."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from ..domain.logs import LogAnalysisResult
from ..domain.monitoring import Alert, ClusterMetrics, SessionAnalysis
from ..domain.sql import OptimizationResult
from .log_analyzer import LogAnalyzerService
from .ras_monitor import RASMonitorService
from .sql_optimizer import SQLOptimizerService


@dataclass
class PerformanceHealth:
    """Overall performance health status."""

    status: str  # "healthy", "warning", "critical"
    score: float  # 0-100
    timestamp: datetime

    # Component scores
    log_score: float = 0.0
    ras_score: float = 0.0
    sql_score: float = 0.0

    # Issues
    critical_issues: int = 0
    warnings: int = 0

    # Recommendations
    top_recommendations: List[str] = field(default_factory=list)


@dataclass
class PerformanceReport:
    """Comprehensive performance report."""

    generated_at: datetime
    time_range_hours: int

    # Component reports
    log_analysis: Optional[LogAnalysisResult] = None
    cluster_metrics: Optional[ClusterMetrics] = None
    session_analysis: Optional[SessionAnalysis] = None

    # Alerts
    active_alerts: List[Alert] = field(default_factory=list)

    # Overall health
    health: Optional[PerformanceHealth] = None

    # Summary
    summary: Dict[str, any] = field(default_factory=dict)


class PerformanceAggregatorService:
    """Unified service for all performance monitoring."""

    def __init__(self):
        """Initialize aggregator with all services."""
        self.log_analyzer = LogAnalyzerService()
        self.ras_monitor = RASMonitorService()
        self.sql_optimizer = SQLOptimizerService()

    async def get_overall_health(
        self,
        cluster_id: Optional[str] = None
    ) -> PerformanceHealth:
        """
        Get overall performance health.

        Args:
            cluster_id: Optional cluster ID for RAS monitoring

        Returns:
            Performance health status
        """
        # Get component scores
        log_score = 100.0  # Default if no data
        ras_score = 100.0
        sql_score = 100.0

        critical_issues = 0
        warnings = 0
        recommendations = []

        # Check RAS if cluster_id provided
        if cluster_id:
            try:
