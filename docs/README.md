# Documentation Hub

Быстрая навигация по основным блокам документации. Используйте этот индекс как стартовую точку (а [`research/README_LOCAL.md`](./research/README_LOCAL.md) — для ежедневных статусов).

## 1. Setup & Runtime
- [Установка Python 3.11](./setup/python_311.md) — установка Python 3.11.
- [Проверка runtime](../scripts/setup/check_runtime.py) + `make check-runtime` — автоматическая проверка версии Python.
- [Справочник CLI-скриптов](./scripts/README.md) — справочник CLI-скриптов.
- `scripts/ba/requirements_cli.py` — извлечение требований (см. `make ba-extract`).

## 2. Infrastructure & Operations
- Стратегия DevOps: [DevOps Platform](./ops/devops_platform.md).
- **Kubernetes кластеры:**
  - [Kind cluster (локально)](../infrastructure/kind/cluster.yaml) — локальный Kubernetes.
- **Helm Charts:**
  - [1cai-stack](../infrastructure/helm/1cai-stack) — Helm chart приложения.
  - [observability-stack](../infrastructure/helm/observability-stack) — Prometheus/Loki/Tempo/Grafana/OTEL.
- **Service Mesh:**
  - [Istio профиль](../infrastructure/service-mesh/istio) — IstioOperator профиль.
  - [Linkerd скрипты](../scripts/service_mesh/linkerd/) — bootstrap/rotate certs, managed identity, CI smoke.
  - [Linkerd bootstrap certs](../scripts/service_mesh/linkerd/bootstrap_certs.sh) — генерация trust anchors/issuer.
  - Make: `linkerd-install`, `linkerd-rotate-certs`, `linkerd-smoke`.
- **Chaos Engineering:**
  - [Litmus эксперименты](../infrastructure/chaos/litmus) — Litmus Chaos эксперименты.
- **GitOps:**
  - GitOps/Argo CD: [GitOps Guide](./ops/gitops.md), [Argo CD manifests](../infrastructure/argocd/).
- **Terraform:**
  - [Terraform конфигурация](../infrastructure/terraform) — Terraform конфигурация для Helm релиза.
  - [AWS EKS модуль](../infrastructure/terraform/aws-eks) — Terraform модуль EKS (AWS).
  - [Azure AKS модуль](../infrastructure/terraform/azure-aks) — Terraform модуль AKS (Azure).
  - [Azure Key Vault модуль](../infrastructure/terraform/azure-keyvault) — Terraform модуль Key Vault.
- **Secrets & Vault:**
  - Vault & secrets: [Vault Guide](./ops/vault.md), [Vault конфигурация](../infrastructure/vault/).
  - [AWS Secrets sync](../scripts/secrets/aws_sync_to_vault.py) — синхронизация AWS Secrets Manager → Vault.
- **CI/CD:**
  - [Azure DevOps pipeline](../infrastructure/azure/azure-pipelines.yml) — Azure DevOps pipeline.
  - [Jenkins pipeline](../infrastructure/jenkins/Jenkinsfile), [GitLab CI](../infrastructure/gitlab/.gitlab-ci.yml) — многостадийные pipeline.
- FinOps & Observability: [FinOps](./ops/finops.md), [SLO](./observability/SLO.md).
- Runbooks: [Alert SLO Runbook](./runbooks/alert_slo_runbook.md), [DR Rehearsal Plan](./runbooks/dr_rehearsal_plan.md).
- Процессы: [Process Guide](./process/README.md) — on-call, RFC, postmortem.

## 3. Architecture & Research
- High-level дизайн, C4: [Architecture Overview](./architecture/README.md).
- ADR: [Architecture Decision Records](./architecture/adr/).
- Исследования и планы: [Research Local](./research/README_LOCAL.md), [Spec Kit Analysis](./research/spec_kit_analysis.md), [Job Market BA](./research/job_market_business_analyst.md), [BA Agent Roadmap](./research/ba_agent_roadmap.md), [Alkoleft Todo](./research/alkoleft_todo.md).

## 4. Feature Guides
- MCP сервер и AI tooling: [MCP Server Guide](./06-features/MCP_SERVER_GUIDE.md).
- AST tooling: [AST Tooling BSL Language Server](./06-features/AST_TOOLING_BSL_LANGUAGE_SERVER.md).
- Парсеры, ML, интеграции: раздел [`06-features/`](./06-features/).

## 5. Automation & CI
- Workflows GitHub Actions: [`.github/workflows/`](../.github/workflows/) (`linkerd-smoke.yml`, `linkerd-chaos.yml`, `dr-rehearsal.yml`, `finops-report.yml`, `chaos-validate.yml` и др.).
- Make targets: см. [`Makefile`](../Makefile) (quick filter: `make help`).
- **CI/CD Pipelines:**
  - [Jenkins pipeline](../infrastructure/jenkins/Jenkinsfile) — многостадийный pipeline.
  - [GitLab CI](../infrastructure/gitlab/.gitlab-ci.yml) — многостадийный pipeline.
  - [Azure DevOps pipeline](../infrastructure/azure/azure-pipelines.yml) — Azure DevOps pipeline.

## 6. Governance & Compliance
- Конституция: [Constitution](./research/constitution.md).
- Policy-as-code: [Policy as Code](./security/policy_as_code.md), [`policy/kubernetes/`](../policy/kubernetes/), [`policy/terraform/`](../policy/terraform/).

## 7. Changelog & Releases
- Изменения: [CHANGELOG.md](../CHANGELOG.md).
- Release automation: `scripts/release/create_release.py`, workflow `release.yml`.

## 8. Business Analyst Platform
- [BA Guide](./06-features/BUSINESS_ANALYST_GUIDE.md) — сценарии агента, структура API.
- [Integration Plan](./07-integrations/BA_INTEGRATION_PLAN.md) — Jira/Confluence/Docflow/PowerBI и требования к секретам.
- [E2E Matrix](./08-e2e-tests/BA_E2E_MATRIX.md) и [Assessment](./assessments/BA_ASSESSMENT.md) — тестовые сценарии и критерии готовности.
- Скрипты и пайплайны: `scripts/ba_assessment/`, `scripts/ba_pipeline/`, `scripts/ba_scenarios/`.

## 9. Resiliency & Offline Mode
- [LLM Blocking Resilience Plan](../analysis/llm_blocking_resilience_plan.md) — регламент действий при отключении интернета / блокировке провайдеров.
- Конфигурации: [`config/llm_gateway_simulation.yaml`](../config/llm_gateway_simulation.yaml), [`config/llm_providers.yaml`](../config/llm_providers.yaml).
- Отчёты и шаблоны: [`docs/templates/offline_incident_report.md`](./templates/offline_incident_report.md), [`docs/stage-0/manual-sync.md`](./stage-0/manual-sync.md).
- Тесты/хаос-скрипты: `scripts/tests/llm_smoke.py`, `scripts/tests/run_offline_dry_run.py`, `scripts/chaos/block_jira.sh`.
# 📚 Документация 1C AI Stack

**Версия:** 5.1.0  
**Обновлено:** 17 ноября 2025  
**Статус:** Production Ready ✅

---

## 🚀 БЫСТРАЯ НАВИГАЦИЯ

