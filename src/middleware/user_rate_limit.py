"""Request rate limiting middleware using Redis counters."""

from __future__ import annotations

import time
from typing import Optional

from fastapi import HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from redis.asyncio import Redis

from src.security.auth import AuthService


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
        self.redis = redis_client
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.auth_service = auth_service

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        limiter_key = self._build_rate_key(request)
        if limiter_key:
            current_value = await self.redis.incr(limiter_key)
            if current_value == 1:
                await self.redis.expire(limiter_key, self.window_seconds)
            if current_value > self.max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests, please try again later.",
                )
        return await call_next(request)

    def _build_rate_key(self, request: Request) -> Optional[str]:
        window = int(time.time() // self.window_seconds)
        current_user = getattr(request.state, "current_user", None)
        if not current_user and self.auth_service:
            authorization: Optional[str] = request.headers.get("Authorization")
            if authorization and authorization.lower().startswith("bearer "):
                token = authorization.split(" ", maxsplit=1)[1].strip()
                try:
                    current_user = self.auth_service.decode_token(token)
                    request.state.current_user = current_user
                except HTTPException:
                    current_user = None
        if current_user and getattr(current_user, "user_id", None):
            return f"rl:user:{current_user.user_id}:{window}"
        if request.client and request.client.host:
            return f"rl:ip:{request.client.host}:{window}"
        return None

