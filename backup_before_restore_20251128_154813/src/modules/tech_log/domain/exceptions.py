"""
Tech Log Analyzer Domain Exceptions

Custom exceptions для Tech Log Analyzer модуля.
"""


class TechLogError(Exception):
    """Базовое исключение для Tech Log модуля"""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class LogParsingError(TechLogError):
    """Ошибка при парсинге логов"""


class PerformanceAnalysisError(TechLogError):
    """Ошибка при анализе производительности"""


class LogFileNotFoundError(TechLogError):
    """Файл лога не найден"""


__all__ = [
    "TechLogError",
    "LogParsingError",
    "PerformanceAnalysisError",
    "LogFileNotFoundError",
]
