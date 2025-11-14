# Cache Utilities

| Модуль | Назначение |
|--------|-----------|
| `multi_layer_cache.py` | Реализация многоуровневого кеша (in-memory + Redis/др.), используется сервисами AI и API для ускорения ответов.

Параметры и конфигурации задаются через `config.py` и `.env`. Проверки — в [`tests/unit/test_cache_service.py`](../../tests/unit/test_cache_service.py).
