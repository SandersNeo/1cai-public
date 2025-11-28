import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Union

from src.config import USE_NESTED_LEARNING
from src.utils.circuit_breaker import CircuitState
from src.utils.structured_logging import StructuredLogger

from .cache_manager import CacheManager
from .model_manager import ModelManager
from .resource_manager import ResourceManager

logger = StructuredLogger(__name__).logger


class EmbeddingService:
    """
    Refactored EmbeddingService using composition.

    With Nested Learning support for continual learning (optional).
    """

    def __init__(
            self,
            model_name: str = None,
            hybrid_mode: bool = None,
            redis_client=None):
        self.model_manager = ModelManager(model_name, hybrid_mode)
        self.cache_manager = CacheManager(redis_client)
        self.resource_manager = ResourceManager()

        self.hybrid_mode = self.model_manager.hybrid_mode
        self._executor = ThreadPoolExecutor(
            max_workers=2) if self.hybrid_mode else None

        # Nested Learning integration (optional)
        self._nested = None
        if USE_NESTED_LEARNING:
            try:
