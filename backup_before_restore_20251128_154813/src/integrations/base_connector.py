"""
Base connector for external integrations.

Provides common functionality for all integration connectors:
- Retry logic with exponential backoff
- Error handling and logging
- Authentication management
- Request/response logging for audit
- Dead Letter Queue (DLQ) for failed operations
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, TypeVar

import httpx
from tenacity import (before_sleep_log, retry, retry_if_exception_type,
                      stop_after_attempt, wait_exponential)

logger = logging.getLogger(__name__)

T = TypeVar('T')


class IntegrationStatus(Enum):
    """Integration operation status."""
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"
    DLQ = "dlq"  # Dead Letter Queue


class BaseConnector(ABC):
    """
    Base class for all external integration connectors.

    Provides:
    - HTTP client with retry logic
    - Authentication management
    - Audit logging
    - Error handling
    - Dead Letter Queue (DLQ)
    """

    def __init__(
        self,
        base_url: str,
        auth_token: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        **kwargs
    ):
        """
        Initialize base connector.

        Args:
            base_url: Base URL for the integration API
            auth_token: Authentication token (Bearer, API key, etc.)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.timeout = timeout
        self.max_retries = max_retries

        # HTTP client
        self._client: Optional[httpx.AsyncClient] = None

        # Audit log
        self.audit_log: list[Dict[str, Any]] = []

        # Dead Letter Queue
        self.dlq: list[Dict[str, Any]] = []

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self):
        """Initialize HTTP client."""
        if self._client is None:
            headers = self._get_headers()
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=self.timeout
            )
            logger.info("Connected to {self.base_url}")

    async def disconnect(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("Disconnected from {self.base_url}")

    def _get_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers for requests.

        Override in subclasses for custom authentication.
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        return headers

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, asyncio.TimeoutError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> httpx.Response:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (relative to base_url)
            **kwargs: Additional arguments for httpx.request

        Returns:
            HTTP response

        Raises:
            httpx.HTTPError: On HTTP errors after retries
        """
        if not self._client:
            await self.connect()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        # Log request
        self._log_request(method, url, kwargs)

        try:
