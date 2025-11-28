"""
Authentication Middleware
"""
import os
from typing import List

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.infrastructure.logging.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for authentication"""

    def __init__(self, app, allowed_paths: List[str] = None):
        super().__init__(app)
        self.allowed_paths = allowed_paths or [
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/gateway/health",
        ]
        # Use environment variables for API keys
        api_keys_env = os.getenv("GATEWAY_API_KEYS", "")
        if api_keys_env:
            self.valid_api_keys = [
                key.strip() for key in api_keys_env.split(",") if key.strip()]
        else:
            # Fallback for development (in production should be via env)
            self.valid_api_keys = ["demo-key-12345", "admin-key-67890"]
            logger.warning(
                "Using default API keys. Set GATEWAY_API_KEYS environment variable for production!")

    async def dispatch(self, request: Request, call_next):
        """Middleware for authentication with input validation"""
        try:
