# [NEXUS IDENTITY] ID: 3630778346350459119 | DATE: 2025-11-19

"""
Traffic Shaper - Формирование трафика для обхода DPI
Версия: 1.0.0

Формирование трафика для имитации легитимного и обхода DPI.
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

try:
    from src.monitoring.prometheus_metrics import (
        traffic_shaping_delay_seconds,
        traffic_shaping_operations_total,
    )
except ImportError:
    traffic_shaping_operations_total = None
    traffic_shaping_delay_seconds = None

logger = logging.getLogger(__name__)


@dataclass
class TrafficShapeConfig:
    """Конфигурация формирования трафика"""

    packet_sizes: List[int] = None  # Типичные размеры пакетов
    delay_range: Tuple[float, float] = (0.01, 0.1)  # Случайные задержки в секундах
    jitter_range: Tuple[float, float] = (0.0, 0.02)  # Джиттер для задержек
    enable_randomization: bool = True  # Случайные задержки
    chunk_size: int = 1500  # Размер чанков по умолчанию

    def __post_init__(self):
        if self.packet_sizes is None:
            self.packet_sizes = [512, 1024, 1500, 2048]  # Типичные размеры


class TrafficShaper:
    """
    Формирование трафика для обхода DPI.

    Особенности:
    - Изменение размера пакетов
    - Добавление случайных задержек
    - Имитация паттернов браузера
    - Смешивание с легитимным трафиком
    """

    def __init__(self, config: Optional[TrafficShapeConfig] = None):
        self.config = config or TrafficShapeConfig()

    async def send_with_shaping(
        self, data: bytes, send_func: Callable, *args, **kwargs
    ) -> None:
        """
        Отправить данные с формированием трафика.

        Args:
            data: Данные для отправки
            send_func: Функция отправки (socket.send, etc.)
            *args: Аргументы функции
            **kwargs: Ключевые аргументы функции
        """
        start_time = time.time()

        try:
            # Разбиваем данные на чанки
            chunks = self._chunk_data(data)

            for chunk in chunks:
                # Отправляем чанк
                await send_func(chunk, *args, **kwargs)

                # Случайная задержка
                if self.config.enable_randomization:
                    delay = self._calculate_delay()
                    await asyncio.sleep(delay)

            # Обновляем метрики
            duration = time.time() - start_time
            if traffic_shaping_operations_total:
                traffic_shaping_operations_total.labels(
                    operation_type="send", status="success"
                ).inc()
            if traffic_shaping_delay_seconds:
                traffic_shaping_delay_seconds.labels(operation_type="send").observe(
                    duration
                )

        except Exception as e:
            logger.warning("Traffic shaping failed: %s", e)
            if traffic_shaping_operations_total:
                traffic_shaping_operations_total.labels(
                    operation_type="send", status="error"
                ).inc()
            raise

    def _chunk_data(self, data: bytes) -> List[bytes]:
        """Разбить данные на чанки случайного размера"""
        chunks = []
        offset = 0

        while offset < len(data):
            # Выбираем случайный размер пакета
            if self.config.enable_randomization:
                chunk_size = random.choice(self.config.packet_sizes)
                # Ограничиваем размер оставшимися данными
                chunk_size = min(chunk_size, len(data) - offset)
            else:
                chunk_size = min(self.config.chunk_size, len(data) - offset)

            chunk = data[offset : offset + chunk_size]
            chunks.append(chunk)
            offset += chunk_size

        return chunks

    def _calculate_delay(self) -> float:
        """Вычислить задержку с джиттером"""
        base_delay = random.uniform(*self.config.delay_range)
        jitter = random.uniform(*self.config.jitter_range)
        return base_delay + jitter

    def shape_http_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """
        Формировать HTTP заголовки для имитации браузера.

        Args:
            headers: Исходные заголовки

        Returns:
            Сформированные заголовки
        """
        # Добавляем типичные заголовки браузера
        shaped_headers = headers.copy()

        # User-Agent (если не указан)
        if "User-Agent" not in shaped_headers:
            shaped_headers["User-Agent"] = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )

        # Accept заголовки
        if "Accept" not in shaped_headers:
            shaped_headers["Accept"] = (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/webp,*/*;q=0.8"
            )

        # Accept-Language
        if "Accept-Language" not in shaped_headers:
            shaped_headers["Accept-Language"] = "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"

        # Accept-Encoding
        if "Accept-Encoding" not in shaped_headers:
            shaped_headers["Accept-Encoding"] = "gzip, deflate, br"

        # Connection
        if "Connection" not in shaped_headers:
            shaped_headers["Connection"] = "keep-alive"

        return shaped_headers

    def add_random_padding(self, data: bytes, max_padding: int = 64) -> bytes:
        """
        Добавить случайный padding к данным.

        Args:
            data: Исходные данные
            max_padding: Максимальный размер padding

        Returns:
            Данные с padding
        """
        if not self.config.enable_randomization:
            return data

        padding_size = random.randint(0, max_padding)
        padding = bytes(random.randint(0, 255) for _ in range(padding_size))

        return data + padding
