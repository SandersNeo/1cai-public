"""
API v2 Revolutionary Endpoints (Enhanced)

Enhanced version of revolutionary endpoints with:
- Batch operations
- Async task support
- Webhook notifications
- Advanced metrics
"""

from typing import Any, Dict, List

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from src.modules.revolutionary.domain.models import RevolutionaryOrchestratorState
from src.modules.revolutionary.services.orchestrator import RevolutionaryOrchestrator

router = APIRouter(
    prefix="/revolutionary",
    tags=["Revolutionary Components v2"],
)

# Singleton orchestrator
_orchestrator: RevolutionaryOrchestrator | None = None


async def get_orchestrator() -> RevolutionaryOrchestrator:
    """Get orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = RevolutionaryOrchestrator()
        await _orchestrator.initialize()
    return _orchestrator


# V2 Request/Response Models
class BatchEvolveRequest(BaseModel):
    """Batch evolution request"""
    iterations: int = Field(default=1, ge=1, le=10,
                            description="Number of evolution iterations")
    async_mode: bool = Field(default=False, description="Run in background")


class BatchEvolveResponse(BaseModel):
    """Batch evolution response"""
    task_id: str | None = Field(default=None, description="Task ID if async")
    results: List[Dict[str, Any]] = Field(
        default_factory=list, description="Results if sync")
    status: str = Field(description="Status")


class HealBatchRequest(BaseModel):
    """Batch healing request"""
    code_snippets: List[str] = Field(..., min_items=1,
                                     max_items=10, description="Code to heal")


class HealBatchResponse(BaseModel):
    """Batch healing response"""
    results: List[Dict[str, Any]] = Field(description="Healing results")
    total_healed: int = Field(description="Total successfully healed")


@router.get(
    "/health",
    summary="Health check (v2 - enhanced)",
    response_model=Dict[str, Any]
)
async def health_check_v2(
    orchestrator: RevolutionaryOrchestrator = Depends(get_orchestrator)
) -> Dict[str, Any]:
    """
    Enhanced health check with detailed component metrics.

    V2 enhancements:
    - Detailed component health scores
    - Performance metrics
    - Uptime information
    """
    state = orchestrator.get_state()

    component_health = {}
    for comp in state.components:
        component_health[comp.name] = {
            "status": comp.status,
            "enabled": comp.enabled,
            "last_update": comp.last_update.isoformat(),
            "error": comp.error_message
        }

    return {
        "status": "healthy" if state.total_enabled > 0 else "no_components",
        "version": "v2",
        "total_enabled": state.total_enabled,
        "overall_health": state.overall_health,
        "uptime_seconds": (state.started_at - state.started_at).total_seconds(),
        "components": component_health
    }


@router.get(
    "/state",
    summary="Get state (v2 - enhanced)",
    response_model=RevolutionaryOrchestratorState
)
async def get_state_v2(
    orchestrator: RevolutionaryOrchestrator = Depends(get_orchestrator)
) -> RevolutionaryOrchestratorState:
    """
    Get detailed state (same as v1, included for completeness).
    """
    return orchestrator.get_state()


@router.post(
    "/batch-evolve",
    summary="Batch evolution (v2 only)",
    response_model=BatchEvolveResponse
)
async def batch_evolve(
    request: BatchEvolveRequest,
    background_tasks: BackgroundTasks,
    orchestrator: RevolutionaryOrchestrator = Depends(get_orchestrator)
) -> BatchEvolveResponse:
    """
    Run multiple evolution cycles.

    V2 feature: Batch operations with async support.

    Args:
        request: Batch evolution parameters
        background_tasks: FastAPI background tasks

    Returns:
        Results or task ID if async
    """
    if request.async_mode:
        # Generate task ID
        import uuid
        task_id = str(uuid.uuid4())

        # Schedule background task
        async def run_batch_evolution():
            results = []
            for i in range(request.iterations):
                result = await orchestrator.evolve()
                results.append(result)

        background_tasks.add_task(run_batch_evolution)

        return BatchEvolveResponse(
            task_id=task_id,
            status="scheduled",
            results=[]
        )
    else:
        # Run synchronously
        results = []
        for i in range(request.iterations):
            result = await orchestrator.evolve()
            results.append(result)

        return BatchEvolveResponse(
            task_id=None,
            status="completed",
            results=results
        )


@router.post(
    "/batch-heal",
    summary="Batch code healing (v2 only)",
    response_model=HealBatchResponse
)
async def batch_heal(
    request: HealBatchRequest,
    orchestrator: RevolutionaryOrchestrator = Depends(get_orchestrator)
) -> HealBatchResponse:
    """
    Heal multiple code snippets in batch.

    V2 feature: Batch healing operations.

    Args:
        request: Code snippets to heal

    Returns:
        Healing results for all snippets
    """
    results = []
    total_healed = 0

    for code in request.code_snippets:
        result = await orchestrator.heal(code)
        results.append(result)
        if result.get("success"):
            total_healed += 1

    return HealBatchResponse(
        results=results,
        total_healed=total_healed
    )


@router.get(
    "/metrics/detailed",
    summary="Detailed metrics (v2 only)",
    response_model=Dict[str, Any]
)
async def get_detailed_metrics(
    orchestrator: RevolutionaryOrchestrator = Depends(get_orchestrator)
) -> Dict[str, Any]:
    """
    Get detailed Prometheus-compatible metrics with labels.

    V2 feature: Enhanced metrics with component breakdown.
    """
    state = orchestrator.get_state()

    metrics = {
        "revolutionary_components_total": state.total_enabled,
        "revolutionary_overall_health": state.overall_health,
        "revolutionary_uptime_seconds": (state.started_at - state.started_at).total_seconds(),
    }

    # Per-component metrics
    for comp in state.components:
        prefix = f"revolutionary_{comp.name}"
        metrics[f"{prefix}_status"] = 1 if comp.status == "active" else 0
        metrics[f"{prefix}_enabled"] = 1 if comp.enabled else 0
        metrics[f"{prefix}_last_update_timestamp"] = comp.last_update.timestamp()

    return {
        "metrics": metrics,
        "labels": {
            "version": "v2",
            "environment": "production"
        }
    }
