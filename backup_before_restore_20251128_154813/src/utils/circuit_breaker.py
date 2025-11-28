# [NEXUS IDENTITY] ID: 3406744695516042437 | DATE: 2025-11-19

"""
Circuit Breaker Pattern Implementation
Версия: 2.1.0

Улучшения:
- Structured logging
- Улучшена обработка ошибок

TIER 1 Improvement: Prevents cascade failures
"""

import time
from enum import Enum
from functools import wraps
from typing import Any, Callable

from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


class CircuitBreaker:
    """
    Circuit Breaker pattern implementation

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, reject requests immediately
    - HALF_OPEN: Allow test request to check if service recovered

    Example:
        cb = CircuitBreaker(failure_threshold=5, timeout=60)

        result = await cb.call(external_api_function, arg1, arg2)
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
    ):
        # Input validation
        if not isinstance(failure_threshold, int) or failure_threshold < 1:
            logger.warning(
                "Invalid failure_threshold in CircuitBreaker.__init__",
                extra={
                    "failure_threshold": failure_threshold,
                    "failure_threshold_type": type(failure_threshold).__name__,
                },
            )
            failure_threshold = 5  # Default

        if not isinstance(recovery_timeout, int) or recovery_timeout < 1:
            logger.warning(
                "Invalid recovery_timeout in CircuitBreaker.__init__",
                extra={
                    "recovery_timeout": recovery_timeout,
                    "recovery_timeout_type": type(recovery_timeout).__name__,
                },
            )
            recovery_timeout = 60  # Default

        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

        logger.debug(
            "CircuitBreaker initialized",
            extra={
                "failure_threshold": failure_threshold,
                "recovery_timeout": recovery_timeout,
            },
        )

    def _should_attempt_reset(self) -> bool:
        """Check if should try to recover"""
        return (
            self.state == CircuitState.OPEN
            and self.last_failure_time
            and time.time() - self.last_failure_time >= self.recovery_timeout
        )

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection с input validation"""
        # Input validation
        if not callable(func):
            logger.warning(
                "Invalid func in CircuitBreaker.call",
                extra={"func_type": type(func).__name__},
            )
            raise ValueError("func must be callable")

        func_name = getattr(func, "__name__", str(func))

        # Check if should attempt recovery
        if self._should_attempt_reset():
            self.state = CircuitState.HALF_OPEN
            logger.info(
                "Circuit breaker entering HALF_OPEN state",
                extra={
                    "function": func_name,
                    "state": "HALF_OPEN",
                    "failure_count": self.failure_count,
                },
            )

        # If circuit is OPEN, reject immediately
        if self.state == CircuitState.OPEN:
            logger.warning(
                "Circuit breaker OPEN, rejecting request",
                extra={
                    "function": func_name,
                    "state": "OPEN",
                    "failure_count": self.failure_count,
                },
            )
            raise Exception(
                f"Circuit breaker is OPEN for {func_name}. Service unavailable."
            )

        try:
