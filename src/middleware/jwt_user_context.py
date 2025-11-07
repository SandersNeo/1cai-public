"""Middleware that attaches CurrentUser to request.state for downstream usage."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.security.auth import AuthService

logger = logging.getLogger(__name__)


class JWTUserContextMiddleware(BaseHTTPMiddleware):
    """Best-effort middleware that extracts user info from JWT bearer token."""

    def __init__(self, app, auth_service: AuthService) -> None:  # type: ignore[override]
        super().__init__(app)
        self._auth_service = auth_service

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        request.state.current_user = None
        service_token = request.headers.get("X-Service-Token")
        if service_token:
            principal = self._auth_service.authenticate_service_token(service_token)
            if principal:
                request.state.current_user = principal
        authorization: Optional[str] = request.headers.get("Authorization")
        if authorization and authorization.lower().startswith("bearer "):
            token = authorization.split(" ", maxsplit=1)[1].strip()
            try:
                current_user = self._auth_service.decode_token(token)
                request.state.current_user = current_user
            except HTTPException:
                logger.debug("Failed to decode JWT token for request path %s", request.url.path)
        return await call_next(request)

