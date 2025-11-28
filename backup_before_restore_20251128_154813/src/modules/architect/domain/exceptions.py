"""
Architect Domain Exceptions

Custom exceptions для Architect модуля.
"""


class ArchitectError(Exception):
    """Базовое исключение для Architect модуля"""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ArchitectureAnalysisError(ArchitectError):
    """Ошибка при анализе архитектуры"""


class ADRGenerationError(ArchitectError):
    """Ошибка при генерации ADR"""


class AntiPatternDetectionError(ArchitectError):
    """Ошибка при детекции anti-patterns"""


__all__ = [
    "ArchitectError",
    "ArchitectureAnalysisError",
    "ADRGenerationError",
    "AntiPatternDetectionError",
]
