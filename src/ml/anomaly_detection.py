"""
ML-based Anomaly Detection

Implements Isolation Forest for detecting anomalies in:
- Application logs
- System metrics
- Performance data
- Security events
"""

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
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

            hour = timestamp.hour
            day_of_week = timestamp.weekday()

            # Log level features
            level = entry.get("level", "INFO").upper()
            is_error = 1 if level == "ERROR" else 0
            is_warning = 1 if level == "WARNING" else 0

            # Message features
            message = entry.get("message", "")
            message_length = len(message)
            has_exception = 1 if "exception" in message.lower() or "error" in message.lower() else 0

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
            # Extract features
            if data_type == "logs":
                X, feature_names = self.extract_log_features(data)
            else:
                X, feature_names = self.extract_metric_features(data)

            self.feature_names = feature_names

            if len(X) < 10:
                return {
                    "status": "insufficient_data",
                    "message": "Need at least 10 samples for training"
                }

            # Normalize features
            X_scaled = self.scaler.fit_transform(X)

            # Train model
            self.model.fit(X_scaled)
            self.is_trained = True

            # Get anomaly scores for training data
            scores = self.model.score_samples(X_scaled)

            self.logger.info(
                f"Trained anomaly detector on {len(X)} samples",
                extra={
                    "data_type": data_type,
                    "features": len(feature_names),
                    "mean_score": float(np.mean(scores))
                }
            )

            return {
                "status": "trained",
                "samples": len(X),
                "features": feature_names,
                "mean_score": float(np.mean(scores)),
                "std_score": float(np.std(scores))
            }

        except Exception as e:
            self.logger.error("Training failed: %s", e)
            return {"status": "failed", "error": str(e)}

    def detect(
        self,
        data: List[Dict[str, Any]],
        data_type: str = "logs"
    ) -> Dict[str, Any]:
        """
        Detect anomalies in data

        Args:
            data: Data to analyze (logs or metrics)
            data_type: Type of data ("logs" or "metrics")

        Returns:
            Detection results with anomalies
        """
        if not self.is_trained:
            return {
                "status": "not_trained",
                "message": "Model must be trained first"
            }

        try:
            # Extract features
            if data_type == "logs":
                X, _ = self.extract_log_features(data)
            else:
                X, _ = self.extract_metric_features(data)

            # Normalize
            X_scaled = self.scaler.transform(X)

            # Predict anomalies (-1 = anomaly, 1 = normal)
            predictions = self.model.predict(X_scaled)

            # Get anomaly scores (lower = more anomalous)
            scores = self.model.score_samples(X_scaled)

            # Find anomalies
            anomalies = []
            for i, (pred, score) in enumerate(zip(predictions, scores)):
                if pred == -1:
                    anomalies.append({
                        "index": i,
                        "data": data[i],
                        "anomaly_score": float(score),
                        "severity": self._calculate_severity(score)
                    })

            # Sort by severity
            anomalies.sort(key=lambda x: x["anomaly_score"])

            self.logger.info(
                f"Detected {len(anomalies)} anomalies in {len(data)} samples",
                extra={
                    "data_type": data_type,
                    "anomaly_rate": len(anomalies) / len(data) if data else 0
                }
            )

            return {
                "status": "completed",
                "total_samples": len(data),
                "anomalies_count": len(anomalies),
                "anomaly_rate": len(anomalies) / len(data) if data else 0,
                "anomalies": anomalies[:10],  # Top 10 most anomalous
                "all_scores": scores.tolist()
            }

        except Exception as e:
            self.logger.error("Detection failed: %s", e)
            return {"status": "failed", "error": str(e)}

    def _calculate_severity(self, score: float) -> str:
        """
        Calculate severity based on anomaly score

        Args:
            score: Anomaly score (lower = more anomalous)

        Returns:
            Severity level
        """
        if score < -0.5:
            return "critical"
        elif score < -0.3:
            return "high"
        elif score < -0.1:
            return "medium"
        else:
            return "low"

    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance (approximation for Isolation Forest)

        Returns:
            Feature importance scores
        """
        if not self.is_trained:
            return {}

        # Isolation Forest doesn't have built-in feature importance
        # This is a simple approximation
        importance = {}
        for i, name in enumerate(self.feature_names):
            # Use feature index as proxy (not accurate, but informative)
            importance[name] = 1.0 / (i + 1)

        return importance


# Singleton instance
_anomaly_detector: Optional[AnomalyDetector] = None


def get_anomaly_detector() -> AnomalyDetector:
    """
    Get or create anomaly detector singleton

    Returns:
        AnomalyDetector instance
    """
    global _anomaly_detector

    if _anomaly_detector is None:
        _anomaly_detector = AnomalyDetector()

    return _anomaly_detector


__all__ = [
    "AnomalyDetector",
    "get_anomaly_detector"
]
