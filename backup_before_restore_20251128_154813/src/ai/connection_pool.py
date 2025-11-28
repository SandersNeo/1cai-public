# [NEXUS IDENTITY] ID: 4028071011291707644 | DATE: 2025-11-19

"""
Connection Pool для AI Clients
-------------------------------

Пул соединений для переиспользования HTTP соединений между AI клиентами.
Улучшает производительность за счет переиспользования TCP соединений.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Optional

import aiohttp

logger = logging.getLogger(__name__)


class ConnectionPool:
    """
    Пул соединений для HTTP клиентов.

    Позволяет переиспользовать aiohttp.ClientSession между разными клиентами
    для улучшения производительности.
    """

    def __init__(self, max_size: int = 10, timeout: int = 60):
        """
        Инициализация пула соединений.

        Args:
            max_size: Максимальный размер пула
            timeout: Таймаут для соединений в секундах
        """
        self.max_size = max_size
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._sessions: Dict[str, aiohttp.ClientSession] = {}
        self._lock = asyncio.Lock()

    async def get_session(self, key: str) -> aiohttp.ClientSession:
        """
        Получить или создать HTTP сессию.

        Args:
            key: Ключ для идентификации сессии (например, URL провайдера)

        Returns:
            aiohttp.ClientSession
        """
        async with self._lock:
            if key not in self._sessions:
                # Если max_size > 0, проверяем переполнение
                if self.max_size > 0 and len(self._sessions) >= self.max_size:
                    # Закрываем старую сессию (FIFO)
                    oldest_key = next(iter(self._sessions))
                    old_session = self._sessions.pop(oldest_key)
                    if not old_session.closed:
                        try:
                            logger = logging.getLogger(__name__)
                            logger.error("Error in try block", exc_info=True)

                # Создаем новую сессию
                session = aiohttp.ClientSession(timeout=self.timeout)
                # Только если max_size > 0, добавляем в пул для
                # переиспользования
                if self.max_size > 0:
                    self._sessions[key] = session
                    logger.debug(
                        "Created new session in pool",
                        extra={"key": key, "pool_size": len(self._sessions)},
                    )
                else:
                    # При max_size=0 не сохраняем в пул (каждая сессия новая)
                    logger.debug(
                        "Created new session (pool disabled, max_size=0)",
                        extra={"key": key},
                    )
                    return session

            session = self._sessions[key]
            # Проверяем, закрыта ли сессия
            if hasattr(session, "closed") and session.closed:
                # Пересоздаем закрытую сессию
                try:
                    logger = logging.getLogger(__name__)
                    logger.error("Error in try block", exc_info=True)
                session = aiohttp.ClientSession(timeout=self.timeout)
                self._sessions[key] = session
                logger.debug(
                    "Recreated closed session in pool",
                    extra={
                        "key": key})

            return session

    @asynccontextmanager
    async def acquire(self, key: str):
        """
        Context manager для получения сессии из пула.

        Args:
            key: Ключ для идентификации сессии

        Yields:
            aiohttp.ClientSession
        """
        session = await self.get_session(key)
        try:
