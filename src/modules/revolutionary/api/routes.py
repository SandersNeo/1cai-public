"""
Revolutionary Components API Routes

FastAPI routes for revolutionary AI components.
Follows Clean Architecture - this is the API layer.
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from src.modules.revolutionary.domain.models import RevolutionaryOrchestratorState
from src.modules.revolutionary.services.orchestrator import RevolutionaryOrchestrator

router = APIRouter(
    prefix="/revolutionary",
    tags=["Revolutionary Components"],
    responses={404: {"description": "Not found"}},
)

# Singleton orchestrator instance
_orchestrator: RevolutionaryOrchestrator | None = None


async def get_orchestrator() -> RevolutionaryOrchestrator:
    """Dependency to get orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = RevolutionaryOrchestrator()
        await _orchestrator.initialize()
    return _orchestrator


@router.get(
    "/health",
    summary="Revolutionary components health check",
    response_model=Dict[str, Any]
)
async def health_check(
    orchestrator: RevolutionaryOrchestrator = Depends(get_orchestrator)
) -> Dict[str, Any]:
    """
    Check health of revolutionary components.

    Returns:
        Health status of all enabled components
    """
    state = orchestrator.get_state()
    return {
        "status": "healthy" if state.total_enabled > 0 else "no_components",
        "total_enabled": state.total_enabled,
        "overall_health": state.overall_health,
        "components": [
            {
                "name": comp.name,
                "status": comp.status,
                "enabled": comp.enabled
            }
            for comp in state.components
        ]
    }


@router.get(
    "/state",
    summary="Get revolutionary components state",
    response_model=RevolutionaryOrchestratorState
)
async def get_state(
    orchestrator: RevolutionaryOrchestrator = Depends(get_orchestrator)
) -> RevolutionaryOrchestratorState:
    """
    Get detailed state of all revolutionary components.

    Returns:
        Complete state including metrics for each component
    """
    return orchestrator.get_state()


@router.post(
    "/evolve",
    summary="Trigger evolution cycle",
    response_model=Dict[str, Any]
)
async def trigger_evolution(
    orchestrator: RevolutionaryOrchestrator = Depends(get_orchestrator)
) -> Dict[str, Any]:
    """
    Trigger Self-Evolving AI evolution cycle.

    Returns:
        Evolution results

    Raises:
        HTTPException: If Self-Evolving AI is not enabled
    """
    result = await orchestrator.evolve()
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post(
    "/heal",
    summary="Trigger code healing",
    response_model=Dict[str, Any]
)
async def trigger_healing(
    code: str,
    orchestrator: RevolutionaryOrchestrator = Depends(get_orchestrator)
) -> Dict[str, Any]:
    """
    Trigger Self-Healing Code to fix bugs.

    Args:
        code: Code to heal

    Returns:
        Healing results

    Raises:
        HTTPException: If Self-Healing Code is not enabled
    """
    result = await orchestrator.heal(code)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get(
    "/metrics",
    summary="Get Prometheus metrics",
    response_model=Dict[str, Any]
)
async def get_metrics(
    orchestrator: RevolutionaryOrchestrator = Depends(get_orchestrator)
) -> Dict[str, Any]:
    """
    Get Prometheus-compatible metrics for all components.

    Returns:
        Metrics in Prometheus format
    """
    state = orchestrator.get_state()

    metrics = {
        "revolutionary_components_total": state.total_enabled,
        "revolutionary_overall_health": state.overall_health,
    }

    # Add component-specific metrics
    for comp in state.components:
        prefix = f"revolutionary_{comp.name}"
        metrics[f"{prefix}_status"] = 1 if comp.status == "active" else 0
        metrics[f"{prefix}_enabled"] = 1 if comp.enabled else 0

    return metrics
