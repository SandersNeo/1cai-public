# [NEXUS IDENTITY] ID: 3208893905318328916 | DATE: 2025-11-19

"""
Centralized Error Handling
Версия: 2.1.0

Улучшения:
- Structured logging
- Улучшена обработка ошибок

Best Practices from top companies (Google, Microsoft, AWS)

Features:
- Structured error responses
- Error codes and categories
- Automatic logging
- Integration with OpenTelemetry
- User-friendly error messages
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from src.utils.structured_logging import StructuredLogger

structured_logger = StructuredLogger(__name__)
logger = structured_logger.logger


def _safe_request_path(request: Request) -> str:
    try:
        return request.url.path
    except Exception:
        scope = getattr(request, "scope", {}) or {}
        return scope.get("path", "unknown")


def _safe_request_method(request: Request) -> str:
    try:
        return request.method
    except Exception:
        scope = getattr(request, "scope", {}) or {}
        return scope.get("method", "UNKNOWN")


# Error categories
class ErrorCategory:
    """Error categories for better error handling"""

    VALIDATION = "validation_error"
    AUTHENTICATION = "authentication_error"
    AUTHORIZATION = "authorization_error"
    NOT_FOUND = "not_found"
    RATE_LIMIT = "rate_limit_error"
    INTERNAL = "internal_error"
    EXTERNAL_SERVICE = "external_service_error"
    BUSINESS_LOGIC = "business_logic_error"


class ErrorCode:
    """Standard error codes"""

    # Validation
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"

    # Authentication
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    MISSING_AUTH_HEADER = "MISSING_AUTH_HEADER"

    # Authorization
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    FORBIDDEN_RESOURCE = "FORBIDDEN_RESOURCE"

    # Not Found
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    ENDPOINT_NOT_FOUND = "ENDPOINT_NOT_FOUND"

    # Rate Limit
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # Internal
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    CACHE_ERROR = "CACHE_ERROR"

    # External Service
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"

    # Business Logic
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"
    INVALID_STATE = "INVALID_STATE"


class APIError(HTTPException):
    """
    Custom API error with structured information

    Best practice: Use structured errors for better client handling
    """

    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        category: str = ErrorCategory.INTERNAL,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ):
        super().__init__(status_code=status_code, detail=message)
        self.error_code = error_code
        self.category = category
        self.details = details or {}
        self.request_id = request_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary"""
        return {
            "error": {
                "code": self.error_code,
                "message": self.detail,
                "category": self.category,
                "details": self.details,
                "request_id": self.request_id,
            }
        }


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Custom HTTP exception handler

    Best practice: Return structured error responses
    """
    request_id = getattr(request.state, "request_id", None)

    # Determine error category and code
    if exc.status_code == 404:
        category = ErrorCategory.NOT_FOUND
        error_code = ErrorCode.RESOURCE_NOT_FOUND
    elif exc.status_code == 401:
        category = ErrorCategory.AUTHENTICATION
        error_code = ErrorCode.INVALID_TOKEN
    elif exc.status_code == 403:
        category = ErrorCategory.AUTHORIZATION
        error_code = ErrorCode.INSUFFICIENT_PERMISSIONS
    elif exc.status_code == 429:
        category = ErrorCategory.RATE_LIMIT
        error_code = ErrorCode.RATE_LIMIT_EXCEEDED
    else:
        category = ErrorCategory.INTERNAL
        error_code = ErrorCode.INTERNAL_SERVER_ERROR

    error_response = {
        "error": {
            "code": error_code,
            "message": exc.detail,
            "category": category,
            "request_id": request_id,
        }
    }

    # Log error with structured logging
    logger.error(
        "HTTP exception",
        extra={
            "request_id": request_id,
            "path": _safe_request_path(request),
            "method": _safe_request_method(request),
            "status_code": exc.status_code,
            "error_code": error_code,
            "category": category,
            "error_type": type(exc).__name__,
            "detail": exc.detail,
        },
        exc_info=exc.status_code >= 500,  # Full traceback for server errors
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Custom validation exception handler

    Best practice: Provide detailed validation errors
    """
    request_id = getattr(request.state, "request_id", None)

    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    error_response = {
        "error": {
            "code": ErrorCode.INVALID_INPUT,
            "message": "Validation failed",
            "category": ErrorCategory.VALIDATION,
            "details": {
                "validation_errors": errors,
            },
            "request_id": request_id,
        }
    }

    logger.warning(
        f"Validation error: {len(errors)} field(s) failed validation",
        extra={
            "request_id": request_id,
            "path": _safe_request_path(request),
            "method": _safe_request_method(request),
            "errors_count": len(errors),
            "errors": errors,
        },
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response,
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    General exception handler for unhandled exceptions

    Best practice: Don't expose internal errors to clients
    """
    request_id = getattr(request.state, "request_id", None)

    # Log full exception with structured logging
    logger.error(
        "Unhandled exception",
        extra={
            "error": str(exc),
            "error_type": type(exc).__name__,
            "request_id": request_id,
            "path": _safe_request_path(request),
            "method": _safe_request_method(request),
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
        },
        exc_info=True,
    )

    error_response = {
        "error": {
            "code": ErrorCode.INTERNAL_SERVER_ERROR,
            "message": "An internal error occurred. Please try again later.",
            "category": ErrorCategory.INTERNAL,
            "request_id": request_id,
        }
    }

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response,
    )


def register_error_handlers(app):
    """
    Register all error handlers with FastAPI app

    Usage:
        from src.utils.error_handling import register_error_handlers
        register_error_handlers(app)
    """
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    logger.info("✅ Error handlers registered")
