# Scripts Overview

> Обновлено: 10 ноября 2025  •  Основано на Python 3.11 и сопутствующих CLI из `scripts/`

## 1. Назначение

Эта страница объединяет основные утилиты из каталога `scripts/`: что они делают, какие зависимости требуют и как связаны с `Makefile` и CI. Читайте перед запуском скриптов напрямую — особенно если работаете в Windows окружении или через WSL.

## 2. Быстрая карта

| Категория | Путь | Ключевые скрипты | Когда использовать |
|-----------|------|------------------|--------------------|
| Analysis | `scripts/analysis/` | `generate_documentation.py`, `analyze_*`, `tree_sitter_adapter.py` | Анализ 1C конфигураций, формирование отчётов и метрик |
| Parsers | `scripts/parsers/` | `bsl_ast_parser.py`, `parse_1c_config*.py`, `edt/` | Парсинг EDT XML и конфигураций, интеграция с `bsl-language-server` |
| Context & Docs | `scripts/context/`, `scripts/docs/` | `export_platform_context.py`, `generate_docs.py`, `create_adr.py`, `render_uml.py` | Генерация платформенного контекста, документации, ADR и UML |
| Audits | `scripts/audit/`, `run_full_audit.py` | `comprehensive_project_audit.py`, `project_structure_audit.py`, `check_git_safety.py` | Комплексные проверки перед релизом, выполнение требований конституции |
| Migrations & Data | `scripts/migrations/`, `scripts/data/` | `migrate_json_to_postgres.py`, `migrate_postgres_to_neo4j.py`, `load_configurations.py` | Наполнение хранилищ (PostgreSQL→Neo4j→Qdrant), загрузка конфигураций |
| Testing | `scripts/tests/`, `scripts/testing/` | `run_bsl_tests.py`, `check_all_results.py`, `test_gateway.sh` | Запуск BSL/YAxUnit и вспомогательных smoke/health тестов |
| Maintenance & Cleanup | `scripts/maintenance/`, `scripts/cleanup/` | `cleanup_project.py`, `move_research_files.py`, `final_root_cleanup.ps1` | Наведение порядка перед публикацией, перенос временных файлов |
| Deployment & Ops | shell-скрипты в корне (`start.sh`, `monitor-deployment.sh`) + `scripts/monitoring/` | `blue-green-deploy.sh`, `schedule-traffic-switch.sh`, `health-check.sh`, `monitoring/github_monitor.py` | Управление окружениями, мониторинг деплоя и внешних зависимостей |
| Windows Helpers | `scripts/windows/` | `bsl-ls-up.ps1`, `bsl-ls-check.ps1`, `feature-init.ps1`, `feature-validate.ps1` | Альтернатива make/dc для PowerShell пользователей |
| Spec-driven workflow | `scripts/research/`, `templates/` | `init_feature.py`, шаблоны `feature-*.md` | Создание каркасов планов/спеков, работа по методологии |
| ML & Benchmarks | `scripts/dataset/`, `scripts/ml/`, `benchmark_*.py` | `create_ml_dataset.py`, `massive_ast_dataset_builder.py`, `benchmark_performance.py` | Подготовка датасетов, измерение производительности |

## 3. Зависимости и подготовка

- Python 3.11.x — установите системно или через `pyenv`. Скрипты проверяют версию.
- Виртуальное окружение + `make install` (или соответствующие `pip install -r requirements*.txt`).
- Docker Compose: требуется для миграций и анализа (PostgreSQL, Neo4j, Qdrant, Redis).
- **Внешние инструменты**: 
  - `platform-context-exporter` → переменная `PLATFORM_CONTEXT_EXPORTER_CMD` (см. `export_platform_context.py`).
  - `ones_doc_gen` → `ONES_DOC_GEN_CMD` (см. `generate_docs.py`).
  - YAxUnit/OneScript → для `run_bsl_tests.py` и тестов 1С.
- Windows: для PowerShell-скриптов (`*.ps1`) запускайте под администратором, либо используйте аналоги в bash/WSL.

## 4. Основные рабочие сценарии

### 4.1 Аналитика (`scripts/analysis/`)
- `generate_documentation.py` — собирает JSON-результаты анализа (архитектура, best practices) и формирует Markdown (используется в pipeline документации).
- `analyze_architecture.py`, `analyze_dependencies.py`, `extract_best_practices.py` — запускаются вручную или через orchestrators для извлечения статистики.
- `tree_sitter_adapter.py` — обёртка над `tree-sitter-bsl` с fallback на regex (используется внутри анализаторов).

### 4.2 Контекст и документация
- `context/export_platform_context.py` — прокси к `alkoleft/platform-context-exporter`. Без заданного `PLATFORM_CONTEXT_EXPORTER_CMD` скрипт мягко завершится, напомнив установить инструмент.
- `context/generate_docs.py` — аналогичный вызов `alkoleft/ones_doc_gen` (env `ONES_DOC_GEN_CMD`).
- `docs/create_adr.py` — создаёт новый ADR на основе slug, автоматически обновляет `docs/architecture/adr/README.md`.
- `docs/render_uml.py` — рендер PlantUML диаграмм; используется в `make render-uml` и GitHub Actions.

### 4.3 Миграции и данные
- `migrations/migrate_json_to_postgres.py` → загрузка выгрузки DO/ERP в Postgres.
- `migrations/migrate_postgres_to_neo4j.py`, `migrate_to_qdrant.py` → построение графа и векторного индекса.
- `run_migrations.py` — orchestration to end-to-end migration.
- **Внимание**: все миграции требуют поднятых сервисов (`make docker-up`).

