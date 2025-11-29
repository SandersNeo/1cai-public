"""
Security Domain Exceptions

Custom exceptions для Security модуля.
"""
from typing import Any, Dict


class SecurityError(Exception):
    """Базовое исключение для Security модуля"""

    def __init__(self, message: str, details: Dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class VulnerabilityScanError(SecurityError):
    """Ошибка при сканировании уязвимостей"""


class DependencyAuditError(SecurityError):
    """Ошибка при аудите зависимостей"""


class SecretDetectionError(SecurityError):
    """Ошибка при детекции секретов"""


class ComplianceCheckError(SecurityError):
    """Ошибка при проверке compliance"""


__all__ = [
    "SecurityError",
    "VulnerabilityScanError",
    "DependencyAuditError",
    "SecretDetectionError",
    "ComplianceCheckError",
]
