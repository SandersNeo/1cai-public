"""
Request Logging Middleware
"""
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.infrastructure.logging.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request logging"""

    def __init__(self, app):
        super().__init__(app)
        self.request_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "response_times": [],
            "service_calls": {},
        }

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Log incoming request
        logger.info(
            f"Incoming request: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query_params": str(
                    request.url.query) if request.url.query else None,
            },
        )

        self.request_stats["total_requests"] += 1

        try:
