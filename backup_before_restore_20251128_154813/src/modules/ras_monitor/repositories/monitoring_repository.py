"""
Monitoring Repository

Repository для хранения thresholds и конфигурации мониторинга.
"""

from typing import Any, Dict


class MonitoringRepository:
    """
    Repository для базы знаний monitoring

    Хранит:
    - Performance thresholds
    - Resource limits
    - Alert configurations
    """

    def __init__(self):
        """Initialize repository with default values"""
        self._thresholds = self._load_thresholds()
        self._max_values = self._load_max_values()
        self._alert_config = self._load_alert_config()

    def get_threshold(self, metric_type: str) -> float:
        """Получить threshold для метрики"""
        return self._thresholds.get(metric_type, 80.0)

    def get_max_value(self, resource_type: str) -> float:
        """Получить максимальное значение для ресурса"""
        return self._max_values.get(resource_type, 100.0)

    def get_alert_config(self, alert_type: str) -> Dict[str, Any]:
        """Получить конфигурацию алерта"""
        return self._alert_config.get(alert_type, {})

    def _load_thresholds(self) -> Dict[str, float]:
        """Load performance thresholds"""
        return {
            "cpu_percent": 80.0,
            "memory_mb": 4096.0,
            "memory_percent": 80.0,
            "connections": 100.0,
            "connections_percent": 80.0,
            "locks_percent": 80.0,
            "response_time_ms": 1000.0,
        }

    def _load_max_values(self) -> Dict[str, float]:
        """Load maximum resource values"""
        return {
            "cpu_percent": 100.0,
            "memory_mb": 8192.0,
            "connections": 200.0,
            "locks": 50.0,
        }

    def _load_alert_config(self) -> Dict[str, Dict]:
        """Load alert configurations"""
        return {
            "cpu": {
                "enabled": True,
                "threshold": 80.0,
                "critical_threshold": 90.0,
                "notification_channels": ["email", "slack"],
            },
            "memory": {
                "enabled": True,
                "threshold": 80.0,
                "critical_threshold": 90.0,
                "notification_channels": ["email", "slack"],
            },
            "connections": {
                "enabled": True,
                "threshold": 80.0,
                "critical_threshold": 95.0,
                "notification_channels": ["slack"],
            },
        }


__all__ = ["MonitoringRepository"]
