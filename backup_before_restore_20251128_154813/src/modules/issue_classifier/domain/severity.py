"""Severity domain models."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class SeverityLevel(str, Enum):
    """Severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class SeverityFactors:
    """Factors affecting severity."""

    # Impact factors
    affects_production: bool = False
    affects_multiple_users: bool = False
    data_loss_risk: bool = False
    security_risk: bool = False

    # Urgency factors
    blocks_critical_function: bool = False
    has_workaround: bool = True

    # Scope
    affected_users_count: int = 0
    affected_systems_count: int = 1


@dataclass
class SeverityEstimate:
    """Severity estimation result."""

    level: SeverityLevel
    score: float  # 0-100
    confidence: float  # 0.0-1.0

    factors: SeverityFactors
    reasoning: List[str] = field(default_factory=list)

    @property
    def is_urgent(self) -> bool:
        """Check if issue is urgent."""
        return self.level in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]

    @property
    def requires_immediate_action(self) -> bool:
        """Check if requires immediate action."""
        return self.level == SeverityLevel.CRITICAL and self.factors.affects_production
