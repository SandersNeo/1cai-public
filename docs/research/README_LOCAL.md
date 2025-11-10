# Локальный README (подготовка публикации)

## Что сделано сегодня

1. **План + первые шаги интеграции bsl-language-server / metadata.js**  
   - Новый документ: `docs/research/bsl_language_server_plan.md`.  
   - Добавлен сервис `bsl-language-server` в `docker-compose.dev.yml`, make-таргеты `bsl-ls-*`, а парсер теперь читает `BSL_LANGUAGE_SERVER_URL` и честно откатывается на regex при недоступности сервиса.  
   - Есть скрипт `scripts/parsers/check_bsl_language_server.py` (`make bsl-ls-check`) для проверки health/parse.
   - ⚠️ Перед публикацией предупредить пользователей: обязательно протестировать локально (`make bsl-ls-up`, запрос `/actuator/health`). Если не работает — сначала проверить конфигурацию и логи, а уже после этого просить помощь.
2. **Главная страница и Documentation Hub**  
   - README переписан: добавлены быстрый обзор, навигация, Quick Start, Documentation Hub.  
   - Все новые гайды и исследования обязаны добавляться в соответствующие секции README/Documentation Hub.
3. **Конституция критических правил**  
   - Создан `docs/research/constitution.md`, добавлены ссылки в README/CHANGELOG.  
   - Используем как единый справочник для AI агентов и команды перед публикацией.

4. **Гайд по MCP серверу**  
   - Новый документ: `docs/06-features/MCP_SERVER_GUIDE.md` (запуск, инструменты, env, troubleshooting).  
   - Документационный хаб дополнен ссылкой.

5. **Testing Guide**  
   - Новый документ: `docs/06-features/TESTING_GUIDE.md` (матрица тестов, локальные команды, CI, troubleshooting).  
   - README обновлён ссылкой в блоках Testing & Documentation Hub.

6. **Обзор скриптов**  
   - Новый документ: `docs/scripts/README.md` (категории, зависимости, связь с Makefile/CI).  
   - Documentation Hub дополнен разделом Operations & Tooling.

7. **GitHub monitoring MVP**  
   - Новый скрипт: `scripts/monitoring/github_monitor.py` (CLI, снимок состояний, сравнение релизов).  
   - План обновлён: следующий шаг — автоматический запуск (cron/CI) и логирование в `logs/`.

8. **Spec-driven workflow**  
   - Шаблоны: `templates/feature-plan.md`, `feature-spec.md`, `feature-tasks.md`, `feature-research.md`.  
   - CLI: `scripts/research/init_feature.py`, `scripts/research/check_feature.py`; make `feature-init`, `feature-validate`.  
   - README/Documentation Hub/Changelog обновлены ссылками; CI job `spec-driven-validation` теперь выполняет `make feature-validate`.

9. **Фича Marketplace Packages (пример spec-driven)**  
   - Создан `docs/research/features/marketplace-packages/` — заполненные план, спецификация, задачи и исследование.  
   - Шаблоны обновлены ссылкой на пример в `templates/README.md`.

10. **План подготовки Marketplace-пакетов** (`onec-markdown-viewer`, `VAEditor`)  
    - Базовый документ: `docs/research/marketplace_integration_plan.md`.  
    - Используется как основной источник требований для фичи.

11. **Оценка архивных утилит** (`cfg_tools`, `ones_universal_tools`)  
    - Новый документ: `docs/research/archive_tools_assessment.md`.  
    - Шаги аудита, критерии отбора функций для переноса в CLI.

12. **План мониторинга GitHub-репозиториев @alkoleft**  
    - Новый документ: `docs/research/github_monitoring_plan.md`.  
    - План дополнен автоматическим workflow `github-monitor.yml`.

13. **Обновлён мастер-лист TODO**  
    - `docs/research/alkoleft_todo.md` теперь с приоритетами и ссылками на соответствующие планы.