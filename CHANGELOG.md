# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 🔴 Breaking Changes & Migration Notes

> **Important:** This section documents breaking changes and migration paths between versions.

### Version 5.x → Future 6.x (When Released)

**Planned breaking changes:**
- Database schema updates (migration script will be provided)
- API endpoint restructuring (detailed migration guide)

**Migration:** 
- Migration scripts will be provided in release notes
- Estimated downtime: <5 minutes

---

## [Unreleased]

### ✨ Added
- Локальная интеграция `bsl-language-server`: docker-compose сервис, make-таргеты для управления и скрипт `scripts/parsers/check_bsl_language_server.py` для health/AST проверки.
- `BSLASTParser` теперь читает `BSL_LANGUAGE_SERVER_URL`, валидирует доступность LSP и корректно откатывается на regex-парсер.
- Документация обновлена планом интеграции и рекомендациями по локальному тестированию.
- Создан `docs/06-features/MCP_SERVER_GUIDE.md` — запуск, инструменты, переменные окружения и troubleshooting для MCP сервера.
- Создан `docs/06-features/TESTING_GUIDE.md` — обзор тестовой матрицы, команды, CI и troubleshooting.
- Создан `docs/scripts/README.md` — карта утилит `scripts/`, зависимости и связь с Makefile/CI.
- Добавлен `scripts/monitoring/github_monitor.py` — CLI для отслеживания релизов/коммитов внешних GitHub-репозиториев и сохранения состояния.
- Добавлены шаблоны spec-driven workflow (`templates/feature-*.md`), README и скрипты `scripts/research/init_feature.py`, `scripts/research/check_feature.py`; Make цели `feature-init` и `feature-validate`.
- CI job `spec-driven-validation` выполняет `make feature-validate`, предотвращая публикацию незаполненных спецификаций.
- Добавлены PowerShell-утилиты (`scripts/windows/*`) для bsl-language-server и spec-driven команд.
- Workflow `github-monitor.yml` ежедневно сохраняет snapshot зависимостей; workflow `docs-lint.yml` проверяет Markdown и ссылки.
- FAQ и `docs/06-features/TESTING_GUIDE.md` расширены разделами Troubleshooting и описанием артефактов.
- Скрипт релиза `scripts/release/create_release.py`, make-таргеты `release-*`, workflow `release.yml` и плейбук [`docs/research/release_playbook.md`](docs/research/release_playbook.md).
- Workflow `secret-scan.yml` (Gitleaks) для проверки утечек секретов; конституция дополнится требованиями least privilege.
- Скрипт `scripts/metrics/collect_dora.py` и workflow `dora-metrics.yml` — автоматический сбор еженедельных DORA метрик.
- Добавлен smoke workflow (`smoke-tests` + `scripts/testing/smoke_healthcheck.py`) и HTML/JUnit артефакты для unit-тестов.
- Документация по наблюдаемости: [`docs/observability/SLO.md`](docs/observability/SLO.md) и [`docs/runbooks/alert_slo_runbook.md`](docs/runbooks/alert_slo_runbook.md).
- FastAPI `/metrics` теперь доступен через `prometheus-fastapi-instrumentator`; unit тесты сохраняют Allure отчёт (`output/test-results/allure/`).
- `scripts/metrics/collect_dora.py` обновляет `docs/status/dora_history.md`; workflow `dora-metrics.yml` коммитит историю автоматически.
- Добавлен стек Prometheus/Grafana для локальной проверки SLO (`observability/docker-compose.observability.yml`, `make observability-up`, workflow `observability.yml`).
- Workflow `observability-test.yml` проверяет docker-compose стек (smoke-api + Prometheus + Grafana) в CI.
- Workflow `telegram-alert.yaml` отправляет уведомления в Telegram при падении Observability/DORA workflow.
- `make check-runtime` + скрипт `scripts/setup/check_runtime.py` проверяют наличие Python 3.11; добавлено руководство [`docs/setup/python_311.md`](docs/setup/python_311.md).
- Alertmanager и правила алертов для observability-стека (`observability/alertmanager.yml`, `observability/alerts.yml`, порт 9093, Telegram-конфигурация).
- Workflow `trufflehog.yml` выполняет дополнительное сканирование секретов (trufflesecurity/trufflehog) на push/PR и по расписанию.
- Добавлен инфраструктурный стек: kind-кластер (`infrastructure/kind/cluster.yaml`), Helm chart (`infrastructure/helm/1cai-stack`), Terraform шаблон (`infrastructure/terraform`), Jenkins pipeline (`infrastructure/jenkins/Jenkinsfile`) и GitLab CI (`infrastructure/gitlab/.gitlab-ci.yml`); документ [`docs/ops/devops_platform.md`](docs/ops/devops_platform.md).
- Добавлен Helm chart `infrastructure/helm/observability-stack` (Prometheus + Loki + Tempo + OTEL Collector + Grafana + Promtail) и make-цель `helm-observability`.

---

## [5.1.1] - 2025-11-07

