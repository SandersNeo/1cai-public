# HTTP кэширование с ETag для MCP сервера

Модуль HTTP кэширования с ETag для FastAPI сервера, реализующий современные стандарты кэширования согласно RFC 7234 и спецификации 1С.

## Основные возможности

### 🔄 Условные HTTP запросы
- Поддержка `If-None-Match` для точной валидации через ETag
- Поддержка `If-Modified-Since` для проверки по времени изменения
- Автоматическая генерация `304 Not Modified` ответов

### 🏷️ Генерация и валидация ETag
- Сильные валидаторы ETag с HMAC подписью
- Поддержка различных типов контента (JSON, текст, бинарные данные)
- Fallback механизмы для надежности

### 📊 Управление заголовками кэширования
- Полная поддержка директив `Cache-Control`:
  - `max-age`, `s-maxage`, `no-cache`, `no-store`
  - `public`, `private`, `immutable`
  - `stale-while-revalidate`, `stale-if-error`
- Автоматическое создание заголовков `Expires`, `Last-Modified`, `Age`

### 📈 Метрики и мониторинг
- Сбор метрик производительности кэша
- Экспорт в формате Prometheus
- Детальная статистика (hit ratio, время отклика, количество запросов)

### 🛠️ Интеграция с FastAPI
- Middleware для прозрачного кэширования
- Интеграция с OAuth2 авторизацией
- Гибкие стратегии кэширования для разных типов контента

## Быстрый старт

### 1. Базовое использование

```python
from fastapi import FastAPI
from cache.http_cache import setup_cache_middleware

# Создаем FastAPI приложение
app = FastAPI(title="MCP Server", version="2.0.0")

# Настраиваем HTTP кэширование
cache_middleware = setup_cache_middleware(
    app=app,
    cache_ttl=3600,  # 1 час
    max_cache_size=1000
)

# Ваши endpoints автоматически будут кэшироваться
@app.get("/api/data")
async def get_data():
    return {"message": "This response will be cached"}
```

### 2. Интеграция с существующим сервером

```python
# В main.py добавляем:
from cache.http_cache import setup_cache_middleware

async def run_http_server(config):
    app = FastAPI()
    
    # Настраиваем кэширование
    cache_middleware = setup_cache_middleware(
        app=app,
        cache_ttl=1800,  # 30 минут
        max_cache_size=500,
        excluded_paths={"/health", "/info", "/token"}
    )
    
    # Добавляем ваши endpoints
    # ...
    
    # Запускаем сервер
    uvicorn.run(app, host=config.host, port=config.port)
```

### 3. Кастомные стратегии кэширования

```python
from cache.http_cache import CacheHeaders

@app.get("/api/metadata")
async def get_metadata():
    # Применяем специфичную стратегию для метаданных
    cache_control = CacheHeaders.create_cache_control(
        public=True,
        max_age=86400,  # 24 часа
        s_maxage=43200,  # 12 часов для CDN
        immutable=True  # Метаданные не изменяются часто
    )
    
    data = get_metadata_from_1c()
    
    response = JSONResponse(content=data)
    response.headers["Cache-Control"] = cache_control
    return response
```

## Архитектура

### Основные компоненты

#### 1. ETagManager
```python
from cache.http_cache import ETagManager

etag_manager = ETagManager(secret_key="your_secret_key")

# Генерация ETag
etag = etag_manager.generate_etag(data, "application/json")
# "W/\"a1b2c3d4.5f6g7h8\""

# Валидация ETag
is_valid = etag_manager.validate_etag(etag, data, "application/json")
```

#### 2. CacheHeaders
```python
from cache.http_cache import CacheHeaders

# Создание заголовков Cache-Control
cache_control = CacheHeaders.create_cache_control(
    public=True,
    max_age=3600,
    stale_while_revalidate=60,
    stale_if_error=300
)
# "public, max-age=3600, stale-while-revalidate=60, stale-if-error=300"
```

