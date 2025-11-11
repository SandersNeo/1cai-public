# 🤖 1C AI Stack

**AI-powered development platform for 1C:Enterprise**

- 🧠 AI ассистенты и MCP-сервер для IDE (Cursor, VS Code, EDT)
- 🔍 Глубокий анализ конфигураций (парсинг EDT, AST, граф зависимостей)
- 📚 Автоматическая документация и архитектурные артефакты (Structurizr, ADR)
- ✅ Тесты и best practices (YAxUnit, CI, статический анализ)

## 🧭 Навигация
- [Quick Start](#-quick-start)
- [Feature Highlights](#-feature-highlights)
- [AI Tooling & Automation](#-ai-tooling--automation)
- [Architecture & Documentation](#-architecture--documentation)
- [Testing & Quality](#-testing--quality)
- [Integrations](#-integrations)
- [Documentation Hub](#-documentation-hub)
- [Recent Updates](#-recent-updates)
- [Support](#-support)
- [Credits & Acknowledgements](#-credits--acknowledgements)
- [Constitution](docs/research/constitution.md)

---

## 🚀 Quick Start
1. **Установите зависимости**
   - Python 3.11 (обязательно) — инструкция: [`docs/setup/python_311.md`](docs/setup/python_311.md)
   - Docker + Docker Compose (для dev окружения)
   - Проверка среды: `make check-runtime`
2. **Клонируйте репозиторий**
3. **Запустите инфраструктуру**
```bash
   make docker-up           # базы данных, Redis, Neo4j, Qdrant
   make migrate             # миграции JSON → PostgreSQL → Neo4j/Qdrant
   make servers             # Graph API + MCP сервер
   make bsl-ls-up           # bsl-language-server для AST (порт 8081 → 8080)
   make bsl-ls-check        # health + тестовый parse
   ```
   > На Windows без `make` используйте скрипты из `scripts/windows/` (например, `pwsh scripts/windows/bsl-ls-up.ps1` и `feature-init.ps1`).
4. **Откройте IDE**
   - Cursor/VS Code через MCP (`http://localhost:6001/mcp`)
   - EDT плагин — билд в `edt-plugin/`

Подробности: [`docs/06-features/AST_TOOLING_BSL_LANGUAGE_SERVER.md`](docs/06-features/AST_TOOLING_BSL_LANGUAGE_SERVER.md), [`docs/architecture/README.md`](docs/architecture/README.md).

---

## 🌟 Feature Highlights

### Конфигурационный анализ
- EDT-parser: статистика объектов, граф зависимостей, best practices.
- Документация из парсинга: [`scripts/analysis/generate_documentation.py`](scripts/analysis/generate_documentation.py).
- Гайды: [`docs/06-features/EDT_PARSER_GUIDE.md`](docs/06-features/EDT_PARSER_GUIDE.md), [`docs/06-features/ML_DATASET_GENERATOR_GUIDE.md`](docs/06-features/ML_DATASET_GENERATOR_GUIDE.md).

### Автоматизация и оркестрация
- MCP-сервер (`src/ai/mcp_server.py`) с инструментами для поиска метаданных, генерации кода, запуска тестов.
- Интеграция с внешними MCP (platform context, тест-раннеры).
- Workflow запуска анализа: `make docker-up` → `make migrate` → `make generate-docs`.

### Документация и архитектура
- Structurizr DSL + PlantUML (C4, динамика, операции, безопасность).
- ADR-реестр (`docs/architecture/adr/`).
- Автоматический рендер диаграмм (`make render-uml`, GitHub Actions).

### AI & MCP tooling
- MCP server, bsl-language-server, spec-driven workflow (см. ниже).
- Создание задач и планов на основе спецификаций (совместимо с GitHub Spec Kit — см. анализ).

---

## 🤖 AI Tooling & Automation
- **bsl-language-server**: сервис AST, make-таргеты `bsl-ls-*`, health-check, fallback в `BSLASTParser`.
  - План интеграции: [`docs/research/bsl_language_server_plan.md`](docs/research/bsl_language_server_plan.md).
  - Детальный гайд: [`docs/06-features/AST_TOOLING_BSL_LANGUAGE_SERVER.md`](docs/06-features/AST_TOOLING_BSL_LANGUAGE_SERVER.md).
- **Spec-driven development** (по мотивам [github/spec-kit](https://github.com/github/spec-kit)):
  - Анализ и предложения: [`docs/research/spec_kit_analysis.md`](docs/research/spec_kit_analysis.md).
  - Конституция правил проверки: [`docs/research/constitution.md`](docs/research/constitution.md).
  - Шаблоны и CLI: `templates/`, `scripts/research/init_feature.py`, make-таргеты `feature-init` и `feature-validate`.
- **MCP инструменты**: поиск метаданных, генерация кода, запуск тестов.
- **Automation scripts**: `scripts/context/export_platform_context.py`, `scripts/context/generate_docs.py`, `scripts/docs/create_adr.py`.
- **Monitoring automation**: `scripts/monitoring/github_monitor.py` + workflow `github-monitor.yml` — ежедневный snapshot зависимостей.
- **Release automation**: `scripts/release/create_release.py`, make `release-*`, workflow `release.yml` — генерация заметок, тегов, публикация релизов.
- **Quality metrics**: `scripts/metrics/collect_dora.py`, workflow `dora-metrics.yml` — еженедельные DORA-показатели.

---

## 🏛 Architecture & Documentation
- **High-Level Design**: [`docs/architecture/01-high-level-design.md`](docs/architecture/01-high-level-design.md)
- **Structurizr DSL**: [`docs/architecture/c4/workspace.dsl`](docs/architecture/c4/workspace.dsl)
- **Диаграммы (PNG)**: `docs/architecture/uml/**` (C4, data, dynamics, operations, security)
- **ADR**: `docs/architecture/adr/`, см. `ADR-0001… ADR-0005`
- **Automated render**: `make render-uml`, workflow `.github/workflows/uml-render-check.yml`

---

## ✅ Testing & Quality
- **YAxUnit + EDT runner** (в планах расширения через репозитории BIA: yaxunit, edt-test-runner).
- `make test-bsl` (см. `scripts/tests/run_bsl_tests.py`).
- Статический анализ, best practices, проверка зависимостей.
- Сторожевые скрипты: `scripts/audit/*`, `scripts/analysis/*`.
- Справочник по тестам: [`docs/06-features/TESTING_GUIDE.md`](docs/06-features/TESTING_GUIDE.md).
- Smoke проверки: `make smoke-tests`, CI job `smoke-tests`, артефакты pytest (`output/test-results`).
- Наблюдаемость: `/metrics` (Prometheus), SLO/Runbooks (`docs/observability/SLO.md`, `docs/runbooks/alert_slo_runbook.md`), автоматические отчёты DORA.
- **Secret scanning & Security**
  - Workflows `secret-scan.yml` (Gitleaks) и `trufflehog.yml` (Trufflehog) — регулярное сканирование репозитория на утечки токенов.

---

## 🔗 Integrations
- **IDE**: MCP сервер (Cursor/VS Code), EDT плагин (`edt-plugin/`).
- **Внешние инструменты**: alkoleft платформенные сервисы, yaxunit, GitHub Spec Kit (в работе).
- **ITS Scraper**: асинхронный сбор статей, версионирование (`integrations/its_scraper`).
- **Telegram / n8n / OCR**: дополнительные модули в `src/` и `integrations/`.

---

## 📚 Documentation Hub
- **Setup & Runtime**
  - [`docs/setup/python_311.md`](docs/setup/python_311.md) — установка Python 3.11 и проверка среды.
  - `scripts/setup/check_runtime.py` + `make check-runtime` — автоматическая проверка версии Python.
- **Infrastructure & DevOps**
  - [`docs/ops/devops_platform.md`](docs/ops/devops_platform.md) — стратегия DevOps-платформы.
  - `infrastructure/kind/cluster.yaml` — локальный Kubernetes.
  - `infrastructure/helm/1cai-stack` — Helm chart приложения.
  - `infrastructure/helm/observability-stack` — Prometheus/Loki/Tempo/Grafana/OTEL.
  - `infrastructure/terraform` — Terraform конфигурация для Helm релиза.
  - `infrastructure/jenkins/Jenkinsfile`, `infrastructure/gitlab/.gitlab-ci.yml` — многостадийные pipeline для Jenkins и GitLab.
- **Feature Guides**
  - [`docs/06-features/AST_TOOLING_BSL_LANGUAGE_SERVER.md`](docs/06-features/AST_TOOLING_BSL_LANGUAGE_SERVER.md) — запуск и диагностика bsl-language-server, fallback сценарии.
  - [`docs/06-features/MCP_SERVER_GUIDE.md`](docs/06-features/MCP_SERVER_GUIDE.md) — эндпоинты MCP, переменные окружения, troubleshooting.
  - [`docs/06-features/TESTING_GUIDE.md`](docs/06-features/TESTING_GUIDE.md) — матрица тестов, команды pytest/k6, CI-джобы.
  - [`docs/06-features/EDT_PARSER_GUIDE.md`](docs/06-features/EDT_PARSER_GUIDE.md) — разбор EDT XML, метрики и сценарии анализа.
  - [`docs/06-features/ML_DATASET_GENERATOR_GUIDE.md`](docs/06-features/ML_DATASET_GENERATOR_GUIDE.md) — подготовка ML датасетов и пайплайн обучения.
- **Operations & Tooling**
  - [`docs/scripts/README.md`](docs/scripts/README.md) — карта CLI/скриптов, spec-driven workflow, Windows альтернативы, release tooling.
- **Observability**
  - [`docs/observability/SLO.md`](docs/observability/SLO.md) — целевые показатели доступности и латентности.
  - [`docs/runbooks/alert_slo_runbook.md`](docs/runbooks/alert_slo_runbook.md) — действия при нарушении SLO.
  - [`docs/status/dora_history.md`](docs/status/dora_history.md) — автоматическая история DORA метрик (weekly).
  - Workflow `observability.yml` — напоминание об интеграции SLO/метрик.
  - `make observability-up` → локальный Prometheus/Grafana/Alertmanager стек (см. `observability/docker-compose.observability.yml`), проверяется CI (`observability-test.yml`).
  - `make helm-observability` → установка Kubernetes-стека наблюдаемости (Prometheus + Loki + Tempo + Grafana + OTEL) из `infrastructure/helm/observability-stack`.
  - Alertmanager конфигурация: `observability/alertmanager.yml` + правила `observability/alerts.yml` (Telegram; требуются `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`).
  - Telegram оповещения: workflow `telegram-alert.yaml` (требует `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`).
- **Architecture**
  - [`docs/architecture/README.md`](docs/architecture/README.md) — обзор C4, операции и ссылки на ADR.
  - [`docs/architecture/adr/`](docs/architecture/adr/) — реестр решений, статусы и история изменений.
  - [`docs/architecture/uml/`](docs/architecture/uml/) — PlantUML диаграммы (структура, потоки, безопасность).
- **Parsers & Documentation**
  - [`docs/06-features/EDT_PARSER_GUIDE.md`](docs/06-features/EDT_PARSER_GUIDE.md) — парсинг конфигураций, метаданные.
  - [`docs/06-features/ML_DATASET_GENERATOR_GUIDE.md`](docs/06-features/ML_DATASET_GENERATOR_GUIDE.md) — генерация обучающих наборов.
  - [`docs/06-features/ITS_SCRAPER.md`](docs/03-integrations/ITS_SCRAPER.md) — сбор данных ITS и обновление базы знаний.
- **Research & Plans**
  - [`docs/research/README_LOCAL.md`](docs/research/README_LOCAL.md) — ежедневные статусы и подготовка публикации.
  - [`