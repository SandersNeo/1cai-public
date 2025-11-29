"""
Business Analyst Domain Exceptions

Custom exceptions для Business Analyst модуля.
"""
from typing import Any, Dict


class BusinessAnalystError(Exception):
    """Базовое исключение для Business Analyst модуля"""

    def __init__(self, message: str, details: Dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class RequirementExtractionError(BusinessAnalystError):
    """Ошибка при извлечении требований"""


class BPMNGenerationError(BusinessAnalystError):
    """Ошибка при генерации BPMN диаграммы"""


class GapAnalysisError(BusinessAnalystError):
    """Ошибка при gap analysis"""


class TraceabilityError(BusinessAnalystError):
    """Ошибка при генерации матрицы прослеживаемости"""


__all__ = [
    "BusinessAnalystError",
    "RequirementExtractionError",
    "BPMNGenerationError",
    "GapAnalysisError",
    "TraceabilityError",
]
