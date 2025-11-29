from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ScenarioStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ScenarioStep(BaseModel):
    """A single step in a scenario."""

    id: str = Field(..., description="Unique identifier for the step")
    action: str = Field(..., description="Action to perform (e.g., 'deploy', 'test')")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the action")
    condition: Optional[str] = Field(None, description="Condition to evaluate before executing")
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class Scenario(BaseModel):
    """Definition of an automation scenario."""

    id: str = Field(..., description="Unique identifier for the scenario")
    name: str = Field(..., description="Human-readable name")
    description: Optional[str] = None
    steps: List[ScenarioStep] = Field(default_factory=list)
    default_parameters: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)


class StepExecution(BaseModel):
    """Record of a step execution."""

    step_id: str
    status: StepStatus = StepStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    logs: List[str] = Field(default_factory=list)


class ScenarioExecution(BaseModel):
    """Record of a full scenario execution."""

    id: str = Field(..., description="Unique execution ID")
    scenario_id: str
    status: ScenarioStatus = ScenarioStatus.CREATED
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    step_executions: List[StepExecution] = Field(default_factory=list)
    result: Optional[Any] = None
    error: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