#### 3. ConditionalGET
```python
from cache.http_cache import ConditionalGET

conditional = ConditionalGET(etag_manager)

# Проверка условного запроса
needs_304, headers = conditional.should_return_304(
    request,
    etag="W/\"a1b2c3d4.5f6g7h8\"",
    last_modified="Mon, 01 Jan 2024 00:00:00 GMT"
)

if needs_304:
    response_304 = conditional.create_304_response(original_headers)
    return response_304
```

#### 4. HTTPCacheMiddleware
```python
from cache.http_cache import HTTPCacheMiddleware

middleware = HTTPCacheMiddleware(
    app=app,
    etag_manager=etag_manager,
    cache_ttl=3600,
    max_cache_size=1000,
    cache_key_func=custom_cache_key_func,
    excluded_paths={"/health", "/admin/*"}
)
```

### Стратегии кэширования

#### Для статических данных (справочники)
```python
cache_control = CacheHeaders.create_cache_control(
    public=True,
    max_age=86400,  # 24 часа
    s_maxage=43200,  # 12 часов для CDN
    immutable=True
)
```

#### Для часто изменяющихся данных (документы)
```python
cache_control = CacheHeaders.create_cache_control(
    public=True,
    max_age=300,  # 5 минут
    s_maxage=60,  # 1 минута для CDN
    stale_while_revalidate=30,
    stale_if_error=300
)
```

#### Для персонализированных данных
```python
cache_control = CacheHeaders.create_cache_control(
    private=True,
    max_age=1800  # 30 минут
)
```

#### Для API с высокой нагрузкой
```python
cache_control = CacheHeaders.create_cache_control(
    public=True,
    max_age=180,  # 3 минуты
    s_maxage=30,  # 30 секунд для CDN
    stale_while_revalidate=60,
    stale_if_error=600
)
```

## Мониторинг и метрики

### Получение метрик
```python
from cache.http_cache import metrics_collector

# JSON формат
metrics = metrics_collector.get_summary()
print(metrics)
# {
#     "hits": 150,
#     "misses": 50,
#     "hit_ratio": 0.75,
#     "conditional_requests": 25,
#     "not_modified_responses": 20,
#     "avg_cache_time": 0.015,
#     "total_requests": 200
# }

# Prometheus формат
prometheus_metrics = metrics_collector.export_prometheus()
print(prometheus_metrics)
```

### Endpoints для мониторинга
```
GET /cache/metrics          # Метрики в JSON
GET /cache/metrics.prometheus  # Метрики для Prometheus
GET /cache/admin/stats      # Подробная статистика
POST /cache/admin/clear     # Очистка кэша
```

### Логирование
```python
import logging

# Настройка логирования кэша
cache_logger = logging.getLogger("cache.http_cache")
cache_logger.setLevel(logging.INFO)

# Логи будут содержать информацию о:
# - Попаданиях/промахах кэша
# - Условных запросах
# - 304 ответах
# - Ошибках кэширования
```

## Интеграция с OAuth2

Модуль корректно работает с OAuth2 авторизацией:

1. **Исключенные пути**: пути авторизации исключены из кэширования
2. **Приватные данные**: для авторизованных пользователей данные кэшируются как `private`
3. **Безопасность**: ETag не раскрывает содержимое данных

```python
# В http_server.py OAuth2BearerMiddleware уже учитывает кэширование
middleware = OAuth2BearerMiddleware(app, oauth2_service, auth_mode)

# Персонализированные данные будут кэшироваться отдельно для каждого пользователя
```

## Тестирование

### Проверка кэширования
```bash
# Первый запрос
curl -i http://localhost:8000/api/data
# Ответ содержит: ETag, Cache-Control, X-Cache: MISS

# Повторный запрос (должен вернуть кэшированный ответ)
curl -i http://localhost:8000/api/data
# Ответ содержит: X-Cache: HIT

# Условный запрос с ETag
curl -i -H "If-None-Match: \"your-etag\"" http://localhost:8000/api/data
# Ответ: 304 Not Modified, X-Cache: HIT
```

### Проверка метрик
```bash
# Получение метрик
curl http://localhost:8000/cache/metrics | jq

# Прометеус метрики
curl http://localhost:8000/cache/metrics.prometheus
```

## Конфигурация

### Параметры кэширования

| Параметр | Тип | Описание | По умолчанию |
|----------|-----|----------|--------------|
| `cache_ttl` | int | TTL кэша в секундах | 3600 |
| `max_cache_size` | int | Максимальное количество записей | 1000 |
| `secret_key` | str | Секретный ключ для ETag | "default..." |
| `excluded_paths` | Set[str] | Пути исключенные из кэширования | {"/health"} |

### Переменные окружения
```bash
# Необязательные настройки
MCP_CACHE_TTL=3600              # TTL кэша
MCP_CACHE_MAX_SIZE=1000         # Максимальный размер кэша
MCP_CACHE_SECRET_KEY="your_key" # Секретный ключ
MCP_CACHE_LOG_LEVEL=INFO        # Уровень логирования
```

## Лучшие практики

### 1. Выбор TTL
- **Статические данные**: 24 часа (86400s)
- **Метаданные**: 1 час (3600s) 
- **Оперативные данные**: 5-15 минут (300-900s)
- **Персональные данные**: 30 минут (1800s)

### 2. Исключение из кэширования
- Пути авторизации (`/token`, `/authorize`)
- Динамические API (`/search`, `/filter`)
- Административные endpoints (`/admin/*`)
- Endpoints с конфиденциальными данными

### 3. Мониторинг
- Регулярно проверяйте hit ratio (должен быть > 70%)
- Следите за временем ответа кэша
- Мониторьте количество 304 ответов
- Настройте алерты при высоком проценте промахов

### 4. Безопасность
- Используйте уникальный secret_key в продакшене
- Для персонализированных данных используйте `private`
- Исключайте конфиденциальные пути из кэширования
- Регулярно обновляйте ETag при изменениях данных

## Производительность

### Ожидаемые результаты
- **Снижение нагрузки на сервер**: до 80%
- **Ускорение ответа**: в 5-10 раз для кэшируемых данных
- **Снижение трафика**: до 70% за счет 304 ответов
- **Улучшение UX**: мгновенная загрузка для повторных запросов

### Оптимизация
- Настройте appropriate TTL для разных типов данных
- Используйте CDN для статических ресурсов
- Мониторьте размер кэша и настройте LRU очистку
- Реализуйте cache warming для критичных данных

## Troubleshooting

### Частые проблемы

#### Кэш не работает
```python
# Проверьте логи
logger = logging.getLogger("cache.http_cache")
logger.setLevel(logging.DEBUG)

# Проверьте заголовки ответа
response.headers["X-Cache"]  # Должно быть HIT или MISS
```

#### Высокий процент промахов
- Проверьте настройки TTL
- Убедитесь что excluded_paths настроены правильно
- Проверьте размер кэша (max_cache_size)

#### ETag не совпадает
```python
# Проверьте генерацию ETag
etag = etag_manager.generate_etag(content)
print(f"Generated ETag: {etag}")

# Валидация
is_valid = etag_manager.validate_etag(etag, content)
print(f"ETag valid: {is_valid}")
```

### Логи и отладка
```python
# Включение детального логирования
import logging
logging.getLogger("cache.http_cache").setLevel(logging.DEBUG)

# Проверка контекста кэша
from cache.http_cache import cache_context
cache_info = cache_context.get()
print(f"Cache info: {cache_info}")
```

## Поддержка

Для вопросов и проблем:
1. Проверьте логи с уровнем DEBUG
2. Используйте endpoints мониторинга
3. Протестируйте с помощью curl
4. Обратитесь к документации RFC 7234

## Ссылки

- [RFC 7234: HTTP Caching](https://tools.ietf.org/html/rfc7234)
- [MDN: HTTP Caching](https://developer.mozilla.org/ru/docs/Web/HTTP/Guides/Caching)
- [Стандарты кэширования 1С](../README.md)
- [Анализ архитектуры 1c_mcp](../README.md)