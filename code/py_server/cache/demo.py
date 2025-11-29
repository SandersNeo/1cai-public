# [NEXUS IDENTITY] ID: 5619063836608662575 | DATE: 2025-11-19

#!/usr/bin/env python3
"""
Демонстрация HTTP кэширования с ETag для FastAPI.

Этот файл содержит простой пример использования модуля HTTP кэширования.
Запустите: python demo.py
"""

import asyncio
import time

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Импортируем наш модуль кэширования
try:
    from .http_cache import (CacheHeaders, metrics_collector, setup_cache_middleware)
except ImportError:
    # Для запуска как отдельного скрипта
    from http_cache import (CacheHeaders, metrics_collector, setup_cache_middleware)


def create_demo_app() -> FastAPI:
    """Создает демо приложение с кэшированием."""
    
    # Создаем FastAPI приложение
    app = FastAPI(
        title="HTTP Cache Demo",
        description="Демонстрация HTTP кэширования с ETag",
        version="1.0.0"
    )
    
    # Настраиваем HTTP кэширование
    cache_middleware = setup_cache_middleware(
        app=app,
        secret_key="demo_secret_key_2024",
        cache_ttl=300,  # 5 минут для демо
        max_cache_size=100,
        excluded_paths={"/health", "/metrics", "/clear"}
    )
    
    # Добавляем endpoints для демонстрации
    
    @app.get("/")
    async def root():
        """Главная страница с описанием endpoints."""
        return {
            "message": "HTTP Cache Demo",
            "description": "Демонстрация HTTP кэширования с ETag",
            "endpoints": {
                "/static-data": "Кэшируемые статические данные",
                "/dynamic-data": "Кэшируемые динамические данные", 
                "/personal-data": "Персональные данные (private cache)",
                "/no-cache": "Данные без кэширования",
                "/cache-stats": "Статистика кэша",
                "/clear": "Очистка кэша",
                "/health": "Проверка здоровья (не кэшируется)"
            },
            "cache_metrics": metrics_collector.get_summary()
        }
    
    @app.get("/static-data")
    async def get_static_data():
        """Получение статических данных с долгим кэшированием."""
        data = {
            "type": "static",
            "message": "Эти данные кэшируются на 24 часа",
            "timestamp": time.time(),
            "metadata": {
                "version": "1.0",
                "last_updated": "2024-01-01T00:00:00Z"
            }
        }
        
        # Создаем ответ с кэшированием на 24 часа
        response = JSONResponse(content=data)
        cache_control = CacheHeaders.create_cache_control(
            public=True,
            max_age=86400,  # 24 часа
            immutable=True  # Данные не меняются
        )
        response.headers["Cache-Control"] = cache_control
        response.headers["X-Data-Type"] = "static"
        
        return response
    
    @app.get("/dynamic-data")
    async def get_dynamic_data():
        """Получение динамических данных с коротким кэшированием."""
        data = {
            "type": "dynamic",
            "message": "Эти данные кэшируются на 5 минут",
            "timestamp": time.time(),
            "counter": int(time.time()) % 1000  # Изменяется каждую секунду
        }
        
        # Создаем ответ с кэшированием на 5 минут
        response = JSONResponse(content=data)
        cache_control = CacheHeaders.create_cache_control(
            public=True,
            max_age=300,  # 5 минут
            stale_while_revalidate=30,  # Отдать устаревший на 30 секунд
            stale_if_error=300  # При ошибке отдать устаревший на 5 минут
        )
        response.headers["Cache-Control"] = cache_control
        response.headers["X-Data-Type"] = "dynamic"
        
        return response
    
    @app.get("/personal-data")
    async def get_personal_data():
        """Персональные данные (кэшируются только в браузере)."""
        data = {
            "type": "personal",
            "message": "Эти данные кэшируются только в браузере пользователя",
            "user_id": "user_123",
            "permissions": ["read", "write"],
            "timestamp": time.time()
        }
        
        # Персональное кэширование
        response = JSONResponse(content=data)
        cache_control = CacheHeaders.create_cache_control(
            private=True,  # Только в браузере пользователя
            max_age=1800   # 30 минут
        )
        response.headers["Cache-Control"] = cache_control
        response.headers["X-Data-Type"] = "personal"
        
        return response
    
    @app.get("/no-cache")
    async def get_no_cache_data():
        """Данные без кэширования."""
        data = {
            "type": "no-cache",
            "message": "Эти данные НЕ кэшируются",
            "timestamp": time.time(),
            "random": int(time.time() * 1000000) % 1000
        }
        
        response = JSONResponse(content=data)
        cache_control = CacheHeaders.create_cache_control(
            no_store=True  # Полный запрет кэширования
        )
        response.headers["Cache-Control"] = cache_control
        response.headers["X-Data-Type"] = "no-cache"
        
        return response
    
    @app.get("/cache-stats")
    async def get_cache_stats():
        """Получение статистики кэша."""
        return {
            "cache_metrics": metrics_collector.get_summary(),
            "description": "Статистика работы HTTP кэша",
            "endpoints_for_testing": {
                "test_static": "/static-data",
                "test_dynamic": "/dynamic-data",
                "test_personal": "/personal-data",
                "test_no_cache": "/no-cache"
            }
        }
    
    @app.post("/clear")
    async def clear_cache():
        """Очистка кэша."""
        cleared_count = 0
        for middleware in metrics_collector.middlewares:
            cleared_count += len(middleware._cache)
            middleware._cache.clear()
            middleware._cache_order.clear()
        
        return {
            "status": "success",
            "message": f"Кэш очищен. Удалено {cleared_count} записей.",
            "new_metrics": metrics_collector.get_summary()
        }
    
    @app.get("/health")
    async def health_check():
        """Проверка здоровья сервера (не кэшируется)."""
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "cache_enabled": True,
            "version": "1.0.0"
        }
    
    # Добавляем middleware для демонстрации ETag
    @app.middleware("http")
    async def demo_etag_middleware(request, call_next):
        """Middleware для демонстрации работы ETag."""
        start_time = time.time()
        
        response = await call_next(request)
        
        # Добавляем время обработки в заголовки
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    
    return app


