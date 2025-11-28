"""SQL Optimizer optimization domain models."""

from dataclasses import dataclass, field
from typing import List

from .query import SQLQuery


@dataclass
class OptimizationResult:
    """Result of query optimization."""

    original_query: SQLQuery
    optimized_query: str

    # Improvement metrics
    expected_improvement_percent: float
    estimated_time_ms: int

    # Changes made
    changes: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    # Validation
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)

    @property
    def time_saved_ms(self) -> int:
        """Calculate expected time savings."""
        return int(
            self.original_query.execution_time_ms
            * (self.expected_improvement_percent / 100)
        )


@dataclass
class PerformancePrediction:
    """Prediction of query performance."""

    query_text: str

    # Predictions
    estimated_time_ms: int
    estimated_rows: int
    estimated_cost: float

    # Confidence
    confidence: float  # 0.0 to 1.0

    # Factors
    factors: List[str] = field(default_factory=list)

    @property
    def is_likely_slow(self) -> bool:
        """Check if query is likely to be slow."""
        return self.estimated_time_ms > 1000 and self.confidence > 0.7
