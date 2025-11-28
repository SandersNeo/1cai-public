"""
RAS Monitor Domain Exceptions

Custom exceptions для RAS Monitor модуля.
"""


class RASMonitorError(Exception):
    """Базовое исключение для RAS Monitor модуля"""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ClusterConnectionError(RASMonitorError):
    """Ошибка подключения к кластеру"""


class SessionAnalysisError(RASMonitorError):
    """Ошибка при анализе сессий"""


class ResourceMonitoringError(RASMonitorError):
    """Ошибка при мониторинге ресурсов"""


__all__ = [
    "RASMonitorError",
    "ClusterConnectionError",
    "SessionAnalysisError",
    "ResourceMonitoringError",
]
