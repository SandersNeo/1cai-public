# План мониторинга GitHub-репозиториев @alkoleft

## Цели

- Отслеживать обновления ключевых репозиториев (`tree-sitter-bsl`, `bsl-language-server`, `cfg_tools`, `ones_doc_gen`, и т.д.).
- Автоматически создавать уведомления/issue, если появились новые релизы или breaking changes.
- Обновлять внутренние зависимости (docker-образы, артефакты, документация) без ручного мониторинга.

## Подходы

1. **GitHub Webhooks → Ingress**
   - Настроить webhook на организацию/репозитории: события `release`, `push`, `issues`.
   - Принять webhook в нашем API (`/integrations/github/webhook`), валидировать подпись.
   - Отправить событие в очередь/Redis и обработать worker'ом.

2. **Scheduled Polling (GitHub API)**
   - Async job (APS scheduler) раз в N часов обращается к `https://api.github.com/repos/...`.
   - Использовать ETag/If-Modified-Since для экономии rate limit.
   - Сравнивать версию тегов/commit hash с последним сохраненным.

## План внедрения

1. **Определить список наблюдаемых репозиториев** (минимум: `tree-sitter-bsl`, `bsl-language-server`, `metadata.js`, `ones_doc_gen`, `platform-context-exporter`, `cfg_tools`).
2. **Создать модель хранения** в БД (таблица `github_repo_status`: repo, latest_release, latest_commit, last_checked).
3. **Разработать сервис** `src/services/github_monitor.py`:
   - Методы `fetch_repo_state`, `detect_changes`, `persist_state`.
   - Интерфейс уведомлений (лог, e-mail, issue creation).
4. **Поддержка webhooks**:
   - Endpoint FastAPI + проверка `X-Hub-Signature-256`.
   - Валидация payload, нормализация.
5. **План работ с событиями**:
   - При release → создать issue/вписать в Slack/Telegram (через существующие интеграции).
   - При push в main → пометить зависимости «проверить» (TODO).
6. **Интеграция с CI**:
   - Workflow GitHub Actions, который обновляет baseline (для подрядчиков).  
   - Возможность запускать `python scripts/monitoring/github_check.py --repo ...` локально.
7. **Документация**: обновить `docs/architecture/README.md`, добавить раздел в `docs/research/alkoleft_todo.md`.

## Минимальный MVP

- Cron job (AsyncIOScheduler) каждые 12 часов → polling GitHub API.  
- Логирование в `logs/github_monitor.log`.  
- Создание заметки в `docs/research/alkoleft_inventory.md` при появлении нового релиза.

## Расширения

- Интеграция с Prometheus (метрики обновлений).  
- Автоматический PR с bump версий файлов (`requirements.txt`, Makefile).  
- Аналитика релизов (скорость обновлений, авторы релизов).
