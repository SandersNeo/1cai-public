"""
API endpoints для автоматической генерации документации
Версия: 1.0.0
"""

import logging
import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from src.services.documentation_generation_service import get_documentation_generator
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger
router = APIRouter()


# ==================== МОДЕЛИ ДАННЫХ ====================

class DocumentationRequest(BaseModel):
    """Запрос на генерацию документации"""
    code: str = Field(..., description="Исходный код для документирования")
    language: Literal["bsl", "typescript", "javascript", "python"] = Field(
        default="bsl",
        description="Язык программирования"
    )
    functionName: Optional[str] = Field(None, description="Имя конкретной функции для документирования")
    format: Literal["markdown", "html", "plain"] = Field(
        default="markdown",
        description="Формат документации"
    )


class DocumentationResponse(BaseModel):
    """Ответ генерации документации"""
    title: str
    language: str
    format: str
    content: str
    sections: list
    generatedAt: datetime = Field(default_factory=datetime.now)
    generationId: str


# ==================== API ENDPOINTS ====================

@router.post(
    "/generate",
    response_model=DocumentationResponse,
    tags=["Documentation"],
    summary="Генерация документации из кода",
    description="Автоматическая генерация документации для указанного кода"
)
async def generate_documentation(request: DocumentationRequest, timeout: float = 60.0):
    """
    Генерация документации с валидацией входных данных и timeout handling
    
    Best practices:
    - Валидация длины кода
    - Sanitization входных данных
    - Timeout handling для предотвращения зависаний
    - Улучшенная обработка ошибок
    """
    
    # Input validation
    if not isinstance(timeout, (int, float)) or timeout <= 0:
        logger.warning(
            "Invalid timeout in generate_documentation",
            extra={"timeout": timeout, "timeout_type": type(timeout).__name__}
        )
        timeout = 60.0
    
    if timeout > 300:  # Max 5 minutes
        logger.warning(
            "Timeout too large in generate_documentation",
            extra={"timeout": timeout}
        )
        timeout = 300.0
    
    try:
        # Input validation and sanitization (best practice)
        if not isinstance(request.code, str):
            raise HTTPException(
                status_code=400,
                detail="Code must be a string"
            )
        
        code = request.code.strip()
        if not code:
            raise HTTPException(
                status_code=400,
                detail="Code cannot be empty"
            )
        
        # Limit code length (prevent DoS)
        max_code_length = 100000  # 100KB max
        if len(code) > max_code_length:
            logger.warning(
                "Code too long in generate_documentation",
                extra={"code_length": len(code), "max_length": max_code_length}
            )
            raise HTTPException(
                status_code=400,
                detail=f"Code too long. Maximum length: {max_code_length} characters"
            )
        
        # Validate language
        supported_languages = ["bsl", "typescript", "javascript", "python"]
        if request.language not in supported_languages:
            logger.warning(
                "Unsupported language in generate_documentation",
                extra={"language": request.language, "supported": supported_languages}
            )
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported language: {request.language}. Supported: {', '.join(supported_languages)}"
            )
        
        # Sanitize function name if provided
        function_name = None
        if request.functionName:
            if not isinstance(request.functionName, str):
                logger.warning(
                    "Invalid functionName type in generate_documentation",
                    extra={"functionName_type": type(request.functionName).__name__}
                )
            else:
                function_name = request.functionName.strip()[:200]  # Limit length
        
        doc_generator = get_documentation_generator()
        
        # Execute with timeout
        try:
            doc = await asyncio.wait_for(
                asyncio.to_thread(
                    doc_generator.generate_documentation,
                    code=code,
                    language=request.language,
                    function_name=function_name,
                    format=request.format
                ),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.error(
                "Timeout generating documentation",
                extra={
                    "language": request.language,
                    "format": request.format,
                    "code_length": len(code),
                    "timeout": timeout
                }
            )
            raise HTTPException(
                status_code=408,
                detail=f"Documentation generation timed out after {timeout} seconds"
            )
        
        generation_id = f"doc-{datetime.now().timestamp()}"
        
        return DocumentationResponse(
            title=doc.get("title", "Documentation"),
            language=doc.get("language", request.language),
            format=request.format,
            content=doc.get("content", ""),
            sections=doc.get("sections", []),
            generationId=generation_id
        )
    
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except ValueError as e:
        logger.warning(
            "Validation error in documentation generation",
            extra={
                "error": str(e),
                "error_type": type(e).__name__
            }
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            f"Unexpected error generating documentation: {e}",
            extra={
                "language": request.language if hasattr(request, 'language') else None,
                "format": request.format if hasattr(request, 'format') else None,
                "code_length": len(request.code) if hasattr(request, 'code') else 0,
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="An error occurred while generating documentation"
        )


@router.get(
    "/health",
    tags=["Documentation"],
    summary="Проверка состояния сервиса"
)
async def health_check():
    """Проверка доступности сервиса генерации документации"""
    return {
        "status": "healthy",
        "service": "documentation-generation",
        "version": "1.0.0",
        "supported_languages": ["bsl"],
        "supported_formats": ["markdown", "html", "plain"]
    }







