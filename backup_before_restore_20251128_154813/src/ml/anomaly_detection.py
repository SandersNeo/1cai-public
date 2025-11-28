"""
ML-based Anomaly Detection

Implements Isolation Forest for detecting anomalies in:
- Application logs
- System metrics
- Performance data
- Security events
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    ML-based anomaly detector using Isolation Forest

    Features:
    - Log anomaly detection
    - Metric anomaly detection
    - Adaptive thresholds
    - Feature extraction
    """

    def __init__(
        self,
        contamination: float = 0.1,
        n_estimators: int = 100
    ):
        """
        Initialize anomaly detector

        Args:
            contamination: Expected proportion of anomalies (0.1 = 10%)
            n_estimators: Number of trees in forest
        """
        self.logger = logging.getLogger("anomaly_detector")

        # Isolation Forest model
        self.model = IsolationForest(
            contamination=contamination,
            n_estimators=n_estimators,
            random_state=42,
            n_jobs=-1  # Use all CPU cores
        )

        # Scaler for normalization
        self.scaler = StandardScaler()

        # Training status
        self.is_trained = False

        # Feature names for interpretability
        self.feature_names = []

    def extract_log_features(
        self,
        log_entries: List[Dict[str, Any]]
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Extract features from log entries

        Args:
            log_entries: List of log entries

        Returns:
            Feature matrix and feature names
        """
        features = []
        feature_names = [
            "hour_of_day",
            "day_of_week",
            "log_level_error",
            "log_level_warning",
            "message_length",
            "has_exception",
            "response_time",
            "status_code"
        ]

        for entry in log_entries:
            # Temporal features
            timestamp = entry.get("timestamp", datetime.now())
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(
                    timestamp.replace('Z', '+00:00'))

            hour = timestamp.hour
            day_of_week = timestamp.weekday()

            # Log level features
            level = entry.get("level", "INFO").upper()
            is_error = 1 if level == "ERROR" else 0
            is_warning = 1 if level == "WARNING" else 0

            # Message features
            message = entry.get("message", "")
            message_length = len(message)
            has_exception = 1 if "exception" in message.lower(
            ) or "error" in message.lower() else 0

            # Performance features
            response_time = entry.get("response_time", 0)
            status_code = entry.get("status_code", 200)

            features.append([
                hour,
                day_of_week,
                is_error,
                is_warning,
                message_length,
                has_exception,
                response_time,
                status_code
            ])

        return np.array(features), feature_names

    def extract_metric_features(
        self,
        metrics: List[Dict[str, Any]]
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Extract features from system metrics

        Args:
            metrics: List of metric data points

        Returns:
            Feature matrix and feature names
        """
        features = []
        feature_names = [
            "cpu_usage",
            "memory_usage",
            "disk_usage",
            "network_in",
            "network_out",
            "request_rate",
            "error_rate",
            "response_time_p95"
        ]

        for metric in metrics:
            features.append([
                metric.get("cpu_usage", 0),
                metric.get("memory_usage", 0),
                metric.get("disk_usage", 0),
                metric.get("network_in", 0),
                metric.get("network_out", 0),
                metric.get("request_rate", 0),
                metric.get("error_rate", 0),
                metric.get("response_time_p95", 0)
            ])

        return np.array(features), feature_names

    def train(
        self,
        data: List[Dict[str, Any]],
        data_type: str = "logs"
    ) -> Dict[str, Any]:
        """
        Train anomaly detector

        Args:
            data: Training data (logs or metrics)
            data_type: Type of data ("logs" or "metrics")

        Returns:
            Training results
        """
        try:
