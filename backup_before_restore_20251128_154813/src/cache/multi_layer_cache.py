# Обратная совместимость - реэкспорт из нового расположения
from src.infrastructure.cache.multi_layer import (
    CircuitBreaker,
    LRUCache,
    MultiLayerCache,
    generate_cache_key)

__all__ = [
    "LRUCache",
    "CircuitBreaker",
    "MultiLayerCache",
    "generate_cache_key"]
