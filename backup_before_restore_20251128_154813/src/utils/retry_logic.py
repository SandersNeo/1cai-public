# [NEXUS IDENTITY] ID: -8326230187956268435 | DATE: 2025-11-19

"""
Retry Logic with Exponential Backoff
Версия: 2.0.0

Улучшения:
- Jitter для предотвращения thundering herd
- Улучшенное логирование с контекстом
- Поддержка circuit breaker pattern
- Метрики retry attempts
- Configurable retry strategies

Best Practices:
- Exponential backoff с jitter
- Retry только для transient errors
- Логирование всех попыток
- Метрики для мониторинга
"""

import asyncio
import random
import secrets
from enum import Enum
from functools import wraps
from typing import Any, Callable, Tuple, Type

from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class RetryStrategy(Enum):
    """Стратегии retry"""

    EXPONENTIAL = "exponential"  # Exponential backoff
    LINEAR = "linear"  # Linear backoff
    CONSTANT = "constant"  # Constant delay


async def retry_async(
    func: Callable,
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    jitter: bool = True,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    *args,
    **kwargs,
) -> Any:
    """
    Retry async function with exponential backoff and jitter с input validation

    Best practices:
    - Exponential backoff для предотвращения перегрузки сервиса
    - Jitter для предотвращения thundering herd problem
    - Retry только для transient errors
    - Структурированное логирование

    Args:
        func: Async function to retry
        max_attempts: Maximum retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff (2 = double each time)
        exceptions: Tuple of exceptions to catch and retry
        jitter: Add random jitter to delay (prevents thundering herd)
        strategy: Retry strategy (exponential, linear, constant)

    Returns:
        Result of function call

    Raises:
        Last exception if all retries fail
    """
    # Input validation
    if not callable(func):
        logger.error(
            "Invalid func in retry_async", extra={
                "func_type": type(func).__name__})
        raise ValueError("func must be callable")

    if not isinstance(max_attempts, int) or max_attempts < 1:
        logger.warning(
            "Invalid max_attempts in retry_async",
            extra={
                "max_attempts": max_attempts,
                "max_attempts_type": type(max_attempts).__name__,
            },
        )
        max_attempts = 3

    if max_attempts > 100:  # Prevent DoS
        logger.warning(
            "Max attempts too large in retry_async",
            extra={"max_attempts": max_attempts},
        )
        max_attempts = 100

    if not isinstance(initial_delay, (int, float)) or initial_delay < 0:
        logger.warning(
            "Invalid initial_delay in retry_async",
            extra={
                "initial_delay": initial_delay,
                "initial_delay_type": type(initial_delay).__name__,
            },
        )
        initial_delay = 1.0

    if not isinstance(max_delay, (int, float)) or max_delay < 0:
        logger.warning(
            "Invalid max_delay in retry_async",
            extra={
                "max_delay": max_delay,
                "max_delay_type": type(max_delay).__name__},
        )
        max_delay = 60.0

    if max_delay > 3600:  # Prevent DoS (max 1 hour)
        logger.warning(
            "Max delay too large in retry_async", extra={
                "max_delay": max_delay})
        max_delay = 3600

    if not isinstance(exponential_base, (int, float)) or exponential_base < 1:
        logger.warning(
            "Invalid exponential_base in retry_async",
            extra={
                "exponential_base": exponential_base,
                "exponential_base_type": type(exponential_base).__name__,
            },
        )
        exponential_base = 2.0

    if not isinstance(jitter, bool):
        logger.warning(
            "Invalid jitter type in retry_async",
            extra={"jitter": jitter, "jitter_type": type(jitter).__name__},
        )
        jitter = True

    if not isinstance(strategy, RetryStrategy):
        logger.warning(
            "Invalid strategy in retry_async",
            extra={
                "strategy": strategy,
                "strategy_type": type(strategy).__name__},
        )
        strategy = RetryStrategy.EXPONENTIAL

    last_exception = None
    func_name = getattr(func, "__name__", str(func))

    for attempt in range(max_attempts):
        try:
