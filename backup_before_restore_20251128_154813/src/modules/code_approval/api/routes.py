"""
Code Approval API Routes
"""
import asyncio
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.infrastructure.logging.structured_logging import StructuredLogger
from src.modules.code_approval.domain.models import (BulkApprovalRequest,
                                                     CodeApprovalRequest,
                                                     CodeGenerationRequest)
from src.modules.code_approval.services.approval_service import \
    CodeApprovalService

logger = StructuredLogger(__name__).logger

router = APIRouter(tags=["Code Approval"])
limiter = Limiter(key_func=get_remote_address)


# Dependency
def get_approval_service() -> CodeApprovalService:
    return CodeApprovalService()


@router.post(
    "/generate",
    summary="Generate code with AI",
    description="Generate code with AI and return suggestion with approval token",
    responses={
        200: {"description": "Code generated successfully"},
        400: {"description": "Invalid input"},
        403: {"description": "Request blocked by security"},
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit("10/minute")
async def generate_code(
    api_request: Request,
    request: CodeGenerationRequest,
    service: CodeApprovalService = Depends(get_approval_service),
):
    """
    Generate code with AI with input validation
    """
    try:
            "Unexpected error generating code",
            extra = {
                "error": str(e),
                "error_type": type(e).__name__,
                "user_id": request.user_id,
            },
            exc_info = True,
        )
        raise HTTPException(status_code=500, detail="An error occurred while generating code")


@router.get("/preview/{token}")
async def get_preview(token: str, service: CodeApprovalService = Depends(get_approval_service)):
    """
    Get preview suggestion for review
    """
    if not isinstance(token, str) or not token.strip():
        raise HTTPException(status_code=400, detail="Token cannot be empty")

    max_token_length = 200
    if len(token) > max_token_length:
        raise HTTPException(status_code=400, detail="Token too long")

    try:
        raise HTTPException(status_code=500, detail="An error occurred while retrieving preview")


@router.post("/approve")
@limiter.limit("30/minute")
async def approve_suggestion(
    api_request: Request,
    request: CodeApprovalRequest,
    service: CodeApprovalService = Depends(get_approval_service),
):
    """
    Approve and apply suggestion
    """
    if not request.token.strip():
        raise HTTPException(status_code=400, detail="Token cannot be empty")

    if not request.approved_by_user.strip():
        raise HTTPException(status_code=400, detail="Approved by user cannot be empty")

    try:
    except Exception as e:
        logger.error("Error in approve_suggestion: %s", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while approving suggestion")


@router.post("/approve-all")
@limiter.limit("10/minute")
async def bulk_approve(
    api_request: Request,
    request: BulkApprovalRequest,
    service: CodeApprovalService = Depends(get_approval_service),
):
    """
    Bulk approval for multiple suggestions
    """
    if not request.tokens:
        raise HTTPException(status_code=400, detail="Tokens list cannot be empty")

    if len(request.tokens) > 100:
        request.tokens = request.tokens[:100]

    validated_tokens = [t.strip() for t in request.tokens if t.strip()]

    if not validated_tokens:
        raise HTTPException(status_code=400, detail="No valid tokens provided")

    try:
        raise HTTPException(status_code=500, detail="An error occurred while processing bulk approval")


@router.delete("/reject/{token}")
async def reject_suggestion(token: str, service: CodeApprovalService = Depends(get_approval_service)):
    """
    Reject suggestion
    """
    if not token.strip():
        raise HTTPException(status_code=400, detail="Token cannot be empty")

    try:
        raise HTTPException(status_code=500, detail="An error occurred while rejecting suggestion")


@router.get("/pending")
async def get_pending_suggestions(user_id: str, service: CodeApprovalService = Depends(get_approval_service)):
    """
    Get all pending suggestions for user
    """
    if not user_id.strip():
        raise HTTPException(status_code=400, detail="User ID cannot be empty")

    try: