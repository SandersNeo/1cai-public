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

from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.utils.structured_logging import StructuredLogger

structured_logger = StructuredLogger(__name__)
logger = structured_logger.logger


def _safe_request_path(request: Request) -> str:
    try:
