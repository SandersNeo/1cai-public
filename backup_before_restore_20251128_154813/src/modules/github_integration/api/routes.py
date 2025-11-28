"""
GitHub Integration API Routes
FastAPI endpoints for GitHub webhook and manual review
"""
import asyncio
from typing import Any, Dict

from fastapi import APIRouter, Header, HTTPException, Request

from src.infrastructure.logging.structured_logging import StructuredLogger
from src.modules.github_integration.services.github_client import GitHubClient
from src.modules.github_integration.services.review_service import \
    ReviewService
from src.modules.github_integration.services.webhook_handler import \
    WebhookHandler

logger = StructuredLogger(__name__).logger

# Create router
router = APIRouter(tags=["GitHub Integration"])

# Initialize services
github_client = GitHubClient()
webhook_handler = WebhookHandler()
review_service = ReviewService(github_client)


@router.post("/webhook")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(None),
    x_hub_signature_256: str = Header(None),
) -> Dict[str, Any]:
    """
    GitHub Webhook endpoint

    Accepts events from GitHub:
    - pull_request
    - push
    - etc.

    Args:
        request: FastAPI request object
        x_github_event: GitHub event type header
        x_hub_signature_256: Webhook signature header

    Returns:
        Processing result dictionary

    Raises:
        HTTPException: On validation or processing errors
    """
    try:
        raise HTTPException(status_code=504, detail="Request timeout")
    except Exception as e:
        logger.error(
            "Unexpected error in github_webhook",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "event_type": x_github_event,
            },
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/review")
async def manual_review(
    code: str, filename: str = "code.bsl") -> Dict[str, Any]:
    """
    Manual code review endpoint (for testing)

    Args:
        code: Code content to review
        filename: File name (default: code.bsl)

    Returns:
        Review result dictionary

    Raises:
        HTTPException: On validation or processing errors
    """
    # Input validation
    if not isinstance(code, str):
        logger.warning(
    "Invalid code type", extra={
        "code_type": type(code).__name__})
        raise HTTPException(status_code=400, detail="Code must be a string")

    # Limit code length (prevent DoS)
    max_code_length = 10 * 1024 * 1024  # 10 MB
    if len(code) > max_code_length:
        logger.warning(
            "Code too long",
            extra={"code_length": len(code), "max_length": max_code_length},
        )
        raise HTTPException(status_code=413, detail="Code too large")

    if not isinstance(filename, str) or not filename.strip():
        logger.warning(
    "Invalid filename", extra={
        "filename_type": type(filename).__name__})
        filename = "code.bsl"

    # Sanitize filename (prevent path traversal)
    filename = filename.replace("..", "").replace("/", "_").replace("\\", "_")
    if len(filename) > 255:
        filename = filename[:255]

    try:
            "Error in manual_review",
            extra = {
                "error": str(e),
                "error_type": type(e).__name__,
                "filename": filename,
            },
            exc_info = True,
        )
        raise HTTPException(status_code=500, detail="An error occurred during code review")
