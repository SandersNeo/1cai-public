"""
Security Middleware for User Context
"""

from typing import Any

from fastapi import Request
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class CurrentUser(BaseModel):
    user_id: str
    roles: list[str]


async def get_current_user(request: Request) -> CurrentUser:
    """
    Dependency to get current user from request state
    """
    # Fallback for tests or if middleware didn't run/failed
    user_id = getattr(request.state, "user_id", "anonymous")
    return CurrentUser(user_id=str(user_id), roles=[])


class JWTUserContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, auth_service: Any = None):
        super().__init__(app)
        self.auth_service = auth_service

    async def dispatch(self, request: Request, call_next):
        # STUB: Logic to extract token and validate
        # For now, we just set a mock user
        request.state.user_id = "dev-user-1"
        request.state.tenant_id = "tenant-1"

        response = await call_next(request)
        return response
