"""
Council API Routes

API endpoints for LLM Council functionality.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field


from src.api.auth import get_current_user
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

router = APIRouter(prefix="/council", tags=["council"])


class CouncilQueryRequest(BaseModel):
    """Request for council query"""

    query: str = Field(..., description="User query")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional context")
    council_config: Optional[Dict[str, Any]] = Field(default=None, description="Optional council configuration")


class CouncilQueryResponse(BaseModel):
    """Response from council query"""

    final_answer: str
    individual_opinions: List[Dict]
    peer_reviews: List[Dict]
    chairman_synthesis: str
    metadata: Dict


@router.post("/query", response_model=CouncilQueryResponse)
async def query_with_council(request: CouncilQueryRequest, current_user: Dict = Depends(get_current_user)):
    """
    Query with LLM Council consensus.

    **Process:**
    1. Stage 1: Multiple models provide first opinions (parallel)
    2. Stage 2: Models review each other's responses (peer review)
    3. Stage 3: Chairman synthesizes final answer

    **Example:**
    ```json
    {
        "query": "Generate BSL code for document processing",
        "context": {
            "configuration": "УТ 11.5",
            "object_type": "Document"
        },
        "council_config": {
            "models": ["kimi", "qwen", "gigachat"],
            "chairman": "kimi"
        }
    }
    ```
    """
    try:
        logger.info(
            f"Council query from user {current_user.get('username')}", extra={"query_length": len(request.query)}
        )

        from src.ai.orchestrator import get_orchestrator

        result = await get_orchestrator().process_query_with_council(
            query=request.query, context=request.context, council_config=request.council_config
        )

        return result

    except ValueError as e:
        logger.error("Council query validation error: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Council query error: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/config")
async def get_council_config(current_user: Dict = Depends(get_current_user)):
    """
    Get current council configuration.

    Returns default council settings.
    """
    from src.ai.council.config import (
        CHAIRMAN_MODEL,
        COUNCIL_ENABLED,
        COUNCIL_MODELS,
        MAX_COUNCIL_SIZE,
        MIN_COUNCIL_SIZE,
    )

    return {
        "enabled": COUNCIL_ENABLED,
        "default_models": COUNCIL_MODELS,
        "default_chairman": CHAIRMAN_MODEL,
        "min_council_size": MIN_COUNCIL_SIZE,
        "max_council_size": MAX_COUNCIL_SIZE,
    }


@router.get("/health")
async def council_health():
    """
    Check council health.

    Returns status of council orchestrator.
    """
    from src.ai.orchestrator import get_orchestrator

    if get_orchestrator().council is None:
        return {"status": "unavailable", "message": "Council orchestrator not initialized"}

    return {"status": "healthy", "message": "Council orchestrator ready"}
