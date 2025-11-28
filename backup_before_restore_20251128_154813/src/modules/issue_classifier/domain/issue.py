"""Issue domain models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class IssueType(str, Enum):
    """Issue type classification."""

    ERROR = "error"
    WARNING = "warning"
    PERFORMANCE = "performance"
    SECURITY = "security"
    CONFIGURATION = "configuration"
    DATABASE = "database"
    NETWORK = "network"
    UNKNOWN = "unknown"


class IssueStatus(str, Enum):
    """Issue status."""

    NEW = "new"
    ANALYZING = "analyzing"
    CLASSIFIED = "classified"
    RESOLVED = "resolved"
    CLOSED = "closed"


@dataclass
class Issue:
    """Issue representation."""

    issue_id: str
    title: str
    description: str

    # Classification
    issue_type: IssueType = IssueType.UNKNOWN
    status: IssueStatus = IssueStatus.NEW

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None  # "tech_log", "user_report", etc.

    # Context
    stack_trace: Optional[str] = None
    error_code: Optional[str] = None
    affected_users: int = 0

    def __post_init__(self):
        """Validate issue."""
        if not self.title.strip():
            raise ValueError("Title cannot be empty")
        if not self.description.strip():
            raise ValueError("Description cannot be empty")


@dataclass
class IssueClassification:
    """Issue classification result."""

    issue: Issue
    classified_type: IssueType
    confidence: float  # 0.0 to 1.0

    # Extracted information
    keywords: List[str] = field(default_factory=list)
    entities: Dict[str, str] = field(default_factory=dict)

    # Classification reasoning
    reasoning: List[str] = field(default_factory=list)

    @property
    def is_confident(self) -> bool:
        """Check if classification is confident."""
        return self.confidence >= 0.7
