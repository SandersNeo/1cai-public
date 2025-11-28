"""RAS Monitor Service."""

from datetime import datetime, timedelta
from typing import List

from ..domain.monitoring import (
    Alert,
    AlertSeverity,
    AlertStatus,
    ClusterInfo,
    ClusterMetrics,
    ResourceUsage,
    Session,
    SessionAnalysis,
)


class RASMonitorService:
    """Service for monitoring 1C RAS cluster."""

    def __init__(self):
        """Initialize RAS monitor."""
        self.memory_threshold_percent = 80.0
        self.cpu_threshold_percent = 80.0
        self.connection_threshold_percent = 90.0

    async def get_cluster_info(self, host: str, port: int) -> ClusterInfo:
        """
        Get cluster information.

        Args:
            host: RAS server host
            port: RAS server port

        Returns:
            Cluster information

        Raises:
            ConnectionError: If can't connect to RAS
        """
        # TODO: Implement actual RAS connection
        # For now, return mock data
        return ClusterInfo(
            cluster_id=f"{host}:{port}",
            host=host,
            port=port,
            version="8.3.24",
            status="active",
            name="Production Cluster",
            started_at=datetime.now() - timedelta(days=30),
        )

    async def get_active_sessions(self, cluster_id: str) -> List[Session]:
        """
        Get active sessions from cluster.

        Args:
            cluster_id: Cluster ID

        Returns:
            List of active sessions
        """
        # TODO: Implement actual RAS API call
        # For now, return empty list
        return []

    async def get_cluster_metrics(self, cluster_id: str) -> ClusterMetrics:
        """
        Get cluster performance metrics.

        Args:
            cluster_id: Cluster ID

        Returns:
            Cluster metrics
        """
        # TODO: Implement actual metrics collection
        return ClusterMetrics(
            cluster_id=cluster_id,
            timestamp=datetime.now(),
            total_memory_mb=16384.0,
            used_memory_mb=8192.0,
            cpu_percent=45.0,
            active_sessions=25,
            total_sessions=100,
            blocked_sessions=0,
            active_connections=50,
            max_connections=200,
        )

    async def analyze_resource_usage(self, sessions: List[Session]) -> SessionAnalysis:
        """
        Analyze resource usage from sessions.

        Args:
            sessions: List of sessions

        Returns:
            Session analysis
        """
        if not sessions:
            return SessionAnalysis(
                total_sessions=0,
                active_sessions=0,
                idle_sessions=0,
                blocked_sessions=0,
                total_memory_mb=0.0,
                avg_memory_per_session_mb=0.0,
                total_cpu_percent=0.0,
            )

        active = [s for s in sessions if not s.is_idle]
        idle = [s for s in sessions if s.is_idle]
        blocked = [s for s in sessions if s.is_blocked]

        total_memory = sum(s.memory_mb for s in sessions)
        total_cpu = sum(s.cpu_percent for s in sessions)

        # Find top consumers
        top_memory = sorted(sessions, key=lambda s: s.memory_mb, reverse=True)[:5]
        top_cpu = sorted(sessions, key=lambda s: s.cpu_percent, reverse=True)[:5]

        # Generate recommendations
        recommendations = []
        if len(idle) > len(active):
            recommendations.append(
                "High number of idle sessions. Consider implementing session timeout."
            )
        if blocked:
            recommendations.append(
                f"{len(blocked)} blocked sessions detected. Review lock management."
            )

        return SessionAnalysis(
            total_sessions=len(sessions),
            active_sessions=len(active),
            idle_sessions=len(idle),
            blocked_sessions=len(blocked),
            total_memory_mb=total_memory,
            avg_memory_per_session_mb=total_memory / len(sessions),
            total_cpu_percent=total_cpu,
            top_memory_sessions=[s.session_id for s in top_memory],
            top_cpu_sessions=[s.session_id for s in top_cpu],
            recommendations=recommendations,
        )

    async def create_alert(
        self,
        cluster_id: str,
        metric_name: str,
        metric_value: float,
        threshold: float,
        severity: AlertSeverity = AlertSeverity.MEDIUM,
    ) -> Alert:
        """
        Create performance alert.

        Args:
            cluster_id: Cluster ID
            metric_name: Metric name (e.g., "memory_usage")
            metric_value: Current metric value
            threshold: Threshold value
            severity: Alert severity

        Returns:
            Created alert
        """
        alert_id = f"alert_{datetime.now().timestamp()}"

        title = f"{metric_name} exceeded threshold"
        description = (
            f"{metric_name} is {metric_value:.1f} (threshold: {threshold:.1f})"
        )

        return Alert(
            alert_id=alert_id,
            cluster_id=cluster_id,
            severity=severity,
            status=AlertStatus.ACTIVE,
            title=title,
            description=description,
            metric_name=metric_name,
            metric_value=metric_value,
            threshold=threshold,
        )

    async def check_thresholds(self, metrics: ClusterMetrics) -> List[Alert]:
        """
        Check metrics against thresholds and create alerts.

        Args:
            metrics: Cluster metrics

        Returns:
            List of alerts
        """
        alerts = []

        # Check memory usage
        if metrics.memory_usage_percent > self.memory_threshold_percent:
            alert = await self.create_alert(
                cluster_id=metrics.cluster_id,
                metric_name="memory_usage",
                metric_value=metrics.memory_usage_percent,
                threshold=self.memory_threshold_percent,
                severity=(
                    AlertSeverity.HIGH
                    if metrics.memory_usage_percent > 90
                    else AlertSeverity.MEDIUM
                ),
            )
            alerts.append(alert)

        # Check CPU usage
        if metrics.cpu_percent > self.cpu_threshold_percent:
            alert = await self.create_alert(
                cluster_id=metrics.cluster_id,
                metric_name="cpu_usage",
                metric_value=metrics.cpu_percent,
                threshold=self.cpu_threshold_percent,
                severity=(
                    AlertSeverity.HIGH
                    if metrics.cpu_percent > 90
                    else AlertSeverity.MEDIUM
                ),
            )
            alerts.append(alert)

        # Check connection pool
        if metrics.connection_usage_percent > self.connection_threshold_percent:
            alert = await self.create_alert(
                cluster_id=metrics.cluster_id,
                metric_name="connection_pool",
                metric_value=metrics.connection_usage_percent,
                threshold=self.connection_threshold_percent,
                severity=AlertSeverity.CRITICAL,
            )
            alerts.append(alert)

        # Check blocked sessions
        if metrics.blocked_sessions > 0:
            alert = await self.create_alert(
                cluster_id=metrics.cluster_id,
                metric_name="blocked_sessions",
                metric_value=float(metrics.blocked_sessions),
                threshold=0.0,
                severity=AlertSeverity.HIGH,
            )
            alerts.append(alert)

        return alerts

    async def get_resource_usage(self, cluster_id: str) -> ResourceUsage:
        """
        Get current resource usage.

        Args:
            cluster_id: Cluster ID

        Returns:
            Resource usage snapshot
        """
        # TODO: Implement actual resource monitoring
        return ResourceUsage(
            cluster_id=cluster_id,
            timestamp=datetime.now(),
            memory_total_mb=16384.0,
            memory_used_mb=8192.0,
            memory_available_mb=8192.0,
            cpu_count=8,
            cpu_percent=45.0,
            disk_total_gb=500.0,
            disk_used_gb=250.0,
        )