| Задача | Документация |
|--------|--------------|
| **🎯 Быстрый старт** | [Quick Start](./01-getting-started/START_HERE.md) |
| **⚠️ Системные правила** | [System Prompt](./SYSTEM_PROMPT.md) |
| **🏗️ Архитектура** | [Architecture Overview](./02-architecture/ARCHITECTURE_OVERVIEW.md) |
| **🛠️ Технологический стек** | [Technology Stack](./02-architecture/TECHNOLOGY_STACK.md) |
| **🤖 AI Агенты** | [AI Agents](./03-ai-agents/README.md) |
| **⚡ Code Execution (NEW!)** | [Code Execution](./08-code-execution/README.md) |
| **📋 ITIL/ITSM (NEW!)** | [ITIL Analysis](./07-itil-analysis/README.md) |
| **📦 Deployment** | [Deployment Guide](./04-deployment/README.md) |
| **💻 Development** | [Development Guide](./05-development/README.md) |
| **🎁 Специальные фичи** | [Features](./06-features/) |
| **🔗 n8n интеграция** | [n8n Integration](./06-features/n8n-integration.md) |
| **🔒 Security automation (NEW!)** | [Security Agent Framework](../security/agent_framework/README.md) |
| **🎬 Showcase / Use cases** | [Case Studies](./CASE_STUDIES.md) |
| **🔑 Auth API** | [Auth endpoints](./API_REFERENCE.md#-auth-api) |

---

## 📂 СТРУКТУРА ДОКУМЕНТАЦИИ

```
docs/
├── README.md                       ← Вы здесь
├── SYSTEM_PROMPT.md                ← ⚠️ СИСТЕМНЫЕ ПРАВИЛА (System Rules)
│
├── 01-getting-started/             🚀 Быстрый старт
│   ├── START_HERE.md               ← Начать здесь!
│   ├── quickstart.md
│   ├── DEPLOYMENT_INSTRUCTIONS.md
│   └── telegram-setup.md
│
├── 02-architecture/                🏗️ Архитектура
│   ├── README.md
│   ├── ARCHITECTURE_OVERVIEW.md    ← Обзор архитектуры
│   ├── TECHNOLOGY_STACK.md         ← Полный стек технологий
│   ├── IMPLEMENTATION_PLAN.md
│   └── adr/                        (Architecture Decision Records)
│
├── 03-ai-agents/                   🤖 AI Агенты
│   ├── README.md
│   ├── FINAL_PROJECT_SUMMARY.md    ← 8 AI агентов, ROI €309K/год
│   ├── SQL_OPTIMIZER_COMPLETE.md
│   └── TECH_LOG_INTEGRATION_COMPLETE.md
│
├── 04-deployment/                  📦 Развертывание
│   ├── README.md
│   ├── PRODUCTION_DEPLOYMENT.md
│   └── kubernetes/
│
├── 05-development/                 💻 Разработка
│   ├── README.md
│   └── CHANGELOG.md
│
├── 06-features/                    🎁 Специальные возможности
│   ├── VOICE_QUERIES.md            (Голосовые запросы)
│   ├── OCR_INTEGRATION.md          (Распознавание документов)
│   ├── I18N_GUIDE.md               (Мультиязычность)
│   └── BSL_FINETUNING_GUIDE.md     (Fine-tuning модели)
│
├── 07-itil-analysis/               📋 ITIL/ITSM (NEW!)
│   ├── README.md
│   ├── ITIL_EXECUTIVE_SUMMARY.md   ← Management summary
│   ├── ITIL_ACTION_PLAN.md         ← Детальный план
│   ├── ITIL_APPLICATION_REPORT.md  (60+ стр)
│   └── ITIL_VISUAL_OVERVIEW.md
│
├── 08-code-execution/              ⚡ Code Execution (NEW!)
│   ├── README.md
│   └── IMPLEMENTATION_COMPLETE.md
│
└── archive/                        📦 Архив
    ├── sessions/                   (Old session reports)
    ├── research-backup/            (Research files)
    └── old-summaries/              (Old versions)
```

---

## 🎯 ПО РОЛЯМ

### 👔 Для Management

**Start here:**
1. [ITIL Executive Summary](./07-itil-analysis/ITIL_EXECUTIVE_SUMMARY.md) - бизнес-кейс
2. [AI Agents ROI](./03-ai-agents/FINAL_PROJECT_SUMMARY.md) - €309K/год
3. [Architecture Overview](./02-architecture/ARCHITECTURE_OVERVIEW.md) - что имеем

**Time:** 30 минут

---

### 👨‍💻 Для Developers

**Start here:**
1. [Quick Start](./01-getting-started/START_HERE.md) - начать работу
2. [Code Execution Guide](./08-code-execution/README.md) - NEW!
3. [AI Agents Guide](./03-ai-agents/README.md) - использование агентов
4. [Development Guide](./05-development/README.md) - контрибьюция

**Time:** 2 часа

---

### ⚙️ Для DevOps

**Start here:**
1. [Deployment Guide](./04-deployment/README.md)
2. [Production Deployment](./04-deployment/PRODUCTION_DEPLOYMENT.md)
3. [Kubernetes](./04-deployment/kubernetes/)
4. [Code Execution Setup](./08-code-execution/README.md)

**Time:** 3 часа

---

### 📋 Для Service Manager

**Start here:**
1. [ITIL Analysis](./07-itil-analysis/README.md) - overview
2. [ITIL Action Plan](./07-itil-analysis/ITIL_ACTION_PLAN.md) - детальный план
3. [ITIL Visual Overview](./07-itil-analysis/ITIL_VISUAL_OVERVIEW.md) - диаграммы

**Time:** 2 часа

---

## 🆕 Что нового (Nov 17, 2025)

### Scenario Hub & Unified Change Graph
- ✅ Scenario Recommender & Impact Analyzer с автоматическим построением графа из 1С кода
- ✅ LLM Provider Abstraction для унификации работы с разными провайдерами
- ✅ Intelligent Cache с контекстной инвалидацией и метриками
- ✅ Unified CLI Tool для работы с платформой
- ✅ Performance Benchmarks и Prometheus метрики для всех новых компонентов
- ✅ E2E тесты и архитектурная документация (UML-схемы, ADR)

---

## 🆕 Что нового (Nov 6, 2025)

### Code Execution with MCP
- ✅ Deno sandbox environment
- ✅ 98.7% token savings
- ✅ PII protection (152-ФЗ)
- ✅ Progressive disclosure
- ✅ Skills system

**Docs:** [08-code-execution/](./08-code-execution/)

### ITIL/ITSM Analysis & Planning
- ✅ Полный анализ применения ITIL
- ✅ План на 12 месяцев
- ✅ ROI 458-4900%
- ✅ Топ-5 quick wins

**Docs:** [07-itil-analysis/](./07-itil-analysis/)

---

## 📊 Метрики проекта

### Текущее состояние:
- **Готовность:** 99.5%
- **LOC:** ~52,500
- **Документов:** ~60 (после cleanup)
- **AI Agents:** 8 (ROI €309K/год)
- **Databases:** 5
- **Docker Services:** 18

### Impact:
- **Token savings:** 98.7% (Code Execution)
- **ITIL ROI:** 458-4900%
- **Combined savings:** ~$430K/год

---

## 🔗 Внешние ресурсы

### Технологии:
- [FastAPI](https://fastapi.tiangolo.com/)
- [Neo4j](https://neo4j.com/)
- [Qdrant](https://qdrant.tech/)
- [Deno](https://deno.land/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Python Setup Guide](01-getting-started/python-setup.md)

### Best Practices:
- [Anthropic: Code Execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp)
- [Cloudflare: Code Mode](https://blog.cloudflare.com/ru-ru/code-mode/)
- [ITIL 4](https://www.axelos.com/certifications/itil-service-management)

---

## 📞 Поддержка

**Вопросы?** 
- Проверьте раздел документации выше
- См. [FAQ](./01-getting-started/README.md)
- Создайте Issue на GitHub

---

**Обновлено:** 6 ноября 2025  
**Cleanup:** 380 → 60 файлов ✅  
**Status:** Clean & Organized 🎯
