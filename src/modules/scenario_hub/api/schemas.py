from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from src.modules.scenario_hub.domain.models import Scenario, ScenarioExecution, ScenarioStatus

class RegisterScenarioRequest(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    steps: List[Dict[str, Any]]
    default_parameters: Dict[str, Any] = Field(default_factory=dict)

class ExecuteScenarioRequest(BaseModel):
    scenario_id: str
    parameters: Dict[str, Any] = Field(default_factory=dict)

class ExecuteScenarioResponse(BaseModel):
    execution_id: str
    status: ScenarioStatus
    result: Optional[Any] = None

class ScenarioStatsResponse(BaseModel):
    total_scenarios: int
    total_executions: int
