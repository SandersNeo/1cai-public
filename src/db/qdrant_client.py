"""
Qdrant Client wrapper used in tests and development.

Реализация не зависит от официального SDK: во время unit-тестов мы замещаем
`qdrant_client.QdrantClient` при помощи `unittest.mock`. Чтобы интеграция
оставалась прозрачной, класс ниже выполняет импорты лениво и не требует
наличия настоящей библиотеки в окружении.
"""

import importlib
import logging
import os
from typing import Any, Dict, List, Optional

from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class QdrantClient:
    """Минималистичная обертка над Qdrant SDK."""

    COLLECTION_CODE = "1c_code"
    COLLECTION_DOCS = "1c_documentation"
    VECTOR_SIZE = 384

    def __init__(self, host: str = "localhost", port: int = 6333, api_key: Optional[str] = None):
        """Initialize Qdrant client с input validation"""
        # Input validation
        if not isinstance(host, str) or not host:
            logger.warning(
                "Invalid host in QdrantClient.__init__",
                extra={"host": host, "host_type": type(host).__name__}
            )
            host = "localhost"
        
        if not isinstance(port, int) or port < 1 or port > 65535:
            logger.warning(
                "Invalid port in QdrantClient.__init__",
                extra={"port": port, "port_type": type(port).__name__}
            )
            port = 6333
        
        if api_key is not None and not isinstance(api_key, str):
            logger.warning(
                "Invalid api_key type in QdrantClient.__init__",
                extra={"api_key_type": type(api_key).__name__}
            )
            api_key = None
        
        self.host = host
        self.port = port
        self.api_key = api_key or os.getenv("QDRANT_API_KEY")
        self.client: Optional[Any] = None
        
        logger.debug(
            "QdrantClient initialized",
            extra={"host": host, "port": port, "has_api_key": bool(self.api_key)}
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
                extra={"max_retries": max_retries, "max_retries_type": type(max_retries).__name__}
            )
            max_retries = 3
        
        if not isinstance(retry_delay, (int, float)) or retry_delay < 0:
            logger.warning(
                "Invalid retry_delay in QdrantClient.connect",
                extra={"retry_delay": retry_delay, "retry_delay_type": type(retry_delay).__name__}
            )
            retry_delay = 1.0
        
        import time
        
        for attempt in range(max_retries):
            try:
                sdk = self._load_sdk()
                client_cls = getattr(sdk, "QdrantClient")
                self.client = client_cls(host=self.host, port=self.port, api_key=self.api_key)
                self.client.get_collections()
                logger.info(
                    "Connected to Qdrant at %s:%s",
                    self.host,
                    self.port,
                    extra={
                        "host": self.host,
                        "port": self.port,
                        "attempt": attempt + 1
                    }
                )
                return True
            except Exception as exc:  # noqa: BLE001
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(
                        "Failed to connect to Qdrant, retrying",
                        extra={
                            "host": self.host,
                            "port": self.port,
                            "attempt": attempt + 1,
                            "max_retries": max_retries,
                            "error": str(exc),
                            "wait_time": wait_time
                        }
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(
                        "Failed to connect to Qdrant after all attempts",
                        exc_info=True,
                        extra={
                            "host": self.host,
                            "port": self.port,
                            "max_retries": max_retries,
                            "error": str(exc)
                        }
                    )
                    return False
        
        return False

    def create_collections(self) -> None:
        if not self.client:
            raise RuntimeError("Qdrant client is not connected")

        try:
            vectors_config = {"size": self.VECTOR_SIZE, "distance": "Cosine"}
            self.client.recreate_collection(collection_name=self.COLLECTION_CODE, vectors_config=vectors_config)
            self.client.recreate_collection(collection_name=self.COLLECTION_DOCS, vectors_config=vectors_config)
        except Exception as exc:  # noqa: BLE001
            logger.error("Error creating collections: %s", exc)

    def add_code(self, code_id: str, embedding: List[float], metadata: Dict[str, Any]) -> bool:
        if not self.client:
            raise RuntimeError("Qdrant client is not connected")

        try:
            point = {"id": code_id, "vector": embedding, "payload": metadata}
            self.client.upsert(collection_name=self.COLLECTION_CODE, points=[point])
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("Error adding code: %s", exc)
            return False

    def search_code(
        self,
        query_vector: List[float],
        config_filter: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        if not self.client:
            raise RuntimeError("Qdrant client is not connected")

        try:
            kwargs = {
                "collection_name": self.COLLECTION_CODE,
                "query_vector": query_vector,
                "limit": limit,
            }
            if config_filter:
                kwargs["query_filter"] = {"must": [{"key": "configuration", "match": {"value": config_filter}}]}

            hits = self.client.search(**kwargs)
            return [{"id": hit.id, "score": hit.score, "payload": hit.payload} for hit in hits]
        except Exception as exc:  # noqa: BLE001
            logger.error("Error searching code: %s", exc)
            return []

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Qdrant SDK не требует явного закрытия соединения
        return False