### 4.4 Аудиты и контроль качества
- `audit/comprehensive_project_audit.py` + `run_full_audit.py` — выполняют полный чек-лист (структура, лицензии, broken links). Обязательны перед публикацией, см. `docs/research/constitution.md`.
- `audit/check_git_safety.py`, `audit/license_compliance_audit.py` — точечные проверки безопасности и лицензий.

### 4.5 Тесты и QA
- `tests/run_bsl_tests.py` — исполняет BSL/YAxUnit манифест (`tests/bsl/testplan.json`), сохраняет логи в `output/bsl-tests`. Связан с `make test-bsl` и job `bsl-tests`.
- `testing/run_demo_tests.py`, `testing/test_its_api.py` и др. — быстрые smoke-проверки API/интеграций.
- Подробный обзор команд — в [`docs/06-features/TESTING_GUIDE.md`](../06-features/TESTING_GUIDE.md).

### 4.6 Сервисные и maintenance скрипты
- `maintenance/cleanup_project.py`, `cleanup/move_research_files.py` — автоматизируют уборку временных файлов, соблюдают требования `.gitignore` и публикации.
- PowerShell сценарии `maintenance/*.ps1` — для Windows (архивация, финальная очистка).
- `backup-restore.sh`, `create-backup.sh`, `emergency-rollback.sh` — готовые процедуры резервирования.

### 4.7 Операции и деплой
- `start.sh`, `stop.sh`, `start_ecosystem.sh` — запуск локальной экосистемы (API, MCP, базы).
- `blue-green-deploy.sh`, `schedule-traffic-switch.sh`, `monitor-deployment.sh` — сценарии развёртывания и переключения трафика.
- `health-check.sh`, `monitoring.sh` — базовые health-проверки.
- `monitoring/github_monitor.py` — опрос GitHub API для отслеживания релизов/коммитов внешних зависимостей, сохраняет состояние в `output/monitoring/github_state.json` (см. план мониторинга).

### 4.8 Spec-driven workflow
- `templates/feature-*.md` — заготовки для планов, спецификаций, задач и исследований (благодарность [github/spec-kit](https://github.com/github/spec-kit)).
- `scripts/research/init_feature.py` — создаёт каталог `docs/research/features/<slug>/` и копирует шаблоны.
- `scripts/research/check_feature.py` — проверяет, что заполненные документы не содержат шаблонных маркеров/`TODO`.
- Make-таргеты: `make feature-init FEATURE=my-feature` и `make feature-validate [FEATURE=my-feature]`.
- После создания обязательно заполните документы, обновите README/CHANGELOG и соблюдайте `docs/research/constitution.md`.

### 4.9 Windows helpers
- `scripts/windows/bsl-ls-up.ps1`, `bsl-ls-check.ps1`, `bsl-ls-logs.ps1` — запуск и диагностика `bsl-language-server` без `make`.
- `scripts/windows/feature-init.ps1`, `feature-validate.ps1` — PowerShell аналоги make-таргетов spec-driven workflow.
- Запускаются из корня проекта: `pwsh scripts/windows/feature-init.ps1 -Feature my-feature`.

### 4.8 ML и экспериментальные утилиты
- `dataset/create_ml_dataset.py`, `prepare_neural_training_data.py` — подготовка выборок для моделей.
- `finetune_qwen_smoltalk.py`, `train_copilot_model.py` — эксперименты с дообучением ассистента.
- `benchmark_performance.py`, `profile_full_parser.py` — измерение скорости анализа/парсинга.

## 5. Связь с Makefile

| Make цель | Что запускает | Где описано |
|-----------|---------------|-------------|
| `make generate-docs` | `context/generate_docs.py` | текущий документ (4.2) |
| `make export-context` | `context/export_platform_context.py` | текущий документ (4.2) |
| `make bsl-ls-check` | `parsers/check_bsl_language_server.py` | [AST tooling guide](../06-features/AST_TOOLING_BSL_LANGUAGE_SERVER.md) |
| `make migrate` | `migrations/*` через последовательный pipelines | раздел 4.3 |
| `make test-bsl` | `tests/run_bsl_tests.py` | раздел 4.5 |
| `make render-uml` | `docs/render_uml.py` | раздел 4.2 |
| `make quality` | пакет формата/линта + `pytest` | см. `Makefile` |

Всегда сверяйтесь с `make help`: команды обновляются синхронно со скриптами.

## 6. Правила безопасности

- Перед выпуском прогоните `run_full_audit.py` и убедитесь, что все пункты `docs/research/constitution.md` соблюдены.
- Скрипты не должны хранить секреты в открытом виде; используйте `.env` и `Settings` (см. `src/config.py`).
- Если скрипт требует внешнюю утилиту, документируйте её версию и путь в README или changelog.

## 7. Благодарности

- [alkoleft/platform-context-exporter](https://github.com/alkoleft/platform-context-exporter) — экспорт платформенного контекста (используется в `export_platform_context.py`).
- [alkoleft/ones_doc_gen](https://github.com/alkoleft/ones_doc_gen) — генерация документации (используется в `generate_docs.py`).
- [alkoleft/yaxunit](https://github.com/alkoleft/yaxunit) и [alkoleft/mcp-onec-test-runner](https://github.com/alkoleft/mcp-onec-test-runner) — тестирование BSL, реализовано в `run_bsl_tests.py` и Makefile.
- Сообщество GitHub Spec Kit — вдохновение для стандартизованных процессов и CLI.
