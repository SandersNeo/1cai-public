# Documentation Hub

Быстрая навигация по основным блокам документации. Используйте этот индекс как стартовую точку (а `docs/research/README_LOCAL.md` — для ежедневных статусов).

## 1. Setup & Runtime
- [`docs/setup/python_311.md`](setup/python_311.md) — установка Python 3.11.
- `scripts/setup/check_runtime.py`, `make check-runtime` — валидация окружения.
- [`docs/scripts/README.md`](scripts/README.md) — справочник CLI-скриптов.
- `scripts/ba/requirements_cli.py` — извлечение требований (см. `make ba-extract`).

## 2. Infrastructure & Operations
- Стратегия DevOps: [`docs/ops/devops_platform.md`](ops/devops_platform.md).
- GitOps/Argo CD: [`docs/ops/gitops.md`](ops/gitops.md), `infrastructure/argocd/`.
- Vault & secrets: [`docs/ops/vault.md`](ops/vault.md), `infrastructure/vault/`, `policy/terraform/`.
- Service Mesh & Chaos: [`docs/ops/service_mesh.md`](ops/service_mesh.md), [`docs/ops/chaos_engineering.md`](ops/chaos_engineering.md), `scripts/service_mesh/linkerd/`.
- FinOps & Observability: [`docs/ops/finops.md`](ops/finops.md), [`docs/observability/SLO.md`](observability/SLO.md).
- Runbooks: [`docs/runbooks/alert_slo_runbook.md`](runbooks/alert_slo_runbook.md), [`docs/runbooks/dr_rehearsal_plan.md`](runbooks/dr_rehearsal_plan.md).
- Процессы: [`docs/process/README.md`](process/README.md) — on-call, RFC, postmortem.

## 3. Architecture & Research
- High-level дизайн, C4: [`docs/architecture/README.md`](architecture/README.md).
- ADR: [`docs/architecture/adr/`](architecture/adr/).
- Исследования и планы: [`docs/research/README_LOCAL.md`](research/README_LOCAL.md), [`docs/research/spec_kit_analysis.md`](research/spec_kit_analysis.md), [`docs/research/job_market_business_analyst.md`](research/job_market_business_analyst.md), [`docs/research/ba_agent_roadmap.md`](research/ba_agent_roadmap.md), [`docs/research/alkoleft_todo.md`](research/alkoleft_todo.md).

## 4. Feature Guides
- MCP сервер и AI tooling: [`docs/06-features/MCP_SERVER_GUIDE.md`](06-features/MCP_SERVER_GUIDE.md).
- AST tooling: [`docs/06-features/AST_TOOLING_BSL_LANGUAGE_SERVER.md`](06-features/AST_TOOLING_BSL_LANGUAGE_SERVER.md).
- Парсеры, ML, интеграции: раздел `docs/06-features/`.

## 5. Automation & CI
- Workflows GitHub Actions: `.github/workflows/` (`linkerd-smoke.yml`, `linkerd-chaos.yml`, `dr-rehearsal.yml`, `finops-report.yml`, `chaos-validate.yml` и др.).
- Make targets: см. `Makefile` (quick filter: `make help`).
- Jenkins/GitLab pipeline: `infrastructure/jenkins/Jenkinsfile`, `infrastructure/gitlab/.gitlab-ci.yml`.

## 6. Governance & Compliance
- Конституция: [`docs/research/constitution.md`](research/constitution.md).
- Policy-as-code: [`docs/security/policy_as_code.md`](security/policy_as_code.md), `policy/kubernetes/**`, `policy/terraform/**`.

## 7. Changelog & Releases
- Изменения: [`CHANGELOG.md`](../CHANGELOG.md).
- Release automation: `scripts/release/create_release.py`, workflow `release.yml`.
# 📚 Документация 1C AI Stack

**Версия:** 5.1.0  
**Обновлено:** 6 ноября 2025  
**Статус:** Production Ready ✅

---

## 🚀 БЫСТРАЯ НАВИГАЦИЯ

| Задача | Документация |
|--------|--------------|
| **🎯 Быстрый старт** | [Quick Start](./01-getting-started/START_HERE.md) |
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
