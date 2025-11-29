"""
Technical Writer Domain Exceptions

Custom exceptions для Technical Writer модуля.
"""
from typing import Any, Dict


class TechnicalWriterError(Exception):
    """Базовое исключение для Technical Writer модуля"""

    def __init__(self, message: str, details: Dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class APIDocGenerationError(TechnicalWriterError):
    """Ошибка при генерации API документации"""


class UserGuideGenerationError(TechnicalWriterError):
    """Ошибка при генерации user guide"""


class ReleaseNotesGenerationError(TechnicalWriterError):
    """Ошибка при генерации release notes"""


class CodeDocGenerationError(TechnicalWriterError):
    """Ошибка при генерации code documentation"""


__all__ = [
    "TechnicalWriterError",
    "APIDocGenerationError",
    "UserGuideGenerationError",
    "ReleaseNotesGenerationError",
    "CodeDocGenerationError",
]
