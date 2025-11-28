"""
Tech Log Analyzer Domain Layer

Domain models и exceptions для Tech Log Analyzer модуля.
"""

from src.modules.tech_log.domain.exceptions import (
    LogFileNotFoundError,
    LogParsingError,
    PerformanceAnalysisError,
    TechLogError,
)
from src.modules.tech_log.domain.models import (
    EventType,
    IssueType,
    LogAnalysisResult,
    PerformanceAnalysisResult,
    PerformanceIssue,
    Severity,
    TechLogEvent,
)

__all__ = [
    # Models
    "Severity",
    "EventType",
    "IssueType",
    "TechLogEvent",
    "PerformanceIssue",
    "LogAnalysisResult",
    "PerformanceAnalysisResult",
    # Exceptions
    "TechLogError",
    "LogParsingError",
    "PerformanceAnalysisError",
    "LogFileNotFoundError",
]
