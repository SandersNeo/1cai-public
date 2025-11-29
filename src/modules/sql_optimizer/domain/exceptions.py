"""
SQL Optimizer Domain Exceptions

Custom exceptions для SQL Optimizer модуля.
"""
from typing import Any, Dict


class SQLOptimizerError(Exception):
    """Базовое исключение для SQL Optimizer модуля"""

    def __init__(self, message: str, details: Dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class QueryAnalysisError(SQLOptimizerError):
    """Ошибка при анализе запроса"""


class QueryOptimizationError(SQLOptimizerError):
    """Ошибка при оптимизации запроса"""


class InvalidQueryError(SQLOptimizerError):
    """Невалидный SQL запрос"""


__all__ = [
    "SQLOptimizerError",
    "QueryAnalysisError",
    "QueryOptimizationError",
    "InvalidQueryError",
]
