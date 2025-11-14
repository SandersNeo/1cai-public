"""Middleware that attaches CurrentUser to request.state for downstream usage."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.security.auth import AuthService
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class JWTUserContextMiddleware(BaseHTTPMiddleware):
    """Best-effort middleware that extracts user info from JWT bearer token."""

    def __init__(self, app, auth_service: AuthService) -> None:  # type: ignore[override]
        super().__init__(app)
        self._auth_service = auth_service

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        """
        Middleware для извлечения пользователя из JWT токена с input validation
        
        Best practices:
        - Best-effort подход (не блокируем запрос при отсутствии токена)
        - Поддержка service tokens для межсервисной коммуникации
        - Детальное логирование для debugging
        - Безопасная обработка ошибок
        - Input validation для безопасности
        """
        # Input validation
        if not request or not hasattr(request, 'headers'):
            logger.error("Invalid request object in JWTUserContextMiddleware.dispatch")
            return await call_next(request)
        
        request.state.current_user = None
        
        # Sanitize path
        request_path = str(request.url.path) if hasattr(request, 'url') and request.url.path else ""
        if len(request_path) > 1000:
            request_path = request_path[:1000]
        
        # Проверка service token (для межсервисной коммуникации)
        service_token = request.headers.get("X-Service-Token")
        if service_token:
            # Input validation
            if not isinstance(service_token, str):
                logger.warning(
                    "Invalid service token type in JWTUserContextMiddleware.dispatch",
                    extra={"service_token_type": type(service_token).__name__}
                )
            else:
                # Limit token length (prevent DoS)
                max_token_length = 1000
                if len(service_token) > max_token_length:
                    logger.warning(
                        "Service token too long in JWTUserContextMiddleware.dispatch",
                        extra={"token_length": len(service_token), "max_length": max_token_length}
                    )
                    service_token = service_token[:max_token_length]
                
                try:
                    principal = self._auth_service.authenticate_service_token(service_token)
                    if principal:
                        request.state.current_user = principal
                        logger.debug(
                            "Authenticated service token",
                            extra={"path": request_path}
                        )
                except Exception as e:
                    logger.warning(
                        "Failed to authenticate service token",
                        extra={
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "path": request_path
                        },
                        exc_info=True
                    )
        
        # Проверка JWT bearer token
        authorization: Optional[str] = request.headers.get("Authorization")
        if authorization and isinstance(authorization, str) and authorization.lower().startswith("bearer "):
            token = authorization.split(" ", maxsplit=1)[1].strip()
            
            # Validate token length (prevent DoS)
            max_token_length = 10000  # JWT tokens can be long but limit anyway
            if len(token) > max_token_length:
                logger.warning(
                    "JWT token too long in JWTUserContextMiddleware.dispatch",
                    extra={"token_length": len(token), "max_length": max_token_length}
                )
                token = token[:max_token_length]
            
            try:
                current_user = self._auth_service.decode_token(token)
                request.state.current_user = current_user
                user_id = getattr(current_user, 'user_id', 'unknown') if current_user else 'unknown'
                logger.debug(
                    "Authenticated JWT token",
                    extra={
                        "path": request_path,
                        "user_id": str(user_id)[:100] if user_id else None
                    }
                )
            except HTTPException as e:
                # Логируем только на debug уровне (best practice: не засоряем логи)
                logger.debug(
                    "Failed to decode JWT token",
                    extra={
                        "path": request_path,
                        "method": str(request.method)[:10] if hasattr(request, 'method') else None,
                        "status_code": e.status_code if hasattr(e, 'status_code') else None,
                        "error_detail": str(e.detail)[:200] if hasattr(e, 'detail') else None
                    }
                )
            except Exception as e:
                # Неожиданные ошибки логируем на warning уровне
                logger.warning(
                    "Unexpected error decoding JWT token",
                    extra={
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "path": request_path,
                        "method": str(request.method)[:10] if hasattr(request, 'method') else None
                    },
                    exc_info=True
                )
        
        return await call_next(request)

