# [NEXUS IDENTITY] ID: -1024636934194263836 | DATE: 2025-11-19

"""
Cache package для 1C MCP сервера

Пакет для кэширования результатов MCP tools, метаданных и агрегированных данных, а также HTTP кэширование с ETag.

Основные компоненты:
- MCPToolsCache: основной класс кэширования
- CacheStrategy: стратегии кэширования (LRU, TTL-based)
- CacheInvalidation: механизмы инвалидации
- PersistentCache: долговременное кэширование на диске
- HTTP кэширование с ETag:
  * ETagManager - генерация и валидация ETag
  * HTTPCacheMiddleware - middleware для FastAPI
  * CacheHeaders - управление Cache-Control заголовками
  * ConditionalGET - обработка If-None-Match запросов
  * HTTP 304 Not Modified ответы
  * Метрики производительности кэша

Примеры использования:

    # HTTP кэширование
    from cache import setup_cache_middleware
    
    # Инициализация кэша
    cache = init_cache(
        max_size_mb=100,
        default_ttl_stable=30 * 60,  # 30 минут
        default_ttl_dynamic=5 * 60,  # 5 минут
        persistent_cache_dir="./cache_data"
    )
    
    # Настройка HTTP кэширования для FastAPI
    cache_middleware = setup_cache_middleware(
        app=app,
        cache_ttl=3600,
        max_cache_size=1000
    )
    
    # Декоратор для кэширования функций
    @cached(ttl=300, data_type='dynamic')
    def expensive_operation(param1, param2):
        # Дорогостоящая операция
        return result
    
    # Кэширование результатов MCP tools
    cache_tool_result("get_nomenclature", {"id": 123}, nomenclature_data)

Версия: 2.0.0
"""

from .mcp_cache import (
    MCPToolsCache,
    CacheStrategy,
    LRUStrategy,
    TTLCacheStrategy,
    CacheInvalidation,
    PersistentCache,
    CacheEntry as MCPCacheEntry,
    CacheMetrics as MCPCacheMetrics,
    get_cache,
    init_cache,
    cached,
    cached_async,
    cache_tool_result,
    get_cached_tool_result,
    cache_metadata_1c,
    get_cached_metadata_1c,
    cache_aggregates,
    get_cached_aggregates,
    get_cache_stats,
    cleanup_expired
)

from .http_cache import (
    ETagManager,
    CacheHeaders,
    ConditionalGET,
    HTTPCacheMiddleware,
    CacheMetrics as HTTPCacheMetrics,
    CacheEntry as HTTPCacheEntry,
    CacheMetricsCollector,
    setup_cache_middleware,
    metrics_collector
)

__version__ = "2.0.0"
__author__ = "1C MCP Server Team"

__all__ = [
    # MCP кэширование
    'MCPToolsCache',
    'CacheStrategy',
    'LRUStrategy',
    'TTLCacheStrategy',
    'CacheInvalidation',
    'PersistentCache',
    'MCPCacheEntry',
    'MCPCacheMetrics',
    'get_cache',
    'init_cache',
    'cached',
    'cached_async',
    'cache_tool_result',
    'get_cached_tool_result',
    'cache_metadata_1c',
    'get_cached_metadata_1c',
    'cache_aggregates',
    'get_cached_aggregates',
    'get_cache_stats',
    'cleanup_expired',
    
    # HTTP кэширование с ETag
    'ETagManager',
    'CacheHeaders',
    'ConditionalGET',
    'HTTPCacheMiddleware',
    'HTTPCacheMetrics',
    'HTTPCacheEntry',
    'CacheMetricsCollector',
    'setup_cache_middleware',
    'metrics_collector'
]
