"""
QA Engineer Domain Exceptions

Custom exceptions для QA Engineer модуля.
"""


class QAError(Exception):
    """Базовое исключение для QA модуля"""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class TestGenerationError(QAError):
    """Ошибка при генерации тестов"""


class CoverageAnalysisError(QAError):
    """Ошибка при анализе покрытия"""


__all__ = [
    "QAError",
    "TestGenerationError",
    "CoverageAnalysisError",
]