### 🚀 Enhancements
- Marketplace API теперь использует Redis-кэш для `featured`/`trending` и категорий (TTL 5 минут).
- Добавлен планировщик (APScheduler) для периодического обновления кэшей и метрик.
- Реализовано per-user/IP rate limiting на основе Redis (глобальный middleware) + логирование контекста пользователя.
- Поддержка подписанных ссылок на загрузку плагинов через S3/MinIO (presigned URL, TTL 5 минут).
- `.env`/документация обновлены: новые переменные `USER_RATE_LIMIT_*`, `MARKETPLACE_CACHE_REFRESH_MINUTES`, `AWS_S3_*`.
- Введены service-to-service токены (`X-Service-Token`) и централизованный аудит действий модерации.
- Добавлены админские REST endpoints `/admin/users/{id}/roles|permissions`, CLI `scripts/manage_roles.py` и миграции для `user_roles`, `user_permissions`, `user_role_assignments`, `security_audit_log`.
- CI теперь выполняет `python scripts/run_migrations.py` перед интеграционными тестами.
- Добавлен REST endpoint `/admin/audit` для просмотра журнала безопасности с фильтрами и пагинацией.

### 🧪 Quality
- Новые unit-тесты для JWT AuthService и S3-пайплайна Marketplace.
- FAQ/Installation/Config гайды дополнены инструкциями по rate limiting и storage.
- README выделяет новые возможности Marketplace (JWT rate limiting, S3, Redis cache).
- Добавлен Python Setup Guide + тесты для audit logger/service tokens.

---

## [5.1.0] - 2025-11-06

### 🎉 Major Features Added

#### EDT-Parser Ecosystem
- **EDT Parser** for 1C configurations in EDT export format
- `edt_parser.py` - основной парсер (149 модулей, 213 справочников, 209 документов)
- `edt_parser_with_metadata.py` - парсер с извлечением метаданных
- Comprehensive test suite (5/5 tests passed, 99.4% success rate)
- Полный парсинг конфигурации ERPCPM:
  - 6,708 объектов
  - 117,349 методов
  - 338 млн символов кода
  - 99.93% успешность

#### ML Dataset Generator
- **Инструмент для создания ML датасетов** из ваших конфигураций 1С
- 5 категорий: API usage, business logic, data processing, UI, integration
- `create_ml_dataset.py` - скрипт генерации
- Автоматический enrichment с контекстом (module name, parameters, return types)
- Формат подходит для fine-tuning GPT/Llama/Qwen
- **Примечание:** Датасет НЕ включен в репозиторий - создается из ваших конфигураций

#### Analysis Tools Suite (5 scripts)
- `analyze_architecture.py` - анализ структуры конфигурации
- `analyze_dependencies.py` - построение графа зависимостей (2,291 узлов)
- `analyze_data_types.py` - анализ типов данных
- `extract_best_practices.py` - извлечение coding patterns
- `generate_documentation.py` - автоматическая документация

#### Comprehensive Audit Suite (4 scripts)
- `project_structure_audit.py` - аудит структуры (2,517 файлов)
- `code_quality_audit.py` - качество кода (complexity, docstrings, type hints)
- `architecture_audit.py` - модульность (540 модулей, 0 циклических зависимостей)
- `comprehensive_project_audit.py` - полный аудит (dependencies, tests, security)

### 🔐 Code Quality & Security

- **SQL queries** улучшены в `postgres_saver.py`
  - Добавлен whitelist разрешенных таблиц
  - Параметризированные запросы
- **Configuration management** улучшен
  - Environment variables для конфигурации
  - .env.example файлы для reference

### 🧹 Project Cleanup

- **Root directory** очищен: 115 → 27 файлов (-88 файлов)
- 88 файлов перемещены в `docs/reports/` и `docs/research/`
- **archive_package** очищен (520 файлов, 26 MB)
- Professional project structure
- Temporary session reports excluded from git

### 📝 Documentation & Architecture

- **Disclaimer** добавлен в README.md (English + Русский)
  - Указано что репозиторий НЕ содержит проприетарные данные 1С
  - Юридическая защита от claims
- **ARCHITECTURE_CURRENT_STATE.md** - текущее состояние архитектуры
- Disclaimer добавлен в 10 устаревших architecture файлов
- README файлы обновлены со ссылками на актуальную версию
- Все новые компоненты документированы

### 💻 Code Quality Improvements

- **Marketplace API** - 13 TODO обработаны
  - Добавлены helper функции для авторизации
  - Улучшены комментарии для production реализации
  - Добавлены проверки прав доступа
- **Type hints** coverage увеличен
- **Docstrings** улучшены

### 📊 Metrics & Statistics

**Проект:**
- 2,517 файлов
- 220,616 строк Python кода
- 539 Python файлов
- Grade: A- (88/100) after P0 fixes

**ERPCPM Analysis:**
- 149 общих модулей
- 213 справочников
- 209 документов
- 24,136 функций/процедур
- 580,049 строк кода

**Code Quality:**
- Cyclomatic complexity: 3.2 avg
- Docstring coverage: 82.8% (functions), 91.3% (classes)
- Type hints: 47.5%
- 0 циклических зависимостей ⭐

### 🐛 Bug Fixes

- i18n claims исправлены в README (было "400+ переводов" → стало "RU/EN для Telegram бота")
- Repository links обновлены на корректные
- Временные отчёты сессий удалены из git

## [Unreleased]

### Planned
- P1 Tasks: Рефакторинг сложных функций (108 функций с complexity >10)
- P2 Tasks: Type hints до 80%+, CI/CD setup
- Расширение EDT-Parser (регистры, отчёты, обработки)

## [0.1.0] - 2025-01-XX

### Added
- Project initialization
- Basic infrastructure setup
- Documentation framework

---

## Version History

- **v0.1.0** - Initial setup (Stage 0, Week 1)
- **v1.0.0** - Planned: Full release (Stage 6, Week 30)







