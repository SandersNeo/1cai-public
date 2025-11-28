# [NEXUS IDENTITY] ID: -4876162559593894968 | DATE: 2025-11-19

"""
Async client for YandexGPT API.

The client supports production usage when credentials are provided and gracefully
falls back when configuration is missing, allowing developers to rely on
heuristics locally.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import aiohttp

from .exceptions import LLMCallError, LLMNotConfiguredError

logger = logging.getLogger(__name__)


@dataclass
class YandexGPTConfig:
    base_url: str = os.getenv(
        "YANDEXGPT_API_URL", "https://llm.api.cloud.yandex.net/llm/v1alpha"
    )
    folder_id: Optional[str] = os.getenv("YANDEXGPT_FOLDER_ID")
    api_key: Optional[str] = os.getenv("YANDEXGPT_API_KEY")
    model_name: str = os.getenv("YANDEXGPT_MODEL", "yandexgpt/latest")
    verify_ssl: bool = os.getenv(
        "YANDEXGPT_VERIFY_SSL",
        "true").lower() != "false"


class YandexGPTClient:
    def __init__(self, config: Optional[YandexGPTConfig] = None):
        self.config = config or YandexGPTConfig()
        self._session: Optional[aiohttp.ClientSession] = None
        self._timeout = aiohttp.ClientTimeout(total=60)

    @property
    def is_configured(self) -> bool:
        return bool(self.config.api_key and self.config.folder_id)

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def __aenter__(self) -> "YandexGPTClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        system_prompt: Optional[str] = None,
        response_format: str = "text",
    ) -> Dict[str, Any]:
        if not self.is_configured:
            raise LLMNotConfiguredError(
                "YandexGPT credentials are not configured")

        session = await self._get_session()

        headers = {
            "Authorization": f"Api-Key {self.config.api_key}",
            "Content-Type": "application/json",
            "x-folder-id": self.config.folder_id,
        }

        messages = [{"role": "system",
                     "text": system_prompt or "Assistant for business analyst tasks.",
                     },
                    {"role": "user",
                     "text": prompt},
                    ]

        json_payload: Dict[str, Any] = {
            "modelUri": f"gpt://{self.config.folder_id}/{self.config.model_name}",
            "completionOptions": {
                "temperature": temperature,
                "maxTokens": max_tokens,
            },
            "messages": messages,
        }

        if response_format == "json":
            json_payload["completionOptions"]["stream"] = False
            json_payload["messages"][0]["text"] += "\nОтвет возвращай в формате JSON."

        try:
