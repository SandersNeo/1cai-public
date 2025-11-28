# [NEXUS IDENTITY] ID: -5028614272032623839 | DATE: 2025-11-19

"""
Request rate limiting middleware using Redis counters.
Версия: 2.1.0

Улучшения:
- Structured logging
- Улучшена обработка ошибок
- Graceful fallback при ошибках Redis
"""

from __future__ import annotations

import time
from typing import Optional

from fastapi import HTTPException, status
from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.modules.auth.application.service import AuthService
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class UserRateLimitMiddleware(BaseHTTPMiddleware):
    """Apply per-user or per-IP rate limiting using Redis counters."""

    def __init__(
        self,
        app,
        redis_client: Redis,
        max_requests: int = 60,
        window_seconds: int = 60,
        auth_service: Optional[AuthService] = None,
    ) -> None:
        super().__init__(app)

        # Input validation
        if not isinstance(max_requests, int) or max_requests < 1:
            logger.warning(
                "Invalid max_requests in UserRateLimitMiddleware.__init__",
                extra={
                    "max_requests": max_requests,
                    "max_requests_type": type(max_requests).__name__,
                },
            )
            max_requests = 60  # Default

        if not isinstance(window_seconds, int) or window_seconds < 1:
            logger.warning(
                "Invalid window_seconds in UserRateLimitMiddleware.__init__",
                extra={
                    "window_seconds": window_seconds,
                    "window_seconds_type": type(window_seconds).__name__,
                },
            )
            window_seconds = 60  # Default

        self.redis = redis_client
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.auth_service = auth_service

        logger.debug(
            "UserRateLimitMiddleware initialized",
            extra={
                "max_requests": max_requests,
                "window_seconds": window_seconds},
        )

    # type: ignore[override]
    async def dispatch(self, request: Request, call_next) -> Response:
        limiter_key = self._build_rate_key(request)
        if limiter_key:
            try:
