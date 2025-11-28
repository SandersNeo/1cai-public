# [NEXUS IDENTITY] ID: 5710371405805580324 | DATE: 2025-11-19

"""
Rate Limiting Middleware для FastAPI
Версия: 2.0.0

Улучшения:
- Поддержка Redis для распределенного rate limiting
- Улучшенная обработка ошибок
- Структурированное логирование
- Graceful fallback на memory storage
"""

import os
from typing import Callable

from fastapi import Request, Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


# Определение storage для rate limiting (best practice: Redis для production)
def get_storage_uri() -> str:
    """
    Получить URI storage для rate limiting с input validation

    Best practice: Использовать Redis для распределенного rate limiting в production
    """
    redis_url = os.getenv("REDIS_URL", "")

    # Input validation and sanitization
    if redis_url and isinstance(redis_url, str):
        # Limit URL length (prevent DoS)
        max_url_length = 1000
        if len(redis_url) > max_url_length:
            logger.warning(
                "Redis URL too long in get_storage_uri",
                extra={
                    "url_length": len(redis_url),
                    "max_length": max_url_length},
            )
            redis_url = redis_url[:max_url_length]

        # Basic URL validation (prevent injection)
        if redis_url.startswith(("redis://", "rediss://", "unix://")):
            logger.info(
                "Using Redis for rate limiting",
                extra={"redis_url_length": len(redis_url)},
            )
            return redis_url
        else:
            logger.warning(
                "Invalid Redis URL format in get_storage_uri",
                extra={"redis_url_start": redis_url[:20] if redis_url else None},
            )
            redis_url = ""

    # Fallback на memory storage (для development или single-instance)
    logger.warning(
        "Redis not configured, using memory storage for rate limiting")
    return "memory://"


# Создание лимитера с улучшенной конфигурацией
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000/hour"],  # По умолчанию 1000 запросов в час
    storage_uri=get_storage_uri(),
    headers_enabled=True,  # Включаем заголовки X-RateLimit-*
    retry_after="x-ratelimit-retry-after",  # Стандартный заголовок для retry
)


def create_rate_limit_middleware(app):
    """Создание rate limiting middleware для приложения"""

    # Добавление обработчика ошибок rate limit
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    @app.middleware("http")
    async def rate_limit_middleware(
            request: Request,
            call_next: Callable) -> Response:
        """
        Middleware для rate limiting с улучшенной обработкой ошибок и input validation

        Best practices:
        - Пропускаем health checks и документацию
        - Логируем rate limit violations
        - Возвращаем структурированные ошибки
        - Input validation для безопасности
        """
        # Input validation
        if not request or not hasattr(request, "url"):
            logger.error("Invalid request object in rate_limit_middleware")
            return await call_next(request)

        # Пропускаем health checks и документацию (best practice)
        excluded_paths = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/metrics",
            "/favicon.ico",
        ]

        # Sanitize path (prevent injection)
        request_path = str(request.url.path) if request.url.path else ""
        if len(request_path) > 1000:  # Prevent DoS
            logger.warning(
                "Path too long in rate_limit_middleware",
                extra={"path_length": len(request_path)},
            )
            request_path = request_path[:1000]

        if request_path in excluded_paths:
            return await call_next(request)

        try:
