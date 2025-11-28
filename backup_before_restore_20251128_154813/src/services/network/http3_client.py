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
