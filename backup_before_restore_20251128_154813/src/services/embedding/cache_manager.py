import hashlib
import json
import os
from collections import OrderedDict
from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Dict, List, Optional, Union

import numpy as np

from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class CacheManager:
    """
    Manages L1 (Memory) and L2 (Redis) caching for embeddings.
    Also handles quantization/dequantization.
    """

    def __init__(
        self,
        redis_client=None,
        quantization_enabled: bool = False,
        quantization_dtype: str = "int8",
    ):
        self._cache_enabled = (
            os.getenv("EMBEDDING_CACHE_ENABLED", "true").lower() == "true"
        )
        self._cache_max_size = int(os.getenv("EMBEDDING_CACHE_SIZE", "1000"))
        self._cache_ttl_seconds = int(os.getenv("EMBEDDING_CACHE_TTL", "3600"))

        # L1: In-memory LRU cache
        self._result_cache: OrderedDict[str, Dict] = OrderedDict()
        self._cache_lock = Lock()

        # L2: Redis cache
        self._redis_client = redis_client
        self._redis_enabled = redis_client is not None
        if self._redis_enabled:
            try:
                logger = logging.getLogger(__name__)
                logger.error("Error in try block", exc_info=True)

        # Simple quantization fallback
        try:
