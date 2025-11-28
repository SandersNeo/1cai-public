from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.modules.documentation.domain.models import (DocumentationRequest,
                                                     DocumentationResponse)
from src.modules.documentation.services.documentation_service import \
    DocumentationService

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(tags=["Documentation"])


def get_documentation_service() -> DocumentationService:
    return DocumentationService()


@router.post(
    "/generate",
    response_model=DocumentationResponse,
    summary="Генерация документации из кода",
    description="Автоматическая генерация документации для указанного кода",
)
@limiter.limit("5/minute")
async def generate_documentation(
        request: Request,
        doc_request: DocumentationRequest,
        timeout: float = 60.0):
    """Generate documentation with validation and timeout handling."""
    try:
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="An error occurred while generating documentation")


@router.get("/health", summary="Проверка состояния сервиса")
async def health_check():
    """Health check for documentation generation service."""
    return {
        "status": "healthy",
        "service": "documentation-generation",
        "version": "1.0.0",
        "supported_languages": ["bsl", "typescript", "javascript", "python"],
        "supported_formats": ["markdown", "html", "plain"],
    }
