from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.modules.copilot.domain.models import (
    CompletionRequest,
    GenerationRequest,
    OptimizationRequest,
)
from src.modules.copilot.services.copilot_service import CopilotService
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

router = APIRouter(tags=["Copilot"])
limiter = Limiter(key_func=get_remote_address)

copilot_service = CopilotService()


@router.post("/complete")
@limiter.limit("60/minute")
async def get_completions(api_request: Request, request: CompletionRequest) -> Dict[str, Any]:
    """Autocomplete endpoint."""
    try:
        code = request.code.strip()
        if not code:
            raise HTTPException(status_code=400, detail="Code cannot be empty")

        if len(code) > 50000:
            raise HTTPException(status_code=400, detail="Code too long")

        suggestions = await copilot_service.get_completions(
            code=code,
            current_line=request.current_line,
            max_suggestions=request.max_suggestions,
            timeout=5.0,
        )

        return {"suggestions": suggestions}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error getting completions", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred")


@router.post("/generate")
@limiter.limit("10/minute")
async def generate_code(api_request: Request, request: GenerationRequest) -> Dict[str, Any]:
    """Code generation endpoint."""
    try:
        prompt = request.prompt.strip()
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt cannot be empty")

        if len(prompt) > 5000:
            raise HTTPException(status_code=400, detail="Prompt too long")

        valid_types = ["function", "procedure", "test"]
        code_type = request.type.lower() if request.type else "function"
        if code_type not in valid_types:
            raise HTTPException(
                status_code=400, detail=f"Invalid code_type: {code_type}")

        code = await copilot_service.generate_code(prompt=prompt, code_type=code_type, timeout=10.0)

        return {"code": code}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error generating code", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred")


@router.post("/optimize")
@limiter.limit("10/minute")
async def optimize_code(api_request: Request, request: OptimizationRequest) -> Dict[str, Any]:
    """Code optimization endpoint."""
    try:
        code = request.code.strip()
        if not code:
            raise HTTPException(status_code=400, detail="Code cannot be empty")

        if len(code) > 100000:
            raise HTTPException(status_code=400, detail="Code too long")

        result = await copilot_service.optimize_code(code=code, language=request.language)

        return result

    except Exception as e:
        logger.error("Optimization error", exc_info=True)
        return {"optimized_code": request.code, "improvements": [], "error": str(e)}


@router.post("/generate-tests")
@limiter.limit("10/minute")
async def generate_tests(api_request: Request, request: GenerationRequest) -> Dict[str, Any]:
    """Test generation endpoint."""
    tests = await copilot_service.generate_code(prompt=request.prompt, code_type="test")
    return {"tests": tests}
