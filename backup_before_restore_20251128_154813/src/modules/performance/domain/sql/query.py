"""SQL Optimizer query domain models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class QueryType(str, Enum):
    """SQL query types."""

    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    OTHER = "OTHER"


@dataclass
class SQLQuery:
    """SQL query representation."""

    query_id: str
    text: str
    query_type: QueryType

    # Execution metrics
    execution_time_ms: int
    rows_affected: int

    # Optional details
    execution_plan: Optional[str] = None
    database: Optional[str] = None
    table_name: Optional[str] = None

    # Timestamps
    executed_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate query."""
        if not self.text.strip():
            raise ValueError("Query text cannot be empty")
        if self.execution_time_ms < 0:
            raise ValueError("Execution time cannot be negative")

    @property
    def is_slow(self) -> bool:
        """Check if query is slow (>1000ms)."""
        return self.execution_time_ms > 1000

    @property
    def normalized_text(self) -> str:
        """Get normalized query text (lowercase, trimmed)."""
        return " ".join(self.text.split()).lower()


@dataclass
class QueryAnalysis:
    """Analysis of SQL query."""

    query: SQLQuery

    # Analysis results
    has_index: bool
    uses_full_scan: bool
    estimated_cost: float

    # Issues found
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Suggestions
    suggestions: List[str] = field(default_factory=list)

    @property
    def severity(self) -> str:
        """Get severity level."""
        if self.issues:
            return "high"
        elif self.warnings:
            return "medium"
        return "low"
