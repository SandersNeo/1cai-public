"""RAS Monitor session domain models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Session:
    """1C user session."""

    session_id: str
    cluster_id: str
    user: str
    app_name: str

    # Timestamps
    started_at: datetime
    last_active: datetime

    # Resource usage
    memory_mb: float
    cpu_percent: float

    # Connection info
    host: Optional[str] = None
    connection_id: Optional[str] = None

    # Status
    is_blocked: bool = False
    blocked_by: Optional[str] = None

    @property
    def duration_minutes(self) -> float:
        """Calculate session duration in minutes."""
        delta = datetime.now() - self.started_at
        return delta.total_seconds() / 60

    @property
    def is_idle(self) -> bool:
        """Check if session is idle (>30 min no activity)."""
        delta = datetime.now() - self.last_active
        return delta.total_seconds() > 1800  # 30 minutes


@dataclass
class SessionAnalysis:
    """Analysis of sessions."""

    total_sessions: int
    active_sessions: int
    idle_sessions: int
    blocked_sessions: int

    # Resource totals
    total_memory_mb: float
    avg_memory_per_session_mb: float
    total_cpu_percent: float

    # Top consumers
    top_memory_sessions: list = field(default_factory=list)
    top_cpu_sessions: list = field(default_factory=list)

    # Recommendations
    recommendations: list = field(default_factory=list)
