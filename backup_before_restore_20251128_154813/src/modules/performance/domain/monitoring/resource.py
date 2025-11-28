"""RAS Monitor resource and alert domain models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertStatus(str, Enum):
    """Alert status."""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


@dataclass
class ResourceUsage:
    """Resource usage snapshot."""

    cluster_id: str
    timestamp: datetime

    # Memory
    memory_total_mb: float
    memory_used_mb: float
    memory_available_mb: float

    # CPU
    cpu_count: int
    cpu_percent: float

    # Disk
    disk_total_gb: Optional[float] = None
    disk_used_gb: Optional[float] = None

    @property
    def memory_percent(self) -> float:
        """Calculate memory usage percentage."""
        if self.memory_total_mb == 0:
            return 0.0
        return (self.memory_used_mb / self.memory_total_mb) * 100


@dataclass
class Alert:
    """Performance alert."""

    alert_id: str
    cluster_id: str
    severity: AlertSeverity
    status: AlertStatus

    # Alert details
    title: str
    description: str
    metric_name: str
    metric_value: float
    threshold: float

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    # Actions
    acknowledged_by: Optional[str] = None
    resolution_note: Optional[str] = None

    def acknowledge(self, user: str):
        """Acknowledge alert."""
        self.status = AlertStatus.ACKNOWLEDGED
        self.acknowledged_at = datetime.now()
        self.acknowledged_by = user

    def resolve(self, note: str):
        """Resolve alert."""
        self.status = AlertStatus.RESOLVED
        self.resolved_at = datetime.now()
        self.resolution_note = note
