# [NEXUS IDENTITY] ID: 3469964817106375621 | DATE: 2025-11-19

"""
Asynchronous client for GigaChat (Sber Devices) LLM.

The implementation is designed to work with the official REST API but falls back
gracefully when credentials are not provided. This allows local development
without network access while keeping the integration ready for production.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import aiohttp
from tenacity import (retry, retry_if_exception_type, stop_after_attempt,
                      wait_fixed)

from .exceptions import LLMCallError, LLMNotConfiguredError

logger = logging.getLogger(__name__)


@dataclass
class GigaChatConfig:
    """Configuration holder for GigaChat client."""

    base_url: str = os.getenv(
        "GIGACHAT_API_URL", "https://gigachat.devices.sberbank.ru/api/v1"
    )
    token_url: str = os.getenv(
        "GIGACHAT_TOKEN_URL",
        "https://ngw.devices.sberbank.ru:9443/api/v2/oauth")
    scope: str = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
    client_id: Optional[str] = os.getenv("GIGACHAT_CLIENT_ID")
    client_secret: Optional[str] = os.getenv("GIGACHAT_CLIENT_SECRET")
    access_token: Optional[str] = os.getenv("GIGACHAT_ACCESS_TOKEN")
    verify_ssl: bool = os.getenv(
        "GIGACHAT_VERIFY_SSL",
        "true").lower() != "false"


class GigaChatClient:
    """Async client for interacting with the GigaChat API."""

    def __init__(self, config: Optional[GigaChatConfig] = None):
        self.config = config or GigaChatConfig()
        self._access_token: Optional[str] = self.config.access_token
        self._token_expires_at: float = 0.0
        self._session: Optional[aiohttp.ClientSession] = None
        self._timeout = aiohttp.ClientTimeout(total=60)

    @property
    def is_configured(self) -> bool:
        """Returns True when we have enough data to perform API calls."""
        return bool(
            self._access_token
            or (
                self.config.client_id
                and self.config.client_secret
                and self.config.token_url
            )
        )

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def __aenter__(self) -> "GigaChatClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.3,
        max_tokens: int = 1024,
        system_prompt: Optional[str] = None,
        response_format: str = "text",
    ) -> Dict[str, Any]:
        """
        Generates a completion from the GigaChat model.

        Returns a dictionary with keys `text` and `usage`. When the client is
        not configured, a LLMNotConfiguredError is raised so callers can fall
        back to heuristic pipelines.
        """
        if not self.is_configured:
            raise LLMNotConfiguredError(
                "GigaChat credentials are not configured")

        await self._ensure_token()

        payload = {
            "model": "GigaChat",
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt or "Ты помогатель аналитика.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        params = {}
        if response_format == "json":
            params["response_format"] = {"type": "json_object"}

        json_payload = {**payload, **params}

        session = await self._get_session()
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

        try:
