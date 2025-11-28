"""
Tiered Rate Limiting Middleware

Enhanced rate limiting with:
- Tiered limits per user role
- Burst protection
- Path-based limits
- Prometheus metrics export
"""

from __future__ import annotations

import time
from enum import Enum
from typing import Dict, Optional

from fastapi import HTTPException, status
from prometheus_client import Counter, Histogram
from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.modules.auth.application.service import AuthService
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class UserTier(str, Enum):
    """User tier for rate limiting"""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    REVOLUTIONARY = "revolutionary"  # For AI endpoints


# Tier configurations (requests per minute)
TIER_LIMITS: Dict[UserTier, int] = {
    UserTier.FREE: 60,
    UserTier.PRO: 300,
    UserTier.ENTERPRISE: 1000,
    UserTier.REVOLUTIONARY: 100,  # Special limit for AI endpoints
}

# Prometheus metrics
rate_limit_exceeded = Counter(
    'rate_limit_exceeded_total',
    'Total number of rate limit violations',
    ['tier', 'path']
)

rate_limit_requests = Counter(
    'rate_limit_requests_total',
    'Total number of rate limited requests',
    ['tier', 'path', 'status']
)


class TieredRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Apply tiered rate limiting based on user role and endpoint.

    Features:
    - Different limits per tier (free/pro/enterprise)
    - Path-based limits (revolutionary endpoints have separate limits)
    - Burst protection (sliding window)
    - Prometheus metrics
    """

    def __init__(
        self,
        app,
        redis_client: Redis,
        auth_service: Optional[AuthService] = None,
        window_seconds: int = 60,
    ) -> None:
        super().__init__(app)
        self.redis = redis_client
        self.auth_service = auth_service
        self.window_seconds = window_seconds

        logger.info("TieredRateLimitMiddleware initialized")

    async def dispatch(self, request: Request, call_next) -> Response:
        """Apply tiered rate limiting"""

        # Determine user tier and limit
        tier, max_requests = self._get_tier_and_limit(request)

        # Build rate limit key
        limiter_key = self._build_rate_key(request, tier)

        if limiter_key:
            try:
                    f"Error in rate limiting: {e}",
                    extra = {"error_type": type(e).__name__},
                    exc_info = True,
                )
                # Graceful fallback
                return await call_next(request)
        
        return await call_next(request)
    
    def _get_tier_and_limit(self, request: Request) -> tuple[UserTier, int]:
        """
        Determine user tier and corresponding limit.
        
        Returns:
            (tier, max_requests)
        """
        # Check if revolutionary endpoint
        path = str(request.url.path)
        if "/revolutionary" in path:
            return UserTier.REVOLUTIONARY, TIER_LIMITS[UserTier.REVOLUTIONARY]
        
        # Get user from request state
        current_user = getattr(request.state, "current_user", None)
        
        if current_user:
            # Get user tier from user object
            user_tier = getattr(current_user, "tier", None)
            
            if user_tier == "enterprise":
                return UserTier.ENTERPRISE, TIER_LIMITS[UserTier.ENTERPRISE]
            elif user_tier == "pro":
                return UserTier.PRO, TIER_LIMITS[UserTier.PRO]
        
        # Default to free tier
        return UserTier.FREE, TIER_LIMITS[UserTier.FREE]
    
    def _build_rate_key(self, request: Request, tier: UserTier) -> Optional[str]:
        """Build rate limit key"""
        try: