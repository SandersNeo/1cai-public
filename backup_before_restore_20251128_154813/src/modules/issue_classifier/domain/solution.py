"""Solution domain models."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class SolutionType(str, Enum):
    """Solution type."""

    FIX = "fix"
    WORKAROUND = "workaround"
    CONFIGURATION = "configuration"
    UPGRADE = "upgrade"
    DOCUMENTATION = "documentation"


@dataclass
class Solution:
    """Solution representation."""

    solution_id: str
    title: str
    description: str
    solution_type: SolutionType

    # Implementation
    steps: List[str] = field(default_factory=list)
    estimated_time_minutes: int = 30

    # Metadata
    success_rate: float = 0.0  # 0.0-1.0
    times_applied: int = 0

    # Requirements
    requires_restart: bool = False
    requires_downtime: bool = False

    @property
    def is_quick_fix(self) -> bool:
        """Check if solution is quick."""
        return self.estimated_time_minutes <= 15 and not self.requires_downtime


@dataclass
class SolutionRecommendation:
    """Solution recommendation for an issue."""

    issue_id: str
    solutions: List[Solution] = field(default_factory=list)

    # Recommendation metadata
    confidence: float = 0.0  # 0.0-1.0
    reasoning: List[str] = field(default_factory=list)

    # Similar issues
    similar_issues_count: int = 0

    @property
    def has_quick_fix(self) -> bool:
        """Check if has quick fix available."""
        return any(s.is_quick_fix for s in self.solutions)

    @property
    def best_solution(self) -> Optional[Solution]:
        """Get best solution by success rate."""
        if not self.solutions:
            return None
        return max(self.solutions, key=lambda s: s.success_rate)
