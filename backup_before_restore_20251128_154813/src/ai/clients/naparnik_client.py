# [NEXUS IDENTITY] ID: -6408177600490684543 | DATE: 2025-11-19

"""
Asynchronous client for 1C:Напарник API.

1C:Напарник - это AI-помощник для разработчиков 1С, специализирующийся на работе
с конфигурациями и метаданными 1С:Enterprise.

The implementation is designed to work with the official REST API but falls back
gracefully when credentials are not provided. This allows local development
without network access while keeping the integration ready for production.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import aiohttp
from tenacity import (retry, retry_if_exception_type, stop_after_attempt,
                      wait_fixed)

from .exceptions import LLMCallError, LLMNotConfiguredError

logger = logging.getLogger(__name__)


@dataclass
class NaparnikConfig:
    """Configuration holder for 1C:Напарник client."""

    base_url: str = os.getenv(
        "NAPARNIK_API_URL", "https://naparnik.platform.1c.ru/api/v1"
    )
    api_key: Optional[str] = os.getenv("NAPARNIK_API_KEY")
    model_name: str = os.getenv("NAPARNIK_MODEL", "naparnik-pro")
    verify_ssl: bool = os.getenv(
        "NAPARNIK_VERIFY_SSL",
        "true").lower() != "false"
    timeout_seconds: int = int(os.getenv("NAPARNIK_TIMEOUT_SECONDS", "25"))


class NaparnikClient:
    """Async client for interacting with the 1C:Напарник API."""

    def __init__(self, config: Optional[NaparnikConfig] = None):
        self.config = config or NaparnikConfig()
        self._session: Optional[aiohttp.ClientSession] = None
        self._timeout = aiohttp.ClientTimeout(
            total=self.config.timeout_seconds)

    @property
    def is_configured(self) -> bool:
        """Returns True when we have enough data to perform API calls."""
        return bool(self.config.api_key)

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def __aenter__(self) -> "NaparnikClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        system_prompt: Optional[str] = None,
        response_format: str = "text",
    ) -> Dict[str, Any]:
        """
        Generates a completion from the 1C:Напарник model.

        Returns a dictionary with keys `text` and `usage`. When the client is
        not configured, a LLMNotConfiguredError is raised so callers can fall
        back to heuristic pipelines.
        """
        if not self.is_configured:
            raise LLMNotConfiguredError(
                "1C:Напарник credentials are not configured")

        session = await self._get_session()

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        # Default system prompt for 1C:Напарник
        default_system_prompt = (
            system_prompt or "Вы — эксперт-помощник для разработчиков 1С:Enterprise. "
            "Вы помогаете с разработкой, настройкой и оптимизацией конфигураций 1С.")

        messages = [
            {"role": "system", "content": default_system_prompt},
            {"role": "user", "content": prompt},
        ]

        payload: Dict[str, Any] = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_format == "json":
            payload["response_format"] = {"type": "json_object"}

        try:
