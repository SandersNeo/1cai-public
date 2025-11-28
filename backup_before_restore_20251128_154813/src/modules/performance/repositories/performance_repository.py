"""Performance Repository - Data Persistence Layer."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from ..domain.logs import LogAnalysisResult
from ..domain.monitoring import Alert, ClusterMetrics
from ..domain.sql import OptimizationResult


class PerformanceRepository:
    """Repository for performance data persistence."""

    def __init__(self, storage_path: str = "data/performance"):
        """
        Initialize repository.

        Args:
            storage_path: Path to storage directory
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    async def save_log_analysis(
        self,
        analysis: LogAnalysisResult
    ) -> str:
        """
        Save log analysis result.

        Args:
            analysis: Log analysis result

        Returns:
            Analysis ID
        """
        analysis_id = f"log_analysis_{datetime.now().timestamp()}"

        data = {
            "id": analysis_id,
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis.to_dict()
        }

        file_path = self.storage_path / "logs" / f"{analysis_id}.json"
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

        return analysis_id

    async def save_cluster_metrics(
        self,
        metrics: ClusterMetrics
    ) -> str:
        """
        Save cluster metrics.

        Args:
            metrics: Cluster metrics

        Returns:
            Metrics ID
        """
        metrics_id = f"cluster_metrics_{datetime.now().timestamp()}"

        data = {
            "id": metrics_id,
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics.to_dict()
        }

        file_path = self.storage_path / "clusters" / f"{metrics_id}.json"
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

        return metrics_id

    async def save_query_optimization(
        self,
        optimization: OptimizationResult
    ) -> str:
        """
        Save query optimization result.

        Args:
            optimization: Optimization result

        Returns:
            Optimization ID
        """
        opt_id = f"sql_opt_{datetime.now().timestamp()}"

        data = {
            "id": opt_id,
            "timestamp": datetime.now().isoformat(),
            "original_query": optimization.original_query.text,
            "optimized_query": optimization.optimized_query,
            "improvement_percent": optimization.expected_improvement_percent,
            "changes": optimization.changes,
            "recommendations": optimization.recommendations
        }

        file_path = self.storage_path / "sql" / f"{opt_id}.json"
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

        return opt_id

    async def save_alert(self, alert: Alert) -> str:
        """
        Save performance alert.

        Args:
            alert: Alert to save

        Returns:
            Alert ID
        """
        data = {
            "id": alert.alert_id,
            "cluster_id": alert.cluster_id,
            "severity": alert.severity.value,
            "status": alert.status.value,
            "title": alert.title,
            "description": alert.description,
            "metric_name": alert.metric_name,
            "metric_value": alert.metric_value,
            "threshold": alert.threshold,
            "created_at": alert.created_at.isoformat(),
        }

        file_path = self.storage_path / "alerts" / f"{alert.alert_id}.json"
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

        return alert.alert_id

    async def get_historical_data(
        self,
        data_type: str,
        days: int = 7
    ) -> List[Dict]:
        """
        Get historical performance data.

        Args:
            data_type: Type of data ("logs", "clusters", "sql", "alerts")
            days: Number of days to retrieve

        Returns:
            List of historical data entries
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        results = []

        data_dir = self.storage_path / data_type
        if not data_dir.exists():
            return results

        for file_path in data_dir.glob("*.json"):
            try:
