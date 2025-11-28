# [NEXUS IDENTITY] ID: 6889335443723287297 | DATE: 2025-11-19

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx

from .exceptions import IntegrationConfigError, IntegrationError


class BaseIntegrationClient:
    """Common HTTP helper for integration clients."""

    def __init__(
        self,
        *,
        base_url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 10.0,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ) -> None:
        if not base_url:
            raise IntegrationConfigError(
                "Base URL is required for integration client.")
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers=headers or {},
            timeout=timeout,
            transport=transport,
        )

    async def _request(self, method: str, url: str, **
                       kwargs: Any) -> httpx.Response:
        try:
