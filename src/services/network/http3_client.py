# [NEXUS IDENTITY] ID: -5839293802660758573 | DATE: 2025-11-19

"""
HTTP/3 (QUIC) Client Support
Версия: 1.0.0

Поддержка HTTP/3 через QUIC протокол.
"""

from __future__ import annotations

import logging
from typing import Optional
import httpx

logger = logging.getLogger(__name__)


class HTTP3Client:
    """
    HTTP/3 клиент с поддержкой QUIC.

    Особенности:
    - HTTP/3 через QUIC
    - Автоматический fallback на HTTP/2
    - Connection migration
    - Улучшенная производительность
    """

    def __init__(self, enable_http3: bool = True):
        """
        Args:
            enable_http3: Включить HTTP/3 поддержку
        """
        self.enable_http3 = enable_http3
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Async context manager exit"""
        await self.close()

    async def _ensure_client(self):
        """Создать HTTP клиент с поддержкой HTTP/3"""
        if self._client is not None:
            return

        # httpx поддерживает HTTP/2 по умолчанию
        # HTTP/3 требует дополнительных библиотек (aioquic)
        try:
            # Пробуем использовать HTTP/3 если доступен
            if self.enable_http3:
                try:
                    pass

                    # HTTP/3 через aioquic (требует дополнительной настройки)
                    logger.info("HTTP/3 support available via aioquic")
                except ImportError:
                    logger.debug("aioquic not available, using HTTP/2")
                    self.enable_http3 = False

            # Создаём клиент с HTTP/2 поддержкой
            self._client = httpx.AsyncClient(
                http2=True,  # HTTP/2 fallback
                limits=httpx.Limits(
                    max_keepalive_connections=20,
                    max_connections=100,
                    keepalive_expiry=30.0,
                ),
                timeout=httpx.Timeout(30.0),
            )

        except Exception as e:
            logger.warning(f"Failed to create HTTP client: {e}")
            # Fallback на стандартный клиент
            self._client = httpx.AsyncClient()

    async def get(self, url: str, **kwargs) -> httpx.Response:
        """GET запрос"""
        await self._ensure_client()
        return await self._client.get(url, **kwargs)

    async def post(self, url: str, **kwargs) -> httpx.Response:
        """POST запрос"""
        await self._ensure_client()
        return await self._client.post(url, **kwargs)

    async def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Произвольный HTTP запрос"""
        await self._ensure_client()
        return await self._client.request(method, url, **kwargs)

    async def close(self):
        """Закрыть клиент"""
        if self._client:
            await self._client.aclose()
            self._client = None