async def run_demo():
    """Запуск демо сервера."""
    print("""
╔════════════════════════════════════════════════════════════════╗
║                HTTP Cache Demo Server                         ║
║                  с ETag и Conditional GET                     ║
╚════════════════════════════════════════════════════════════════╝

Сервер запущен на http://localhost:8000

Endpoints для тестирования:
┌─────────────────┬──────────────────────────────────────────────┐
│ Endpoint        │ Описание                                    │
├─────────────────┼──────────────────────────────────────────────┤
│ /               │ Главная страница с описанием               │
│ /static-data    │ Статические данные (кэш 24h, immutable)    │
│ /dynamic-data   │ Динамические данные (кэш 5m, stale-*)      │
│ /personal-data  │ Персональные данные (private cache)        │
│ /no-cache       │ Данные без кэширования                     │
│ /cache-stats    │ Статистика кэша                            │
│ /clear          │ Очистка кэша (POST)                        │
│ /health         │ Проверка здоровья                          │
└─────────────────┴──────────────────────────────────────────────┘

Тестирование кэширования:

1. Базовое кэширование:
   curl -i http://localhost:8000/static-data
   # Первый запрос: X-Cache: MISS
   # Повторный запрос: X-Cache: HIT

2. Условные запросы с ETag:
   curl -i http://localhost:8000/static-data
   # Скопируйте ETag из ответа
   curl -i -H "If-None-Match: \\"ваш-etag\\"" http://localhost:8000/static-data
   # Должен вернуть: 304 Not Modified

3. Проверка метрик:
   curl http://localhost:8000/cache-stats | jq

4. Очистка кэша:
   curl -X POST http://localhost:8000/clear

Ожидаемые результаты:
- Статические данные: X-Cache: HIT после первого запроса
- Динамические данные: X-Cache: HIT (но содержимое может отличаться)
- Персональные данные: X-Cache: HIT, Cache-Control: private
- Без кэширования: X-Cache: BYPASS
- Условные запросы: 304 Not Modified

Нажмите Ctrl+C для остановки сервера
""")
    
    # Создаем и запускаем приложение
    app = create_demo_app()
    
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
        access_log=True
    )
    server = uvicorn.Server(config)
    
    try:
        await server.serve()
    except KeyboardInterrupt:
        print("\nСервер остановлен.")


def test_cache_endpoints():
    """Тестирование endpoints кэша с помощью curl."""
    import json
    import subprocess
    
    base_url = "http://localhost:8000"
    
    print("Тестирование HTTP кэширования...")
    print("=" * 50)
    
    # Тест 1: Статические данные
    print("\n1. Тестирование статических данных:")
    try:
        # Первый запрос
        result = subprocess.run([
            "curl", "-s", "-i", f"{base_url}/static-data"
        ], capture_output=True, text=True)
        
        print("Первый запрос:")
        print(result.stdout)
        
        # Второй запрос
        result2 = subprocess.run([
            "curl", "-s", "-i", f"{base_url}/static-data"
        ], capture_output=True, text=True)
        
        print("\nВторой запрос (должен попасть в кэш):")
        print(result2.stdout)
        
    except Exception as e:
        print(f"Ошибка тестирования: {e}")
    
    # Тест 2: Получение метрик
    print("\n\n2. Получение метрик кэша:")
    try:
        result = subprocess.run([
            "curl", "-s", f"{base_url}/cache-stats"
        ], capture_output=True, text=True)
        
        metrics = json.loads(result.stdout)
        print(f"Попадания в кэш: {metrics['cache_metrics']['hits']}")
        print(f"Промахи кэша: {metrics['cache_metrics']['misses']}")
        print(f"Коэффициент попаданий: {metrics['cache_metrics']['hit_ratio']:.2%}")
        
    except Exception as e:
        print(f"Ошибка получения метрик: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Режим тестирования
        print("Запуск тестов кэширования...")
        try:
            # Запускаем сервер в фоне
            import threading
            import time
            
            def run_server():
                asyncio.run(run_demo())
            
            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            
            # Ждем запуска сервера
            time.sleep(3)
            
            # Запускаем тесты
            test_cache_endpoints()
            
            print("\nТесты завершены. Сервер продолжает работать...")
            print("Для остановки нажмите Ctrl+C")
            
            # Ждем завершения
            server_thread.join()
            
        except KeyboardInterrupt:
            print("\nТестирование завершено.")
    else:
        # Обычный запуск
        asyncio.run(run_demo())