from typing import List, Optional
from datetime import date
from pydantic import BaseModel, Field
from src.modules.project_manager.domain.models import (
    TaskPriority,
    TaskStatus,
    Task,
    Sprint,
    Risk,
    RiskLevel,
    RiskStrategy,
)


class DecomposeTaskRequest(BaseModel):
    title: str
    description: str
    priority: TaskPriority = TaskPriority.SHOULD


class DecomposeTaskResponse(BaseModel):
    original_task: Task
    subtasks: List[Task]


class EstimateTaskRequest(BaseModel):
    task: Task


class EstimateTaskResponse(BaseModel):
    task_id: str
    story_points: int
    confidence: float = 0.8  # Placeholder for confidence score


class PlanSprintRequest(BaseModel):
    sprint_name: str
    start_date: date
    duration_weeks: int = 2
    capacity: int
    backlog: List[Task]


class PlanSprintResponse(BaseModel):
    sprint: Sprint


class AnalyzeRiskRequest(BaseModel):
    description: str
    probability: int = Field(..., ge=1, le=5)
    impact: int = Field(..., ge=1, le=5)


class AnalyzeRiskResponse(BaseModel):
    risk: Risk


class AnalyzeRisksRequest(BaseModel):
    risks: List[AnalyzeRiskRequest]


class AnalyzeRisksResponse(BaseModel):
    risks: List[Risk]


class CheckCapacityRequest(BaseModel):
    tasks: List[Task]


class CheckCapacityResponse(BaseModel):
    required_capacity: dict  # Skill -> Points
