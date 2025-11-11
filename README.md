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
   - Python 3.11 (обязательно)
   - Docker + Docker Compose (для dev окружения)
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

---

## 🔗 Integrations
- **IDE**: MCP сервер (Cursor/VS Code), EDT плагин (`edt-plugin/`).
- **Внешние инструменты**: alkoleft платформенные сервисы, yaxunit, GitHub Spec Kit (в работе).
- **ITS Scraper**: асинхронный сбор статей, версионирование (`integrations/its_scraper`).
- **Telegram / n8n / OCR**: дополнительные модули в `src/` и `integrations/`.

---

## 📚 Documentation Hub
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
  - [`docs/research/alkoleft_todo.md`](docs/research/alkoleft_todo.md) — интеграция экосистемы @alkoleft с приоритетами.
  - [`docs/research/github_monitoring_plan.md`](docs/research/github_monitoring_plan.md) — мониторинг внешних репозиториев и уведомления.
  - [`docs/research/archive_tools_assessment.md`](docs/research/archive_tools_assessment.md) — анализ архивных утилит и кандидаты для CLI.
  - [`docs/research/release_playbook.md`](docs/research/release_playbook.md) — процесс выпуска, теги, GitHub Release.

---

## 📝 Recent Updates
- **[Unreleased]** – см. [`CHANGELOG.md`](CHANGELOG.md)
  - Интеграция `bsl-language-server` (docker-compose, make-таргеты, диагностика)
  - Новый гид по AST tooling (`docs/06-features/AST_TOOLING_BSL_LANGUAGE_SERVER.md`)
  - Перестройка README и документационного хаба
  - Исследование GitHub Spec Kit (план внедрения)
- **5.1.1 (2025-11-07)** — улучшения Marketplace API, Redis caching, rate limiting
- **5.1.0 (2025-11-06)** — масштабный выпуск: EDT parser, ML dataset generator, audit suite, ITIL анализ

Полный список изменений — в [`CHANGELOG.md`](CHANGELOG.md).

---

## 💬 Support
- Issues: [GitHub Issues](https://github.com/DmitrL-dev/1cai-public/issues)
- Telegram: см. [`docs/SUPPORT.md`](docs/SUPPORT.md)
- FAQ: [`docs/FAQ.md`](docs/FAQ.md)

---

## 🙏 Credits & Acknowledgements
- **1c-syntax/bsl-language-server** — язык-сервер BSL (AST, диагностика).
- **BIA (yaxunit, edt-test-runner, precommit4onec)** — экосистема тестирования 1С.
- **GitHub/spec-kit** — идеи для spec-driven development и автоматизации планирования.
- **alkoleft** — platform context exporter, ones_doc_gen, MCP инструменты.

Благодарим авторов открытых решений, которые мы используем и расширяем. Все сторонние проекты упомянуты в документации и changelog.

---

© 2025 1C AI Stack. MIT License.
