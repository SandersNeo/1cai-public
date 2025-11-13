# 🤖 1C AI Stack

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![Kubernetes](https://img.shields.io/badge/kubernetes-ready-326CE5.svg)](https://kubernetes.io/)
[![Status](https://img.shields.io/badge/status-production-green.svg)](CHANGELOG.md)
[![Documentation](https://img.shields.io/badge/docs-complete-brightgreen.svg)](docs/README.md)

> Платформа, которая собирает DevOps-, AI- и эксплуатационные практики вокруг 1C:Enterprise в одну управляемую систему: разбор конфигураций, MCP-инструменты, CI/CD, безопасность и наблюдаемость.
> Внутри — рабочие сервисы, make-таргеты и документация, которые мы используем каждый день для реальных 1С-ландшафтов.
>
> **С чего начать:**
> - [`Makefile`](Makefile) — сценарии запуска инфраструктуры, MCP и тестов;
> - [`docs/architecture/uml/`](docs/architecture/uml/) — PNG-диаграммы, обновляемые скриптами (`make render-uml`, [`scripts/docs/render_uml.py`](scripts/docs/render_uml.py));
> - [`docs/research/constitution.md`](docs/research/constitution.md) — правила проверки и стандарты разработки.

**Кому полезно:** DevOps-командам 1С, архитекторам платформы и ML/аналитикам, которым нужно быстрее внедрять изменения в продуктивные 1С-ландшафты.

### Что уже работает
- **Многослойный анализ конфигураций.** Парсер EDT, `bsl-language-server` и диагностические скрипты из [`src/`](src/) и [`scripts/analysis/`](scripts/analysis/) превращают 1C-конфигурации в метаданные, отчёты и графы зависимостей (см. [`docs/06-features/EDT_PARSER_GUIDE.md`](docs/06-features/EDT_PARSER_GUIDE.md)).
- **Автоматизация и MCP-инструменты.** [`src/ai/mcp_server.py`](src/ai/mcp_server.py), spec-driven workflow и готовые CLI помогают создавать задачи, генерировать код и запускать тесты из IDE или CI (см. [`docs/06-features/MCP_SERVER_GUIDE.md`](docs/06-features/MCP_SERVER_GUIDE.md)).
- **Промышленный контур.** Helm charts, Argo CD, Linkerd, Vault и Terraform-модули в [`infrastructure/`](infrastructure/) + регламенты в [`docs/ops/`](docs/ops/README.md) позволяют разворачивать и поддерживать стек в облаке без ручных «магических» шагов.

## Архитектура платформы

```mermaid
graph TB
    subgraph Users["👥 Пользователи"]
        Developer["👨‍💻 1C Developers<br/>Use IDE and automation"]
        Operator["👔 Business Stakeholders<br/>Consume dashboards, reports"]
    end

    subgraph Core["🔵 Core Services"]
        API["🌐 Graph API<br/>FastAPI<br/>GraphQL, REST, MCP endpoints"]
        RestGateway["⚡ Realtime Gateway<br/>Starlette, WebSocket"]
        Auth["🔐 Auth and RBAC<br/>OAuth2, JWT"]
        AdminPortal["🛡️ Admin Portal<br/>React, FastAPI"]
    end

    subgraph Workers["⚙️ Worker Tier"]
        Celery["🔍 Analysis Workers<br/>Celery"]
        MLPipelines["🤖 ML Pipelines<br/>Prefect, PyTorch"]
        ITSScraper["📰 ITS Scraper<br/>Async Python"]
        Orchestrator["🎯 Task Orchestrator<br/>Bash, scripts"]
    end

    subgraph DataStores["💾 Data Stores"]
        Postgres[("🐘 PostgreSQL<br/>Relational data, audit")]
        Neo4j[("🕸️ Neo4j<br/>Graph DB")]
        Qdrant[("🔍 Qdrant<br/>Vector DB")]
        Redis[("⚡ Redis<br/>Cache, queues")]
        Minio[("📦 MinIO<br/>Object Storage")]
    end

    subgraph Integrations["🔗 Integration Channels"]
        EDTPlugin["🔌 EDT Plugin<br/>Java"]
        n8nNode["🔄 n8n Node<br/>TypeScript"]
        TelegramBot["💬 Telegram Bot<br/>Python"]
        Marketplace["🏪 Marketplace<br/>BSL"]
    end

    subgraph Ops["📊 Operations"]
        Prometheus["📈 Prometheus<br/>Monitoring"]
        Grafana["📊 Grafana<br/>Dashboards"]
        Alertmanager["🚨 Alertmanager"]
        GitHubActions["⚙️ CI/CD<br/>GitHub Actions"]
    end

    Developer -->|Graph queries, MCP| API
    Developer -->|IDE commands| EDTPlugin
    Operator -->|Dashboards| Grafana

    API -->|Auth| Auth
    API -->|Persist| Postgres
    API -->|Graph| Neo4j
    API -->|Vector search| Qdrant
    API -->|Cache| Redis
    API -->|Jobs| Celery

    Celery -->|Update| Postgres
    Celery -->|Update| Neo4j
    Celery -->|Sync| Qdrant
    MLPipelines -->|Store| Minio

    EDTPlugin -->|Analysis| API
    n8nNode -->|Workflow| API
    TelegramBot -->|Chatops| API

    Prometheus -->|Metrics| API
    Prometheus -->|Alerts| Alertmanager
    Alertmanager -->|Escalations| TelegramBot

    classDef coreStyle fill:#e8f4ff,stroke:#0066cc,stroke-width:2px
    classDef integrationStyle fill:#fff4e6,stroke:#ff9900,stroke-width:2px
    classDef storeStyle fill:#f0f7ff,stroke:#0066cc,stroke-width:2px
    classDef opsStyle fill:#f6fdf3,stroke:#00cc66,stroke-width:2px

    class API,RestGateway,Auth,AdminPortal coreStyle
    class EDTPlugin,n8nNode,TelegramBot,Marketplace integrationStyle
    class Postgres,Neo4j,Qdrant,Redis,Minio storeStyle
    class Prometheus,Grafana,Alertmanager,GitHubActions opsStyle
```

> **Подробная версия:** [Полная интерактивная карта](docs/architecture/interactive-architecture.html) с фильтрами и поиском

## За 5 минут: пробный запуск

1. Установить Python 3.11, Docker и Docker Compose — подробности в [`docs/setup/python_311.md`](docs/setup/python_311.md).
2. Проверить окружение: `make check-runtime` (использует [`scripts/setup/check_runtime.py`](scripts/setup/check_runtime.py)).
3. Запустить минимальный стенд:
   ```bash
   make docker-up      # инфраструктура: БД, брокеры, Neo4j, Qdrant
   make migrate        # первичная миграция данных
   make servers        # Graph API + MCP server
   open http://localhost:6001/mcp
   ```
   > Для Windows есть аналоги в [`scripts/windows/`](scripts/windows/). После запуска доступен живой MCP endpoint, логи сервисов и тестовые данные — можно сразу проверять сценарии.

## Сценарии использования

| Роль | Первое действие | Ключевые материалы |
| ---- | ---------------- | ------------------ |
| DevOps / SRE | Пройти `make gitops-apply`, подключить Vault/Linkerd | [`docs/ops/devops_platform.md`](docs/ops/devops_platform.md), [`docs/ops/gitops.md`](docs/ops/gitops.md), [`docs/ops/service_mesh.md`](docs/ops/service_mesh.md), [`infrastructure/helm/1cai-stack`](infrastructure/helm/1cai-stack) |
| 1С-разработчик / архитектор | Разобрать конфигурацию и получить документацию | [`docs/06-features/EDT_PARSER_GUIDE.md`](docs/06-features/EDT_PARSER_GUIDE.md), [`scripts/analysis/generate_documentation.py`](scripts/analysis/generate_documentation.py), [`docs/architecture/README.md`](docs/architecture/README.md) |
| ML / аналитика | Сформировать датасет и прогнать проверки качества | [`docs/06-features/ML_DATASET_GENERATOR_GUIDE.md`](docs/06-features/ML_DATASET_GENERATOR_GUIDE.md), [`docs/06-features/TESTING_GUIDE.md`](docs/06-features/TESTING_GUIDE.md), [`scripts/analysis/`](scripts/analysis/) |
| Операционный менеджер / on-call | Подготовить регламенты и тренировки | [`docs/runbooks/dr_rehearsal_plan.md`](docs/runbooks/dr_rehearsal_plan.md), [`docs/process/oncall_rotations.md`](docs/process/oncall_rotations.md), [`docs/observability/SLO.md`](docs/observability/SLO.md) |

## Ключевые блоки платформы

| Направление | Что включено | Ссылки |
|-------------|--------------|--------|
| **MCP & AI tooling** | Генерация кода, анализ AST, MCP-инструменты | [`src/ai/`](src/ai/), [`docs/06-features/AST_TOOLING_BSL_LANGUAGE_SERVER.md`](docs/06-features/AST_TOOLING_BSL_LANGUAGE_SERVER.md), [`docs/06-features/MCP_SERVER_GUIDE.md`](docs/06-features/MCP_SERVER_GUIDE.md) |
| **Инфраструктура** | Helm charts, Terraform, Argo CD, Linkerd, Vault | [`infrastructure/helm/`](infrastructure/helm/), [`infrastructure/terraform/`](infrastructure/terraform/), [`infrastructure/argocd/`](infrastructure/argocd/), [`scripts/service_mesh/`](scripts/service_mesh/) |
| **Надёжность и наблюдаемость** | Runbooks, DR, DORA, Prometheus, Alertmanager | [`docs/runbooks/`](docs/runbooks/README.md), [`docs/process/`](docs/process/README.md), [`observability/`](observability/) |
| **Безопасность и FinOps** | Политики, проверки, отчёты, FinOps-скрипты | [`policy/`](policy/), [`scripts/security/`](scripts/security/), [`scripts/finops/`](scripts/finops/) |

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
  - Policy-as-code: `policy/` (Rego) + `scripts/security/run_policy_checks.sh` (Conftest Kubernetes + Terraform, Semgrep, Checkov/Trivy) → `make policy-check` / CI стадии.
  - Infrastructure scanners: `scripts/security/run_checkov.sh` (Checkov + Trivy) подключён в Jenkins/GitLab/Azure pipeline.
  - GitOps: `infrastructure/argocd/`, `scripts/gitops/*.sh`, make `gitops-apply`, `gitops-sync`.
  - Cloud readiness: `infrastructure/terraform/aws-eks/`, `infrastructure/terraform/azure-aks/`, Ansible bootstrap (`infrastructure/ansible/`).
  - Secrets: `scripts/secrets/aws_sync_to_vault.py`, `scripts/secrets/azure_sync_to_vault.py`, `scripts/secrets/apply_vault_csi.sh`.
  - Self-control: `scripts/checklists/preflight.sh`, make `preflight`.
- **FinOps**
  - Скрипты `scripts/finops/aws_cost_*`, `scripts/finops/azure_cost_to_slack.py`, `scripts/finops/aws_budget_check.py`, `scripts/finops/azure_budget_check.py`, `scripts/finops/teams_notify.py` — отчёты, бюджеты и Slack/Teams уведомления; дашборд `observability/grafana/dashboards/finops_cost.json`.
  - Workflow `.github/workflows/finops-report.yml` — ежедневный отчёт.
  - DR rehearsal: `docs/runbooks/dr_rehearsal_plan.md`, script `scripts/runbooks/dr_rehearsal_runner.py`, workflow `dr-rehearsal.yml`.

---

## 🔗 Integrations
- **IDE**: MCP сервер (Cursor/VS Code), EDT плагин (`edt-plugin/`).
- **Внешние инструменты**: alkoleft платформенные сервисы, yaxunit, GitHub Spec Kit (в работе).
- **ITS Scraper**: асинхронный сбор статей, версионирование (`integrations/its_scraper`).
- **Telegram / n8n / OCR**: дополнительные модули в `src/` и `integrations/`.

---

## 📚 Documentation Hub

Полный индекс: [`docs/README.md`](docs/README.md). Ключевые разделы:
- **Setup & Runtime**
  - [`docs/setup/python_311.md`](docs/setup/python_311.md) — установка Python 3.11 и проверка среды.
  - `scripts/setup/check_runtime.py` + `make check-runtime` — автоматическая проверка версии Python.
- **Infrastructure & DevOps**
  - [`docs/ops/devops_platform.md`](docs/ops/devops_platform.md) — стратегия DevOps-платформы.
  - [`docs/ops/gitops.md`](docs/ops/gitops.md) — GitOps с Argo CD.
  - [`docs/ops/ansible.md`](docs/ops/ansible.md) — bootstrap инфраструктуры Ansible.
  - [`docs/ops/service_mesh.md`](docs/ops/service_mesh.md) — Istio blueprint.
  - [`infrastructure/service-mesh/linkerd`](infrastructure/service-mesh/linkerd) — альтернативный service mesh.
  - [`docs/ops/chaos_engineering.md`](docs/ops/chaos_engineering.md) — Litmus chaos сценарии.
  - [`docs/ops/vault.md`](docs/ops/vault.md) — Vault & secret management.
  - [`docs/ops/azure_devops.md`](docs/ops/azure_devops.md) — Azure DevOps pipeline.
  - [`docs/ops/finops.md`](docs/ops/finops.md) — FinOps и контроль затрат (`make finops-slack`, workflow `finops-report.yml`).
  - [`docs/ops/self_control.md`](docs/ops/self_control.md) — самоконтроль инженера (`make preflight`).
  - `infrastructure/kind/cluster.yaml` — локальный Kubernetes.
  - `infrastructure/helm/1cai-stack` — Helm chart приложения.
  - `infrastructure/helm/observability-stack` — Prometheus/Loki/Tempo/Grafana/OTEL.
  - `infrastructure/service-mesh/istio` — IstioOperator профиль.
  - `infrastructure/chaos/litmus` — Litmus Chaos эксперименты.
  - `infrastructure/argocd/` — manifests для Argo CD (GitOps, Linkerd ApplicationSet).
  - `infrastructure/terraform` — Terraform конфигурация для Helm релиза.
  - `infrastructure/terraform/aws-eks` — Terraform модуль EKS (AWS).
  - `infrastructure/terraform/azure-aks` — Terraform модуль AKS (Azure).
  - `infrastructure/terraform/azure-keyvault` — Terraform модуль Key Vault.
  - `scripts/service_mesh/linkerd/bootstrap_certs.sh` — генерация trust anchors/issuer.
  - `scripts/service_mesh/linkerd/` — bootstrap/rotate certs, managed identity, CI smoke (`linkerd-smoke.yml`).
  - Make: `linkerd-install`, `linkerd-rotate-certs`, `linkerd-smoke`.
  - `infrastructure/azure/azure-pipelines.yml` — Azure DevOps pipeline.
  - `infrastructure/vault/` — политики, скрипты, SecretProviderClass для Vault (`make vault-csi-apply`, sync скрипты).
  - `scripts/secrets/aws_sync_to_vault.py` — синхронизация AWS Secrets Manager → Vault.
  - `infrastructure/jenkins/Jenkinsfile`, `infrastructure/gitlab/.gitlab-ci.yml` — многостадийные pipeline.
  - [`docs/security/policy_as_code.md`](docs/security/policy_as_code.md) — Rego-политики, Conftest, Semgrep.
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
  - [`docs/research/alkoleft_todo.md`](docs/research/alkoleft_todo.md) — roadmap и планы развития.
  - [`docs/research/constitution.md`](docs/research/constitution.md) — конституция правил проверки.

## Чего ждать дальше

- Расширение spec-driven практик и интеграции с GitHub Spec Kit — см. [`docs/research/spec_kit_analysis.md`](docs/research/spec_kit_analysis.md), [`docs/research/constitution.md`](docs/research/constitution.md).
- Новые тестовые раннеры (YAxUnit, edt-test-runner) и сценарии — слежение в [`docs/06-features/TESTING_GUIDE.md`](docs/06-features/TESTING_GUIDE.md), [`docs/research/alkoleft_todo.md`](docs/research/alkoleft_todo.md).
- UI/презентационный слой для быстрой навигации — наработки в [`docs/09-archive/ui-ux-backup/`](docs/09-archive/ui-ux-backup/).

## Документация и ресурсы

- Полный индекс: [`docs/README.md`](docs/README.md).
- Архитектура: [`docs/architecture/README.md`](docs/architecture/README.md), Structurizr DSL и PlantUML лежат в [`docs/architecture/c4/`](docs/architecture/c4/) и [`docs/architecture/uml/`](docs/architecture/uml/).
- Практики тестирования и качества: [`docs/06-features/TESTING_GUIDE.md`](docs/06-features/TESTING_GUIDE.md), тестовые сценарии — в [`scripts/tests/`](scripts/tests/).
- Политики безопасности: [`docs/security/policy_as_code.md`](docs/security/policy_as_code.md), workflows [`.github/workflows/secret-scan.yml`](.github/workflows/secret-scan.yml), [`.github/workflows/trufflehog.yml`](.github/workflows/trufflehog.yml).
- Наблюдаемость и метрики: [`observability/docker-compose.observability.yml`](observability/docker-compose.observability.yml), [`docs/observability/SLO.md`](docs/observability/SLO.md), [`docs/status/dora_history.md`](docs/status/dora_history.md).

## Как взаимодействовать

- Бэклог и актуальные задачи — [`docs/research/alkoleft_todo.md`](docs/research/alkoleft_todo.md).
- Issues и pull-requests приветствуются; ориентируйтесь на [recent commits](https://github.com/DmitrL-dev/1cai/commits/main) и [`docs/05-development/README.md`](docs/05-development/README.md) + [`docs/05-development/CHANGELOG.md`](docs/05-development/CHANGELOG.md).
- Перед изменением диаграмм обязательно запускайте `make render-uml` (workflow «PlantUML Render Check» использует те же скрипты).
- Для оперативных вопросов — внутренний канал команды (контакты описаны в приватной документации).