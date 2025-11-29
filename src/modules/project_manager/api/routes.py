from fastapi import APIRouter, HTTPException, Depends
from src.modules.project_manager.api.schemas import (
    DecomposeTaskRequest,
    DecomposeTaskResponse,
    EstimateTaskRequest,
    EstimateTaskResponse,
    PlanSprintRequest,
    PlanSprintResponse,
    AnalyzeRiskRequest,
    AnalyzeRiskResponse,
    AnalyzeRisksRequest,
    AnalyzeRisksResponse,
    CheckCapacityRequest,
    CheckCapacityResponse,
)
from src.modules.project_manager.services import (
    TaskDecomposer,
    EffortEstimator,
    SprintPlanner,
    RiskAnalyzer,
    ResourceAllocator,
)
from src.modules.project_manager.domain.models import Task, TaskStatus
from src.modules.project_manager.domain.exceptions import ProjectManagerError

router = APIRouter(prefix="/project_manager", tags=["Project Manager Agent"])


# Dependency Injection (Simple instantiation for now)
def get_task_decomposer():
    return TaskDecomposer()


def get_effort_estimator():
    return EffortEstimator()


def get_resource_allocator():
    return ResourceAllocator()


def get_sprint_planner(allocator=Depends(get_resource_allocator)):
    return SprintPlanner(resource_allocator=allocator)


def get_risk_analyzer():
    return RiskAnalyzer()


@router.post("/decompose", response_model=DecomposeTaskResponse)
async def decompose_task(request: DecomposeTaskRequest, decomposer: TaskDecomposer = Depends(get_task_decomposer)):
    """
    Decomposes a high-level task into subtasks using INVEST criteria.
    """
    try:
        # Create a temporary Task object from request
        parent_task = Task(
            id="temp-parent",
            title=request.title,
            description=request.description,
            priority=request.priority,
            status=TaskStatus.BACKLOG,
        )
        subtasks = decomposer.decompose(parent_task)
        return DecomposeTaskResponse(original_task=parent_task, subtasks=subtasks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/estimate", response_model=EstimateTaskResponse)
async def estimate_task(request: EstimateTaskRequest, estimator: EffortEstimator = Depends(get_effort_estimator)):
    """
    Estimates effort for a task using Planning Poker logic (Fibonacci).
    """
    try:
        points = estimator.estimate(request.task)
        return EstimateTaskResponse(task_id=request.task.id, story_points=points)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plan_sprint", response_model=PlanSprintResponse)
async def plan_sprint(request: PlanSprintRequest, planner: SprintPlanner = Depends(get_sprint_planner)):
    """
    Plans a sprint based on team capacity and backlog priority.
    """
    try:
        sprint = planner.plan_sprint(
            sprint_name=request.sprint_name,
            start_date=request.start_date,
            duration_weeks=request.duration_weeks,
            capacity=request.capacity,
            backlog=request.backlog,
        )
        return PlanSprintResponse(sprint=sprint)
    except ProjectManagerError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze_risk", response_model=AnalyzeRiskResponse)
async def analyze_risk(request: AnalyzeRiskRequest, analyzer: RiskAnalyzer = Depends(get_risk_analyzer)):
    """
    Analyzes a project risk using ROAM model.
    """
    try:
        risk = analyzer.analyze_risk(request.description, request.probability, request.impact)
        return AnalyzeRiskResponse(risk=risk)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze_risks", response_model=AnalyzeRisksResponse)
async def analyze_risks(request: AnalyzeRisksRequest, analyzer: RiskAnalyzer = Depends(get_risk_analyzer)):
    """
    Analyzes multiple project risks in bulk.
    """
    try:
        risks_data = [r.dict() for r in request.risks]
        risks = analyzer.analyze_bulk(risks_data)
        return AnalyzeRisksResponse(risks=risks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check_capacity", response_model=CheckCapacityResponse)
async def check_capacity(request: CheckCapacityRequest, allocator: ResourceAllocator = Depends(get_resource_allocator)):
    """
    Calculates required capacity per skill for a list of tasks.
    """
    try:
        capacity = allocator.check_capacity(request.tasks)
        return CheckCapacityResponse(required_capacity=capacity)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
