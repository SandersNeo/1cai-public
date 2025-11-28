"""
Architect Domain Layer

Domain models и exceptions для Architect модуля.
"""

from src.modules.architect.domain.exceptions import (
    ADRGenerationError,
    AntiPatternDetectionError,
    ArchitectError,
    ArchitectureAnalysisError,
)
from src.modules.architect.domain.models import (
    ADR,
    ADRStatus,
    Alternative,
    AntiPattern,
    AntiPatternType,
    ArchitectureAnalysisResult,
    ArchitectureMetrics,
    Consequences,
    Effort,
    HealthStatus,
    Severity,
)

__all__ = [
    # Models
    "AntiPatternType",
    "Severity",
    "Effort",
    "HealthStatus",
    "ADRStatus",
    "ArchitectureMetrics",
    "AntiPattern",
    "ArchitectureAnalysisResult",
    "Alternative",
    "Consequences",
    "ADR",
    # Exceptions
    "ArchitectError",
    "ArchitectureAnalysisError",
    "ADRGenerationError",
    "AntiPatternDetectionError",
]
