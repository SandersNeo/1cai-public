"""
Technical Writer Domain Layer

Domain models и exceptions для Technical Writer модуля.
"""

from src.modules.technical_writer.domain.exceptions import (
    APIDocGenerationError,
    CodeDocGenerationError,
    ReleaseNotesGenerationError,
    TechnicalWriterError,
    UserGuideGenerationError,
)
from src.modules.technical_writer.domain.models import (
    APIDocumentation,
    APIEndpoint,
    APIExample,
    APIParameter,
    Audience,
    DocumentationType,
    FAQItem,
    FunctionDocumentation,
    GuideSection,
    HTTPMethod,
    Parameter,
    ReleaseNotes,
    UserGuide,
)

__all__ = [
    # Models
    "HTTPMethod",
    "Audience",
    "DocumentationType",
    "APIParameter",
    "APIEndpoint",
    "APIExample",
    "APIDocumentation",
    "GuideSection",
    "FAQItem",
    "UserGuide",
    "ReleaseNotes",
    "Parameter",
    "FunctionDocumentation",
    # Exceptions
    "TechnicalWriterError",
    "APIDocGenerationError",
    "UserGuideGenerationError",
    "ReleaseNotesGenerationError",
    "CodeDocGenerationError",
]
