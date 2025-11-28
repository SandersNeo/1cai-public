# [NEXUS IDENTITY] ID: 7411858915040180267 | DATE: 2025-11-19

"""
Universal Ollama Client
-----------------------

Универсальный клиент для работы с локальными моделями через Ollama.
Поддерживает различные модели: llama3, mistral, codellama, qwen и другие.
"""

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import aiohttp
from tenacity import (retry, retry_if_exception_type, stop_after_attempt,
                      wait_fixed)

from .exceptions import LLMCallError, LLMNotConfiguredError

logger = logging.getLogger(__name__)


@dataclass
class OllamaConfig:
    """Конфигурация Ollama клиента."""

    base_url: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    model_name: str = os.getenv("OLLAMA_MODEL", "llama3")
    timeout: int = int(os.getenv("OLLAMA_TIMEOUT", "60"))
    verify_ssl: bool = os.getenv(
        "OLLAMA_VERIFY_SSL",
        "true").lower() != "false"
    max_retries: int = 3


class OllamaClient:
    """
    Универсальный клиент для работы с Ollama моделями.

    Поддерживает различные модели:
    - llama3, llama3.1, llama3.2
    - mistral, mistral:7b
    - codellama, codellama:7b
    - qwen2.5-coder, qwen2.5:7b
    - и другие модели Ollama
    """

    def __init__(self, config: Optional[OllamaConfig] = None):
        """
        Инициализация Ollama клиента.

        Args:
            config: Конфигурация клиента. Если не указана, используется конфигурация из env.
        """
        self.config = config or OllamaConfig()
        self._session: Optional[aiohttp.ClientSession] = None
        self._timeout = aiohttp.ClientTimeout(total=self.config.timeout)

    @property
    def is_configured(self) -> bool:
        """Проверка, настроен ли клиент."""
        return bool(self.config.base_url)

    async def close(self) -> None:
        """Закрыть HTTP сессию."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def __aenter__(self) -> "OllamaClient":
        """Context manager вход."""
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        """Context manager выход."""
        await self.close()

    async def list_models(self) -> List[str]:
        """
        Получить список доступных моделей в Ollama.

        Returns:
            Список названий моделей.

        Raises:
            LLMNotConfiguredError: Если Ollama не настроен
            LLMCallError: Если запрос не удался
        """
        if not self.is_configured:
            raise LLMNotConfiguredError("Ollama URL is not configured")

        session = await self._get_session()
        try:
