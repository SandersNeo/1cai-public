# [NEXUS IDENTITY] ID: -9069577396218547301 | DATE: 2025-11-19

"""
Пример интеграции HTTP кэширования с ETag в существующий FastAPI сервер.

Демонстрирует:
1. Настройку middleware для FastAPI приложения
2. Интеграцию с существующей OAuth2 авторизацией
3. Использование различных стратегий кэширования
4. Мониторинг метрик кэша

Основан на архитектуре из src/py_server/main.py и src/py_server/http_server.py
"""

import logging
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse

from .http_cache import (CacheHeaders, metrics_collector, setup_cache_middleware)

logger = logging.getLogger(__name__)


def create_cached_fastapi_app(
    base_app: Optional[FastAPI] = None,
    cache_config: Optional[Dict[str, Any]] = None
) -> FastAPI:
    """
    Создает FastAPI приложение с настроенным HTTP кэшированием.
    
    Args:
        base_app: Базовое приложение для расширения
        cache_config: Конфигурация кэширования
        
    Returns:
        FastAPI приложение с кэшированием
    """
    # Конфигурация кэширования по умолчанию
    default_cache_config = {
        "secret_key": "mcp_server_secret_2024",
        "cache_ttl": 3600,  # 1 час
        "max_cache_size": 1000,
        "excluded_paths": {
            "/health",
            "/info",
            "/token",
            "/authorize", 
            "/register"
        }
    }
    
    # Обновляем конфигурацию
    if cache_config:
        default_cache_config.update(cache_config)
    
    cache_config = default_cache_config
    
    # Создаем или используем базовое приложение
    if base_app is None:
        app = FastAPI(
            title="MCP Server with HTTP Cache",
            description="MCP-прокси сервер с HTTP кэшированием",
            version="2.0.0"
        )
    else:
        app = base_app
    
    # Настраиваем HTTP кэширование
    cache_middleware = setup_cache_middleware(
        app=app,
        secret_key=cache_config["secret_key"],
        cache_ttl=cache_config["cache_ttl"],
        max_cache_size=cache_config["max_cache_size"],
        excluded_paths=cache_config["excluded_paths"]
    )
    
    # Добавляем дополнительные endpoints для управления кэшем
    @app.get("/cache/admin/stats")
    async def get_cache_admin_stats():
        """Подробная статистика кэша для администраторов."""
        return metrics_collector.get_summary()
    
    @app.post("/cache/admin/clear")
    async def clear_cache():
        """Очистка всего кэша."""
        for middleware in metrics_collector.middlewares:
            middleware._cache.clear()
            middleware._cache_order.clear()
        
        logger.info("Cache cleared by admin request")
        return {"status": "cleared", "message": "All cache entries removed"}
    
    @app.get("/cache/admin/export")
    async def export_cache_metrics():
        """Экспорт метрик для внешних систем мониторинга."""
        return {
            "prometheus_format": metrics_collector.export_prometheus(),
            "json_format": metrics_collector.get_summary()
        }
    
    return app


def create_content_specific_cache_strategies() -> Dict[str, Dict[str, Any]]:
    """
    Создает стратегии кэширования для разных типов контента.
    
    Returns:
        Словарь с конфигурациями для разных типов контента
    """
    return {
        # Статические ресурсы (справочники, редко изменяющиеся данные)
        "static_data": {
            "max_age": 86400,  # 24 часа
            "s_maxage": 43200,  # 12 часов для CDN
            "immutable": True,
            "public": True
        },
        
        # Часто изменяющиеся данные (документы, оперативные данные)
        "dynamic_data": {
            "max_age": 300,  # 5 минут
            "s_maxage": 60,  # 1 минута для CDN
            "stale_while_revalidate": 30,
            "stale_if_error": 300,
            "public": True
        },
        
        # Персонализированные данные (зависят от пользователя)
        "personal_data": {
            "max_age": 1800,  # 30 минут
            "private": True,
            "no_cache": False
        },
        
        # API данные с высокой нагрузкой
        "api_data": {
            "max_age": 180,  # 3 минуты
            "s_maxage": 30,  # 30 секунд для CDN
            "stale_while_revalidate": 60,
            "stale_if_error": 600,
            "public": True
        }
    }


def apply_content_specific_headers(
    response: Response,
    content_type: str,
    data_type: str
) -> Response:
    """
    Применяет специфичные заголовки кэширования для типа контента.
    
    Args:
        response: HTTP ответ
        content_type: Тип контента
        data_type: Тип данных для определения стратегии
        
    Returns:
        Обновленный HTTP ответ
    """
    strategies = create_content_specific_cache_strategies()
    
    if data_type not in strategies:
        data_type = "api_data"  # Дефолтная стратегия
    
    strategy = strategies[data_type]
    
    # Создаем Cache-Control заголовок
    cache_control = CacheHeaders.create_cache_control(
        public=strategy.get("public", False),
        private=strategy.get("private", False),
        max_age=strategy.get("max_age"),
        s_maxage=strategy.get("s_maxage"),
        no_cache=strategy.get("no_cache", False),
        immutable=strategy.get("immutable", False),
        stale_while_revalidate=strategy.get("stale_while_revalidate"),
        stale_if_error=strategy.get("stale_if_error")
    )
    
    response.headers["Cache-Control"] = cache_control
    
    # Добавляем X-Content-Type для отладки
    response.headers["X-Content-Strategy"] = data_type
    
    return response


def create_cached_mcp_endpoints(app: FastAPI, config: Dict[str, Any]) -> None:
    """
    Создает MCP endpoints с кэшированием.
    
    Args:
        app: FastAPI приложение
        config: Конфигурация сервера
    """
    
    @app.get("/mcp/cached/health")
    async def cached_health_check():
        """Кэшируемая проверка здоровья сервера."""
        return {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",
            "version": "2.0.0",
            "cache_enabled": True
        }
    
    @app.get("/mcp/cached/info")
    async def cached_server_info():
        """Кэшируемая информация о сервере."""
        return {
            "name": "MCP Server with HTTP Cache",
            "version": "2.0.0",
            "description": "MCP-прокси сервер с HTTP кэшированием и ETag",
            "features": [
                "HTTP caching with ETag",
                "Conditional GET requests",
                "Cache metrics and monitoring",
                "Multiple cache strategies",
                "FastAPI middleware integration"
            ],
            "cache_stats": metrics_collector.get_summary()
        }
    
    @app.get("/mcp/cached/metadata/{entity_type}")
    async def get_cached_metadata(entity_type: str):
        """Кэшируемые метаданные 1С."""
        # Имитация получения метаданных
        metadata = {
            "entity_type": entity_type,
            "fields": [
                {"name": "id", "type": "string", "required": True},
                {"name": "name", "type": "string", "required": True},
                {"name": "code", "type": "string", "required": False}
            ],
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        return apply_content_specific_headers(
            JSONResponse(content=metadata),
            content_type="application/json",
            data_type="static_data"
        )
    
    @app.get("/mcp/cached/data/{entity_type}/{id}")
    async def get_cached_entity_data(entity_type: str, id: str):
        """Кэшируемые данные сущности."""
        # Имитация получения данных
        data = {
            "entity_type": entity_type,
            "id": id,
            "name": f"Entity {id}",
            "code": f"CODE_{id}",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        
        return apply_content_specific_headers(
            JSONResponse(content=data),
            content_type="application/json", 
            data_type="dynamic_data"
        )


def integrate_with_existing_server():
    """
    Интеграция с существующим MCP сервером.
    
    Показывает как добавить кэширование к существующему FastAPI приложению.
    """
    
    # Читаем существующий код из src/py_server/main.py и http_server.py
    # и показываем как интегрировать кэширование
    
    print("""
Интеграция HTTP кэширования с существующим MCP сервером:

1. В main.py добавляем:
   from cache.http_cache import setup_cache_middleware
   
   # В функции run_http_server:
   cache_middleware = setup_cache_middleware(
       app=app,
       cache_ttl=3600,
       max_cache_size=1000,
       excluded_paths={"/health", "/info", "/token"}
   )

2. В http_server.py добавляем кастомные стратегии:
   from cache.http_cache import CacheHeaders, create_content_specific_cache_strategies
   
   # Для разных типов данных применяем разные стратегии кэширования
   response.headers["Cache-Control"] = CacheHeaders.create_cache_control(
       public=True,
       max_age=3600,
       stale_while_revalidate=60
   )

3. Добавляем endpoints для мониторинга кэша:
   @app.get("/cache/metrics")
   async def cache_metrics():
       return metrics_collector.get_summary()

4. Настраиваем логирование кэша:
   logger = logging.getLogger("cache.http_cache")
   logger.setLevel(logging.INFO)

Ключевые преимущества интеграции:
- Прозрачное кэширование существующих endpoints
- Поддержка условных запросов (If-None-Match)
- Автоматическая генерация ETag
- Метрики производительности
- Гибкие стратегии кэширования
- Интеграция с OAuth2 авторизацией
    """)


def run_example_server():
    """Запуск примера сервера с кэшированием."""
    
    # Создаем приложение с кэшированием
    app = create_cached_fastapi_app(cache_config={
        "cache_ttl": 1800,  # 30 минут
        "max_cache_size": 500,
        "excluded_paths": {
            "/health",
            "/info", 
            "/cache/admin/stats",
            "/cache/admin/clear"
        }
    })
    
    # Добавляем MCP endpoints с кэшированием
    create_cached_mcp_endpoints(app, {})
    
    # Добавляем общие endpoints
    @app.get("/")
    async def root():
        return {
            "message": "MCP Server with HTTP Cache",
            "endpoints": [
                "/health - Health check",
                "/info - Server info",
                "/cache/metrics - Cache metrics", 
                "/cache/metrics.prometheus - Prometheus format",
                "/mcp/cached/health - Cached health",
                "/mcp/cached/info - Cached info",
                "/mcp/cached/metadata/{entity_type} - Cached metadata",
                "/mcp/cached/data/{entity_type}/{id} - Cached entity data"
            ]
        }
    
    @app.get("/health")
    async def health():
        return {"status": "healthy", "cache_version": "2.0.0"}
    
    print("""
Запуск примера сервера с HTTP кэшированием:

Сервер доступен по адресу: http://localhost:8000

Endpoints для тестирования кэша:
- GET /mcp/cached/health - Кэшируемая проверка здоровья
- GET /mcp/cached/info - Кэшируемая информация о сервере  
- GET /mcp/cached/metadata/nomenclature - Кэшируемые метаданные
- GET /mcp/cached/data/nomenclature/123 - Кэшируемые данные
- GET /cache/metrics - Метрики кэша
- GET /cache/metrics.prometheus - Метрики в формате Prometheus

Тестирование ETag:
1. Первый запрос вернет ответ с заголовками ETag и Cache-Control
2. Повторный запрос с заголовком If-None-Match вернет 304 Not Modified
3. В заголовке X-Cache будет указано HIT или MISS

Пример curl команды:
curl -i http://localhost:8000/mcp/cached/info
curl -i -H "If-None-Match: \\"etag_value\\"" http://localhost:8000/mcp/cached/info
    """)
    
    # Запускаем сервер
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    run_example_server()