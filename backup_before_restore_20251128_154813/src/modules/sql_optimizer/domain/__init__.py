"""
SQL Optimizer Domain Layer

Domain models и exceptions для SQL Optimizer модуля.
"""

from src.modules.sql_optimizer.domain.exceptions import (
    InvalidQueryError,
    QueryAnalysisError,
    QueryOptimizationError,
    SQLOptimizerError,
)
from src.modules.sql_optimizer.domain.models import (
    IndexRecommendation,
    IndexType,
    OptimizationImpact,
    OptimizationResult,
    OptimizedQuery,
    PerformancePrediction,
    QueryAnalysis,
    QueryComplexity,
    SQLQuery,
)

__all__ = [
    # Models
    "QueryComplexity",
    "OptimizationImpact",
    "IndexType",
    "SQLQuery",
    "QueryAnalysis",
    "IndexRecommendation",
    "OptimizedQuery",
    "PerformancePrediction",
    "OptimizationResult",
    # Exceptions
    "SQLOptimizerError",
    "QueryAnalysisError",
    "QueryOptimizationError",
    "InvalidQueryError",
]
