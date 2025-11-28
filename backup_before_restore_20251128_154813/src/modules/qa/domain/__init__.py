"""
QA Engineer Domain Layer

Domain models и exceptions для QA Engineer модуля.
"""

from src.modules.qa.domain.exceptions import (
    CoverageAnalysisError,
    QAError,
    TestGenerationError,
)
from src.modules.qa.domain.models import (
    CoverageGrade,
    CoverageReport,
    TestCase,
    TestFramework,
    TestGenerationResult,
    TestParameter,
    TestTemplate,
    TestType,
)

__all__ = [
    # Models
    "TestType",
    "TestFramework",
    "CoverageGrade",
    "TestParameter",
    "TestCase",
    "TestGenerationResult",
    "CoverageReport",
    "TestTemplate",
    # Exceptions
    "QAError",
    "TestGenerationError",
    "CoverageAnalysisError",
]
