"""Connection pool domain models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class ConnectionPool:
    """Database connection pool configuration."""

    pool_name: str
    min_connections: int
    max_connections: int

    # Timeout settings
    connection_timeout_sec: int = 30
    idle_timeout_sec: int = 300
    max_lifetime_sec: int = 1800

    # Current state
    active_connections: int = 0
    idle_connections: int = 0

    def __post_init__(self):
        """Validate pool settings."""
        if self.min_connections < 0:
            raise ValueError("Min connections cannot be negative")
        if self.max_connections < self.min_connections:
            raise ValueError("Max connections must be >= min connections")

    @property
    def total_connections(self) -> int:
        """Get total connections."""
        return self.active_connections + self.idle_connections

    @property
    def usage_percent(self) -> float:
        """Calculate pool usage percentage."""
        if self.max_connections == 0:
            return 0.0
        return (self.total_connections / self.max_connections) * 100


@dataclass
class PoolMetrics:
    """Connection pool metrics."""

    pool_name: str
    timestamp: datetime

    # Usage metrics
    avg_active: float
    peak_active: int
    avg_wait_time_ms: float

    # Error metrics
    timeout_count: int
    error_count: int


@dataclass
class PoolOptimization:
    """Connection pool optimization."""

    current_pool: ConnectionPool
    recommended_min: int
    recommended_max: int

    expected_improvement: str
    reasoning: List[str] = field(default_factory=list)

    @property
    def size_change(self) -> int:
        """Calculate size change."""
        return self.recommended_max - self.current_pool.max_connections
