"""SQL Optimizer index domain models."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Index:
    """Database index."""

    index_name: str
    table_name: str
    columns: List[str]

    # Index properties
    is_unique: bool = False
    is_clustered: bool = False

    # Statistics
    size_mb: Optional[float] = None
    row_count: Optional[int] = None

    def __post_init__(self):
        """Validate index."""
        if not self.columns:
            raise ValueError("Index must have at least one column")


@dataclass
class IndexRecommendation:
    """Recommendation to create or modify index."""

    table_name: str
    recommended_columns: List[str]
    reason: str

    # Impact estimation
    expected_improvement_percent: float
    estimated_size_mb: float

    # Priority
    priority: str = "medium"  # "high", "medium", "low"

    # SQL to create index
    create_sql: Optional[str] = None

    def __post_init__(self):
        """Generate CREATE INDEX SQL."""
        if not self.create_sql:
            cols = ", ".join(self.recommended_columns)
            idx_name = f"idx_{self.table_name}_{'_'.join(self.recommended_columns)}"
            self.create_sql = f"CREATE INDEX {idx_name} ON {self.table_name} ({cols})"
