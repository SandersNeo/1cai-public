"""RAS Monitor cluster domain models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ClusterInfo:
    """1C cluster information."""

    cluster_id: str
    host: str
    port: int
    version: str
    status: str  # "active", "inactive", "error"

    # Optional info
    name: Optional[str] = None
    description: Optional[str] = None

    # Timestamps
    started_at: Optional[datetime] = None
    last_check: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate cluster info."""
        if self.port < 1 or self.port > 65535:
            raise ValueError("Invalid port number")
        if self.status not in ["active", "inactive", "error"]:
            raise ValueError(f"Invalid status: {self.status}")

    @property
    def is_active(self) -> bool:
        """Check if cluster is active."""
        return self.status == "active"


@dataclass
class ClusterMetrics:
    """Cluster performance metrics."""

    cluster_id: str
    timestamp: datetime

    # Resource metrics
    total_memory_mb: float
    used_memory_mb: float
    cpu_percent: float

    # Session metrics
    active_sessions: int
    total_sessions: int
    blocked_sessions: int

    # Connection metrics
    active_connections: int
    max_connections: int

    @property
    def memory_usage_percent(self) -> float:
        """Calculate memory usage percentage."""
        if self.total_memory_mb == 0:
            return 0.0
        return (self.used_memory_mb / self.total_memory_mb) * 100

    @property
    def connection_usage_percent(self) -> float:
        """Calculate connection pool usage."""
        if self.max_connections == 0:
            return 0.0
        return (self.active_connections / self.max_connections) * 100

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "cluster_id": self.cluster_id,
            "timestamp": self.timestamp.isoformat(),
            "memory_usage_percent": self.memory_usage_percent,
            "cpu_percent": self.cpu_percent,
            "active_sessions": self.active_sessions,
            "total_sessions": self.total_sessions,
            "blocked_sessions": self.blocked_sessions,
            "connection_usage_percent": self.connection_usage_percent,
        }
