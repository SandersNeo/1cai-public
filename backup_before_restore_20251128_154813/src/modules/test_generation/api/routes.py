"""
Test Generation API Routes
"""
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request

from src.infrastructure.logging.structured_logging import StructuredLogger
from src.middleware.rate_limiter import limiter
from src.modules.test_generation.domain.models import (GeneratedTest,
                                                       TestGenerationRequest,
                                                       TestGenerationResponse)
from src.modules.test_generation.services.generator import TestGeneratorService
from src.services.openai_code_analyzer import get_openai_analyzer

logger = StructuredLogger(__name__).logger

router = APIRouter(tags=["Test Generation"])

# Initialize service
generator_service = TestGeneratorService()


@router.post(
    "/generate",
    response_model=TestGenerationResponse,
    summary="Generate tests for code",
    description="Automatically generate tests for the provided code",
)
@limiter.limit("10/minute")
async def generate_tests(
    request: Request,
     request_data: TestGenerationRequest):
    """
    Generate tests with input validation
    """
    try:
            "Unexpected error in test generation",
            extra = {
                "error": str(e),
                "language": request_data.language,
            },
            exc_info = True,
        )
        raise HTTPException(status_code=500, detail="An error occurred while generating tests")


@router.get("/health", summary="Check service status")
async def health_check():
    """Check Test Generation service availability"""
    openai_analyzer = get_openai_analyzer()
    ai_enabled = getattr(openai_analyzer, "enabled", False)

    return {
        "status": "healthy",
        "service": "test-generation",
        "version": "1.1.0",
        "supported_languages": ["bsl", "typescript", "python", "javascript"],
        "features": {
            "unit_tests": True,
            "ai_generation": ai_enabled,
        },
    }
