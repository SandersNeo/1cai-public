# [NEXUS IDENTITY] ID: -1664150677816167666 | DATE: 2025-11-19

"""
Сервис кэширования для Code Review и других сервисов
Версия: 2.0.0

Улучшения:
- Circuit breaker для Redis
- Улучшенная обработка ошибок
- Логирование через logging вместо print
- Timeout для операций Redis
"""

import asyncio
import hashlib
import json
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Optional

import redis.asyncio as aioredis

from src.config import settings
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

# In-memory кэш для fallback (если Redis недоступен)
memory_cache: dict = {}
memory_cache_ttl: dict = {}


class CircuitState(Enum):
    """Состояния circuit breaker"""

    CLOSED = "closed"  # Нормальная работа
    OPEN = "open"  # Сбой, не используем Redis
    HALF_OPEN = "half_open"  # Пробуем восстановить


class CacheService:
    """
    Сервис кэширования результатов с circuit breaker

    Best practices:
    - Circuit breaker для защиты от каскадных сбоев
    - Graceful fallback на in-memory cache
    - Timeout для всех операций
    - Structured logging
    """

    def __init__(self):
        self.redis_client: Optional[aioredis.Redis] = None
        self.use_redis = False
        self.circuit_state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.circuit_open_timeout = 60  # секунд до попытки восстановления
        self.max_failures = 5  # Максимум ошибок перед открытием circuit
        self._init_redis()

    def _init_redis(self):
        """Инициализация Redis клиента (синхронная инициализация)"""
        # Redis инициализируется асинхронно при первом использовании
        self.use_redis = False

    async def _ensure_redis(self):
        """Обеспечение наличия Redis соединения с circuit breaker"""
        # Проверяем circuit breaker
        if self.circuit_state == CircuitState.OPEN:
            # Проверяем, можно ли попробовать восстановить
            if self.last_failure_time:
                elapsed = (datetime.now() -
     self.last_failure_time).total_seconds()
                if elapsed > self.circuit_open_timeout:
                    self.circuit_state = CircuitState.HALF_OPEN
                    logger.info(
                        "Circuit breaker: переход в HALF_OPEN состояние")
                else:
                    return  # Circuit открыт, используем fallback

        if not self.use_redis and not self.redis_client:
            try:
                    "Ошибка чтения из Redis",
                    extra = {
    "key": key,
    "error": str(e),
     "error_type": type(e).__name__},
                    exc_info = True,
                )
                self.failure_count += 1
                self.last_failure_time = datetime.now()

                if self.failure_count >= self.max_failures:
                    self.circuit_state = CircuitState.OPEN

        # In-memory fallback
        if key in memory_cache:
            if key in memory_cache_ttl:
                if datetime.now() < memory_cache_ttl[key]:
                    return memory_cache[key]
                else:
                    # TTL истек
                    del memory_cache[key]
                    del memory_cache_ttl[key]
            else:
                return memory_cache[key]

        return None

    async def set(self, key: str, value: Any, ttl: int = 3600):
        """
        Сохранение значения в кэш с circuit breaker и input validation

        Best practice: Всегда сохраняем в memory cache как fallback
        """
        # Input validation
        if not isinstance(key, str) or not key.strip():
            logger.warning(
                "Invalid key in CacheService.set",
                extra={"key_type": type(key).__name__ if key else None},
            )
            return

        # Limit key length (prevent DoS)
        max_key_length = 1000
        if len(key) > max_key_length:
            logger.warning(
                "Key too long in CacheService.set",
                extra={"key_length": len(key), "max_length": max_key_length},
            )
            key = key[:max_key_length]

        # Validate TTL
        if not isinstance(ttl, int) or ttl < 0:
            logger.warning(
                "Invalid TTL in CacheService.set",
                extra={"ttl": ttl, "ttl_type": type(ttl).__name__},
            )
            ttl = 3600

        if ttl > 86400 * 365:  # Max 1 year
            logger.warning("TTL too large in CacheService.set", extra={"ttl": ttl})
            ttl = 86400 * 365

        await self._ensure_redis()

        try: