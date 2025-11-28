# [NEXUS IDENTITY] ID: 8774243699080093361 | DATE: 2025-11-19

"""
Security Headers Middleware
Версия: 2.1.0

Улучшения:
- Structured logging
- Улучшена обработка ошибок
- Input validation для CSP policy

Features:
- Content Security Policy (CSP)
- XSS Protection
- Clickjacking Protection
- MIME Sniffing Protection
- HSTS (HTTP Strict Transport Security)
- Referrer Policy
- Permissions Policy
"""

import os
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware для добавления security headers ко всем ответам"""

    async def dispatch(
            self,
            request: Request,
            call_next: Callable) -> Response:
        return await security_headers_middleware(request, call_next)


async def security_headers_middleware(
    request: Request, call_next: Callable
) -> Response:
    """
    Add security headers to all responses

    Headers:
    - Content-Security-Policy: Prevents XSS
    - X-Frame-Options: Prevents clickjacking
    - X-Content-Type-Options: Prevents MIME sniffing
    - Strict-Transport-Security: Forces HTTPS
    - Referrer-Policy: Controls referrer info
    - Permissions-Policy: Controls browser features
    """
    try:
