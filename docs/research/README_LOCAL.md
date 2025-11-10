# Локальный README (подготовка публикации)

## Что сделано сегодня

1. **План + первые шаги интеграции bsl-language-server / metadata.js**  
   - Новый документ: `docs/research/bsl_language_server_plan.md`.  
   - Добавлен сервис `bsl-language-server` в `docker-compose.dev.yml`, make-таргеты `bsl-ls-*`, а парсер теперь читает `BSL_LANGUAGE_SERVER_URL` и честно откатывается на regex при недоступности сервиса.  
   - Есть скрипт `scripts/parsers/check_bsl_language_server.py` (`make bsl-ls-check`) для проверки health/parse.
   - ⚠️ Перед публикацией предупредить пользователей: обязательно протестировать локально (`make bsl-ls-up`, запрос `/actuator/health`). Если не работает — сначала проверить конфигурацию и логи, а уже после этого просить помощь.

2. **План подготовки Marketplace-пакетов** (`onec-markdown-viewer`, `VAEditor`)  
   - Новый документ: `docs/research/marketplace_integration_plan.md`.  
   - Структура bundle, manifest, процесс публикации через наш API, требования к материалам.

3. **Оценка архивных утилит** (`cfg_tools`, `ones_universal_tools`)  
   - Новый документ: `docs/research/archive_tools_assessment.md`.  
   - Шаги аудита, критерии отбора функций для переноса в CLI.

4. **План мониторинга GitHub-репозиториев @alkoleft**  
   - Новый документ: `docs/research/github_monitoring_plan.md`.  
   - Описаны варианты webhooks/polling, хранение состояния, уведомления.

5. **Обновлён мастер-лист TODO**  
   - `docs/research/alkoleft_todo.md` теперь с приоритетами и ссылками на соответствующие планы.

## Что ещё не опубликовано

- Все изменения пока только локально, без коммитов/пуша.
- Техдолг: установка Python 3.11 и запуск API/MCP остаётся на паузе.

## Следующие шаги (после ревью)

- Решить, какие планы публикуем в repo (оформление PR).  
- После подтверждения — коммит + пуш документации.  
- При необходимости дополнить changelog/README основными пунктами.
