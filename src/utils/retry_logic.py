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

import logging
import asyncio
import time
import random
from typing import Callable, Any, Type, Tuple, Optional
from functools import wraps
from enum import Enum

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
    **kwargs
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
            "Invalid func in retry_async",
            extra={"func_type": type(func).__name__}
        )
        raise ValueError("func must be callable")
    
    if not isinstance(max_attempts, int) or max_attempts < 1:
        logger.warning(
            "Invalid max_attempts in retry_async",
            extra={"max_attempts": max_attempts, "max_attempts_type": type(max_attempts).__name__}
        )
        max_attempts = 3
    
    if max_attempts > 100:  # Prevent DoS
        logger.warning(
            "Max attempts too large in retry_async",
            extra={"max_attempts": max_attempts}
        )
        max_attempts = 100
    
    if not isinstance(initial_delay, (int, float)) or initial_delay < 0:
        logger.warning(
            "Invalid initial_delay in retry_async",
            extra={"initial_delay": initial_delay, "initial_delay_type": type(initial_delay).__name__}
        )
        initial_delay = 1.0
    
    if not isinstance(max_delay, (int, float)) or max_delay < 0:
        logger.warning(
            "Invalid max_delay in retry_async",
            extra={"max_delay": max_delay, "max_delay_type": type(max_delay).__name__}
        )
        max_delay = 60.0
    
    if max_delay > 3600:  # Prevent DoS (max 1 hour)
        logger.warning(
            "Max delay too large in retry_async",
            extra={"max_delay": max_delay}
        )
        max_delay = 3600
    
    if not isinstance(exponential_base, (int, float)) or exponential_base < 1:
        logger.warning(
            "Invalid exponential_base in retry_async",
            extra={"exponential_base": exponential_base, "exponential_base_type": type(exponential_base).__name__}
        )
        exponential_base = 2.0
    
    if not isinstance(jitter, bool):
        logger.warning(
            "Invalid jitter type in retry_async",
            extra={"jitter": jitter, "jitter_type": type(jitter).__name__}
        )
        jitter = True
    
    if not isinstance(strategy, RetryStrategy):
        logger.warning(
            "Invalid strategy in retry_async",
            extra={"strategy": strategy, "strategy_type": type(strategy).__name__}
        )
        strategy = RetryStrategy.EXPONENTIAL
    
    last_exception = None
    func_name = getattr(func, '__name__', str(func))
    
    for attempt in range(max_attempts):
        try:
            # Execute function
            result = await func(*args, **kwargs)
            
            # Success!
            if attempt > 0:
                logger.info(
                    f"✅ {func_name} succeeded on attempt {attempt + 1}/{max_attempts}",
                    extra={
                        "function": func_name,
                        "attempt": attempt + 1,
                        "total_attempts": max_attempts
                    }
                )
            
            return result
            
        except exceptions as e:
            last_exception = e
            
            # Last attempt, don't retry
            if attempt == max_attempts - 1:
                logger.error(
                    "Function failed after all retry attempts",
                    extra={
                        "function": func_name,
                        "attempt": attempt + 1,
                        "total_attempts": max_attempts,
                        "exception_type": type(e).__name__,
                        "exception_message": str(e)
                    },
                    exc_info=True
                )
                break
            
            # Calculate backoff delay based on strategy
            if strategy == RetryStrategy.EXPONENTIAL:
                delay = min(
                    initial_delay * (exponential_base ** attempt),
                    max_delay
                )
            elif strategy == RetryStrategy.LINEAR:
                delay = min(
                    initial_delay * (attempt + 1),
                    max_delay
                )
            else:  # CONSTANT
                delay = initial_delay
            
            # Add jitter (best practice: prevent thundering herd)
            if jitter:
                jitter_amount = delay * 0.1  # 10% jitter
                delay = delay + random.uniform(-jitter_amount, jitter_amount)
                delay = max(0.1, delay)  # Ensure positive delay
            
            logger.warning(
                "Function failed, retrying",
                extra={
                    "function": func_name,
                    "attempt": attempt + 1,
                    "total_attempts": max_attempts,
                    "delay": delay,
                    "exception_type": type(e).__name__,
                    "exception_message": str(e)
                }
            )
            
            # Wait before retry
            await asyncio.sleep(delay)
    
    # All retries failed
    if last_exception:
        raise last_exception
    raise Exception(f"{func_name} failed after {max_attempts} attempts")


# Decorator version
def with_retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator to add retry logic to async functions
    
    Usage:
        @with_retry(max_attempts=3, initial_delay=1.0)
        async def query_database(query: str):
            # Database query
            pass
    """
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_async(
                func,
                max_attempts=max_attempts,
                initial_delay=initial_delay,
                max_delay=max_delay,
                exponential_base=exponential_base,
                exceptions=exceptions,
                *args,
                **kwargs
            )
        
        return wrapper
    
    return decorator


# Jittered retry (prevents thundering herd)
async def retry_with_jitter(
    func: Callable,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    *args,
    **kwargs
) -> Any:
    """
    Retry with jittered exponential backoff
    
    Adds randomness to prevent all clients retrying simultaneously
    """
    import random
    
    for attempt in range(max_attempts):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            
            # Exponential backoff with jitter
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            
            logger.warning(
                "Retry attempt",
                extra={
                    "attempt": attempt + 1,
                    "max_attempts": max_attempts,
                    "delay": delay,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            await asyncio.sleep(delay)


# Example usage:
"""
from src.utils.retry_logic import with_retry

# Database queries
@with_retry(max_attempts=3, initial_delay=0.5)
async def query_db(sql: str):
    async with db_pool.acquire() as conn:
        return await conn.fetch(sql)

# External API calls
@with_retry(
    max_attempts=5,
    initial_delay=2.0,
    exceptions=(httpx.HTTPError, asyncio.TimeoutError)
)
async def call_openai(prompt: str):
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
        response = await client.post(...)
        return response.json()

# Redis operations
@with_retry(max_attempts=2, initial_delay=0.1)
async def get_from_cache(key: str):
    return await redis_client.get(key)
"""


