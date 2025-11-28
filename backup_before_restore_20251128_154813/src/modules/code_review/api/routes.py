"""
Code Review API Routes
"""
import asyncio
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, Response

from src.infrastructure.logging.structured_logging import StructuredLogger
from src.middleware.rate_limiter import PUBLIC_RATE_LIMIT, limiter
from src.modules.code_review.domain.models import (AutoFixRequest,
                                                   AutoFixResponse,
                                                   CodeAnalysisResponse,
                                                   CodeContextRequest,
                                                   CodeMetrics, CodeStatistics,
                                                   CodeSuggestion)
from src.modules.code_review.services.analyzer import CodeAnalyzer
from src.modules.code_review.services.fixer import CodeFixer
from src.services.caching_service import get_cache_service
from src.services.openai_code_analyzer import get_openai_analyzer

logger = StructuredLogger(__name__).logger

router = APIRouter(tags=["Code Review"])

# Initialize services
analyzer = CodeAnalyzer()
fixer = CodeFixer()


@router.post(
    "/analyze",
    response_model=CodeAnalysisResponse,
    summary="Real-time code analysis",
    description="""
    Analyze code and provide improvement suggestions in real-time.

    **Supported Languages:**
    - BSL (1C:Enterprise)
    - TypeScript
    - JavaScript
    - Python
    - Java
    - C#
    """,
)
@limiter.limit(PUBLIC_RATE_LIMIT)
async def analyze_code(
    request: Request,
    request_data: CodeContextRequest,
     response: Response):
    """
    Analyze code with improvement suggestions
    """
    try:
            "Unexpected error analyzing code",
            extra = {
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info = True,
        )
        raise HTTPException(status_code=500, detail="An error occurred while analyzing code")


@router.post(
    "/auto-fix",
    response_model=AutoFixResponse,
    summary="Automatic code fix",
    description="Apply automatic fix to code based on suggestion",
)
@limiter.limit("20/minute")
async def auto_fix_code_endpoint(api_request: Request, request: AutoFixRequest, response: Response):
    return await fixer.apply_auto_fix(request)


@router.get(
    "/health",
    summary="Check service status",
)
async def health_check():
    """Check Code Review service availability"""
    # Check OpenAI availability
    openai_analyzer = get_openai_analyzer()
    ai_enabled = getattr(openai_analyzer, "enabled", False)

    return {
        "status": "healthy",
        "service": "code-review",
        "version": "1.1.0",
        "features": {
            "bsl": True,
            "typescript": True,
            "python": True,
            "javascript": True,
            "ai_analysis": ai_enabled,
        },
        "openai": {
            "enabled": ai_enabled,
            "model": getattr(openai_analyzer, "model", None) if ai_enabled else None,
        },
    }
