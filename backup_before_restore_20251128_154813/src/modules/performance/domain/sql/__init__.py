"""SQL Optimizer domain package."""

from .index import Index, IndexRecommendation
from .optimization import OptimizationResult, PerformancePrediction
from .query import QueryAnalysis, QueryType, SQLQuery

__all__ = [
    "SQLQuery",
    "QueryAnalysis",
    "QueryType",
    "Index",
    "IndexRecommendation",
    "OptimizationResult",
    "PerformancePrediction",
]
