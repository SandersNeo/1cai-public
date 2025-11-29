from enum import Enum
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel, Field, validator


class TaskPriority(str, Enum):
    MUST = "MUST"
    SHOULD = "SHOULD"
    COULD = "COULD"
    WONT = "WONT"


class TaskStatus(str, Enum):
    BACKLOG = "BACKLOG"
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    REVIEW = "REVIEW"
    DONE = "DONE"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskStrategy(str, Enum):
    RESOLVE = "RESOLVE"
    OWN = "OWN"
    ACCEPT = "ACCEPT"
    MITIGATE = "MITIGATE"


class Skill(str, Enum):
    PYTHON = "PYTHON"
    SQL = "SQL"
    BSL = "BSL"
    DEVOPS = "DEVOPS"
    TESTING = "TESTING"
    ANALYSIS = "ANALYSIS"
    SECURITY = "SECURITY"
    DOCS = "DOCS"


class AgentProfile(BaseModel):
    """
    Represents an AI Agent with specific skills.
    """

    id: str
    name: str
    skills: List[Skill] = Field(default_factory=list)
    efficiency: float = Field(default=1.0, ge=0.1, le=2.0, description="Efficiency multiplier")


class Task(BaseModel):
    """
    Represents a unit of work (User Story, Task, Bug).
    Follows INVEST criteria.
    """

    id: str = Field(..., description="Unique identifier")
    title: str = Field(..., min_length=5, max_length=100)
    description: str = Field(..., description="Detailed description")
    priority: TaskPriority = Field(default=TaskPriority.SHOULD)
    status: TaskStatus = Field(default=TaskStatus.BACKLOG)
    story_points: Optional[int] = Field(None, ge=1, le=100, description="Fibonacci estimate")
    assignee_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list, description="IDs of dependent tasks")

    @validator("story_points")
    def validate_fibonacci(cls, v):
        if v is not None and v not in [1, 2, 3, 5, 8, 13, 21, 34, 55, 89]:
            raise ValueError("Story points must be a Fibonacci number")
        return v


class Sprint(BaseModel):
    """
    Represents a time-boxed iteration.
    """

    id: str
    name: str
    start_date: date
    end_date: date
    goal: str
    capacity: int = Field(..., gt=0, description="Total team capacity in Story Points")
    tasks: List[Task] = Field(default_factory=list)

    @property
    def total_points(self) -> int:
        return sum(t.story_points or 0 for t in self.tasks)

    @property
    def is_overloaded(self) -> bool:
        return self.total_points > self.capacity


class Risk(BaseModel):
    """
    Represents a project risk (PMI standard).
    """

    id: str
    description: str
    probability: int = Field(..., ge=1, le=5, description="1 (Rare) to 5 (Almost Certain)")
    impact: int = Field(..., ge=1, le=5, description="1 (Negligible) to 5 (Catastrophic)")
    strategy: RiskStrategy
    mitigation_plan: str

    @property
    def score(self) -> int:
        return self.probability * self.impact

    @property
    def level(self) -> RiskLevel:
        score = self.score
        if score >= 20:
            return RiskLevel.CRITICAL
        if score >= 12:
            return RiskLevel.HIGH
        if score >= 6:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW
