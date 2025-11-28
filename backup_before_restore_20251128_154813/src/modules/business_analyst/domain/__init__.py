"""
Business Analyst Domain Layer

Domain models и exceptions для Business Analyst модуля.
"""

from src.modules.business_analyst.domain.exceptions import (
    BPMNGenerationError,
    BusinessAnalystError,
    GapAnalysisError,
    RequirementExtractionError,
    TraceabilityError,
)
from src.modules.business_analyst.domain.models import (
    BPMNDiagram,
    CoverageSummary,
    DecisionPoint,
    Effort,
    Gap,
    GapAnalysisResult,
    Impact,
    Priority,
    Requirement,
    RequirementExtractionResult,
    RequirementType,
    RoadmapItem,
    TraceabilityItem,
    TraceabilityMatrix,
    UserStory,
)

__all__ = [
    # Models
    "RequirementType",
    "Priority",
    "Impact",
    "Effort",
    "UserStory",
    "Requirement",
    "RequirementExtractionResult",
    "DecisionPoint",
    "BPMNDiagram",
    "Gap",
    "RoadmapItem",
    "GapAnalysisResult",
    "TraceabilityItem",
    "CoverageSummary",
    "TraceabilityMatrix",
    # Exceptions
    "BusinessAnalystError",
    "RequirementExtractionError",
    "BPMNGenerationError",
    "GapAnalysisError",
    "TraceabilityError",
]
