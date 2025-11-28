# [NEXUS IDENTITY] ID: -6115039186332115559 | DATE: 2025-11-19

"""
Qdrant Client wrapper used in tests and development.

Реализация не зависит от официального SDK: во время unit-тестов мы замещаем
`qdrant_client.QdrantClient` при помощи `unittest.mock`. Чтобы интеграция
оставалась прозрачной, класс ниже выполняет импорты лениво и не требует
наличия настоящей библиотеки в окружении.
"""

import importlib
import os
from typing import Any, Dict, List, Optional

from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class QdrantClient:
    """Минималистичная обертка над Qdrant SDK."""

    COLLECTION_CODE = "1c_code"
    COLLECTION_DOCS = "1c_documentation"
    VECTOR_SIZE = 384

    def __init__(
            self,
            host: str = "localhost",
            port: int = 6333,
            api_key: Optional[str] = None):
        """Initialize Qdrant client с input validation"""
        # Input validation
        if not isinstance(host, str) or not host:
            logger.warning(
                "Invalid host in QdrantClient.__init__",
                extra={"host": host, "host_type": type(host).__name__},
            )
            host = "localhost"

        if not isinstance(port, int) or port < 1 or port > 65535:
            logger.warning(
                "Invalid port in QdrantClient.__init__",
                extra={"port": port, "port_type": type(port).__name__},
            )
            port = 6333

        if api_key is not None and not isinstance(api_key, str):
            logger.warning(
                "Invalid api_key type in QdrantClient.__init__",
                extra={"api_key_type": type(api_key).__name__},
            )
            api_key = None

        self.host = host
        self.port = port
        self.api_key = api_key or os.getenv("QDRANT_API_KEY")
        self.client: Optional[Any] = None

        logger.debug(
            "QdrantClient initialized",
            extra={
                "host": host,
                "port": port,
                "has_api_key": bool(
                    self.api_key)},
        )

    def _load_sdk(self):
        """Импортирует модуль `qdrant_client` в момент обращения."""
        return importlib.import_module("qdrant_client")

    def connect(self, max_retries: int = 3, retry_delay: float = 1.0) -> bool:
        """
        Connect to Qdrant with retry logic с input validation

        Best practices:
        - Retry для transient errors
        - Exponential backoff
        - Structured logging
        """
        # Input validation
        if not isinstance(max_retries, int) or max_retries < 1:
            logger.warning(
                "Invalid max_retries in QdrantClient.connect",
                extra={
                    "max_retries": max_retries,
                    "max_retries_type": type(max_retries).__name__,
                },
            )
            max_retries = 3

        if not isinstance(retry_delay, (int, float)) or retry_delay < 0:
            logger.warning(
                "Invalid retry_delay in QdrantClient.connect",
                extra={
                    "retry_delay": retry_delay,
                    "retry_delay_type": type(retry_delay).__name__,
                },
            )
            retry_delay = 1.0

        import time

        for attempt in range(max_retries):
            try:
