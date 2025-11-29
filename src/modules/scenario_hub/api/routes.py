from fastapi import APIRouter, HTTPException, Depends
from src.modules.scenario_hub.api.schemas import (
    RegisterScenarioRequest, ExecuteScenarioRequest, ExecuteScenarioResponse, ScenarioStatsResponse
)
from src.modules.scenario_hub.services import ScenarioEngine
from src.modules.scenario_hub.domain.models import Scenario, ScenarioStep
from src.modules.scenario_hub.domain.exceptions import ScenarioNotFound, ExecutionError

router = APIRouter(prefix="/scenario_hub", tags=["Scenario Hub"])

# Dependency Injection (Singleton for now)
_engine = ScenarioEngine()
def get_scenario_engine(): return _engine

@router.post("/register", response_model=Scenario)
async def register_scenario(
    request: RegisterScenarioRequest,
    engine: ScenarioEngine = Depends(get_scenario_engine)
):
    """Registers a new automation scenario."""
    try:
        # Convert dict steps to ScenarioStep objects
        steps = [ScenarioStep(**s) for s in request.steps]
        scenario = Scenario(
            id=request.id,
            name=request.name,
            description=request.description,
            steps=steps,
            default_parameters=request.default_parameters
        )
        return engine.register_scenario(scenario)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute", response_model=ExecuteScenarioResponse)
async def execute_scenario(
    request: ExecuteScenarioRequest,
    engine: ScenarioEngine = Depends(get_scenario_engine)
):
    """Executes a registered scenario."""
    try:
        execution = await engine.execute_scenario(request.scenario_id, request.parameters)
        return ExecuteScenarioResponse(
            execution_id=execution.id,
            status=execution.status,
            result=execution.result
        )
    except ScenarioNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ExecutionError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=ScenarioStatsResponse)
async def get_stats(engine: ScenarioEngine = Depends(get_scenario_engine)):
    """Returns statistics about scenario execution."""
    return ScenarioStatsResponse(
        total_scenarios=len(engine.scenarios),
        total_executions=len(engine.executions)
    )
