# TODO: Бэклог развития платформы

> **Примечание:** Этот файл содержит общий бэклог задач проекта. Название файла исторически связано с тем, что часть задач касается интеграции внешних инструментов из экосистемы [@alkoleft](https://github.com/alkoleft) (открытые инструменты для разработки на 1С: MCP-серверы, тест-раннеры, парсеры BSL и др.). Подробнее о внешних зависимостях см. [`alkoleft_inventory.md`](./alkoleft_inventory.md) и ADR в [`docs/architecture/adr/`](../architecture/adr/).

> **Последнее обновление:** Ноябрь 2025  
> **Версия платформы:** 5.3.0

## Задачи по интеграции внешних инструментов

- [ ] (Высокий) Реализация плана по `bsl-language-server` и `metadata.js` ([детали](./bsl_language_server_plan.md))
  - 👣 План сформирован, далее — выполнение шагов 1–6
- [ ] (Средний) Подготовка Marketplace-пакетов (`onec-markdown-viewer`, `VAEditor`) — требования и публикация ([план](./marketplace_integration_plan.md))
- [ ] (Низкий) Оценка архивных утилит (`cfg_tools`, `ones_universal_tools`) — перенос в CLI ([план оценки](./archive_tools_assessment.md))
- [ ] (Средний) Мониторинг GitHub-репозиториев @alkoleft (webhook/API) ([план](./github_monitoring_plan.md))
  - ✅ CLI `scripts/monitoring/github_monitor.py` создаёт снимок и сравнивает релизы; далее — автоматизация (cron/CI, уведомления).

## 🎯 ПРИОРИТЕТНЫЕ ЗАДАЧИ (Следующие шаги)

### 🔥 Высокий приоритет (делаем сейчас):

1. **[ ] Завершить EDT Plugin**
   - ☑ MetadataGraphView (визуализация графа метаданных)
   - ☑ SemanticSearchView (семантический поиск в IDE)
   - ☑ Context menu интеграция
   - ☑ Build .jar файла для установки в EDT

2. **[ ] Улучшить тестовое покрытие**
   - ✅ Unit tests для Kimi client (выполнено)
   - ✅ Integration tests для AI Orchestrator (выполнено)
  - ☑ E2E тесты для критических путей (API → AI → Response)
  - ☑ Performance benchmarks для Kimi-K2-Thinking

3. **[ ] Мониторинг и наблюдаемость**
   - ✅ Prometheus метрики для AI сервисов (выполнено)
   - ✅ Grafana дашборды для AI (выполнено)
   - ✅ Alert правила (выполнено)
   - ☐ Интеграция с Telegram уведомлениями
   - ☐ Настроить реальный alert канал (prod)

### 🟡 Средний приоритет (ближайшие недели):

4. **[ ] Расширить AI интеграции**
   - ✅ Kimi-K2-Thinking (API + local) (выполнено)
   - ☐ 1C:Напарник (реальная интеграция, не только структура)
   - ☐ GigaChat / YandexGPT (полная интеграция)
   - ☐ Локальные модели через Ollama (расширить список)

5. **[ ] Production readiness**
   - ☐ Load testing (API endpoints)
   - ☐ Security audit (penetration testing)
   - ☐ Performance optimization (кэширование, connection pooling)
   - ☐ Kubernetes deployment (полное развертывание)

---

## Общий бэклог платформы

- [ ] (Высокий) DevOps платформа (K8s/IaC/CI/GitOps)
  - ✅ Kind кластер, Helm chart, Terraform шаблон, Jenkins/GitLab pipeline.
  - ✅ GitOps: Argo CD manifests (`infrastructure/argocd`), ApplicationSet для Linkerd (`applicationset-linkerd.yaml`) и 1cai (`applicationset-1cai.yaml`), скрипты `scripts/gitops/*`, make `gitops-*`.
  - TODO: Terraform модуль Argo CD, Vault интеграция (secret management для Argo CD/Linkerd/observability).
- [ ] (Средний) Spec-driven workflow: проверки заполнения шаблонов, интеграция с CI (TODO в `docs/research/spec_kit_analysis.md`).
  - ✅ Скрипты `init_feature.py` / `check_feature.py`, make-таргеты `feature-init` / `feature-validate`, CI job `spec-driven-validation`.
- [ ] (Средний) Release automation и репортинг
  - ✅ `scripts/release/create_release.py`, make `release-*`, workflow `release.yml`, `docs/research/release_playbook.md`.
- [ ] (Средний) Secret scanning и политика безопасности
  - ✅ Workflows `secret-scan.yml` (Gitleaks) и `trufflehog.yml` (Trufflehog); расширить конституцию пунктами по least privilege.
  - ✅ Policy-as-code: `policy/kubernetes/*.rego`, Semgrep (`security/semgrep.yml`), make `policy-check`, CI интеграция; Conftest для Terraform планов (`scripts/security/run_policy_checks.sh`).
  - TODO: расширить Conftest/OPA на GitOps-манифесты (Argo CD) и формализовать список допустимых исключений (policy waivers). 
- [ ] (Низкий) Сбор и публикация DORA-метрик
  - ✅ `scripts/metrics/collect_dora.py`, workflow `dora-metrics.yml`; добавлен шаблон weekly summary (`docs/status/weekly_summary_template.md`) и README (`docs/status/README.md`) для визуализации/обзора.
- [x] (Средний) Observability & Runbooks **[ОБНОВЛЕНО: Январь 2025]**
  - ✅ `docs/observability/SLO.md`, `docs/runbooks/alert_slo_runbook.md`, `docs/runbooks/postmortem_template.md`; внедрить автоматический экспорт метрик и alert канал.
  - ✅ Инфраструктура: `observability/docker-compose.observability.yml` (локально), `infrastructure/helm/observability-stack` (K8s), правила `observability/alerts.yml`, конфиг `observability/alertmanager.yml`.
  - ✅ **Prometheus метрики для AI сервисов** (Kimi-K2-Thinking, AI Orchestrator) **[NEW]**
  - ✅ **Grafana дашборды** (`monitoring/grafana/dashboards/ai_services.json`) **[NEW]**
  - ✅ **Alert правила** (`monitoring/prometheus/alerts/ai_alerts.yml`) **[NEW]**
  - ✅ **Документация мониторинга** (`monitoring/AI_SERVICES_MONITORING.md`) **[NEW]**
  - ☑ Интеграция с Telegram (workflow `.github/workflows/telegram-alert.yaml`); TODO: добавить/задокументировать секреты в prod CI/CD (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`).
- [ ] (Высокий) AWS/Azure Cloud readiness
  - ✅ Terraform модуль `infrastructure/terraform/aws-eks`.
  - ✅ Terraform модуль `infrastructure/terraform/azure-aks`, Azure DevOps pipeline (`infrastructure/azure/azure-pipelines.yml`).
  - ✅ Ansible bootstrap `infrastructure/ansible`.
  - TODO: Terraform backend (S3/DynamoDB, Azure Storage), Managed Identity для Vault.
- [ ] (Средний) Secret management
  - ✅ Vault политика/скрипт (`infrastructure/vault/`, `docs/ops/vault.md`).
  - ✅ CSI: SecretProviderClass (`infrastructure/vault/csi`), Helm интеграция (`vault.enabled`, agent sidecar), make `vault-csi-apply`, sync скрипты (`scripts/secrets/*`).
  - TODO: Vault Agent sidecar автоматические обновления, Azure Key Vault Terraform, Secret rotation alerts.
- [ ] (Средний) FinOps
  - ✅ Скрипты `scripts/finops/aws_cost_report.py`, `aws_cost_to_slack.py`, `aws_budget_check.py`, `azure_cost_to_slack.py`, `azure_budget_check.py`; workflow `finops-report.yml`; make `finops-slack` (Slack/Teams);
  - ✅ Дашборд Grafana `observability/grafana/dashboards/finops_cost.json` (требуются datasources).
  - TODO: Teams dashboard и автоматическая загрузка FinOps данных в Prometheus/ClickHouse.
- [ ] (Средний) Service Mesh & Chaos
  - ✅ Istio профиль (`infrastructure/service-mesh/istio`), make `mesh-istio-apply`, документ `docs/ops/service_mesh.md`.
  - ✅ Linkerd blueprint (`infrastructure/service-mesh/linkerd`), ArgoCD application/ApplicationSet, make `linkerd-install`, серты `bootstrap_certs.sh`/`rotate_certs.sh`, Managed Identity, smoke `ci_smoke.sh` + `linkerd-smoke.yml`, chaos `chaos_ci.sh` + `linkerd-chaos.yml`.
  - ✅ Litmus pod-delete + network latency (`infrastructure/chaos/litmus`, `make chaos-litmus-run`).
  - TODO: Linkerd trust anchors автоматизация через external secrets/Key Vault, Istio mTLS policies enforcement.
- [ ] (Средний) Business Analyst Agent
  - ✅ Исследование рынка вакансий (RU/EU/US) → `docs/research/job_market_business_analyst.md`.
  - ✅ Подготовлен roadmap → `docs/research/ba_agent_roadmap.md`.
  - ✅ BA-02 Requirements Intelligence (LLM-ready extractor, docx/pdf support, CLI `ba-extract`, тесты).
  - ☐ BA-03 Process & Journey Modelling (BPMN 2.0, CJM, экспорт) — добавлен план/гайд `docs/06-features/BA_PROCESS_MODELLING_GUIDE.md`, реализация остаётся planned.
  - ☐ BA-04 Analytics & KPI Toolkit (SQL/BI, OKR/ROI, Observability) — добавлен план/гайд `docs/06-features/BA_ANALYTICS_KPI_GUIDE.md`, реализация остаётся planned.
  - ☐ BA-05 Traceability & Compliance (risk register, heatmap) — добавлен план/гайд `docs/06-features/BA_TRACEABILITY_COMPLIANCE_GUIDE.md`, реализация остаётся planned.
  - ☐ BA-06 Integrations & Collaboration (Jira/Confluence/ServiceNow) — добавлен план/гайд `docs/06-features/BA_INTEGRATIONS_COLLAB_GUIDE.md`, реализация остаётся planned.
  - ☐ BA-07 Documentation & Enablement (guides, примеры, дашборды) — добавлен план/гайд `docs/06-features/BA_ENABLEMENT_GUIDE.md`, реализация остаётся planned.
  - ☐ BA-06 Integrations & Collaboration (Jira/Confluence/ServiceNow).
  - ☐ BA-07 Documentation & Enablement (guides, примеры, дашборды).
- [ ] (Высокий) Runtime & Compliance
  - ✅ `scripts/setup/check_runtime.py`, make `check-runtime`, инструкция `docs/setup/python_311.md`.
  - ✅ **Структурированное логирование** (100% миграция на StructuredLogger) **[NEW]**
  - ✅ **Централизованная обработка ошибок** (ErrorHandler) **[NEW]**
  - ✅ **Retry logic с exponential backoff** (для всех внешних вызовов) **[NEW]**
  - TODO: Обновить конституцию правилами по установленной версии Python; автоматизировать проверку наличия `make`, `docker compose`.
- [ ] (Средний) DR/Resilience
  - ✅ План `docs/runbooks/dr_rehearsal_plan.md`, скрипт `scripts/runbooks/dr_rehearsal_runner.py`, workflow `dr-rehearsal.yml`.
  - ☑ Автоматический отчёт в postmortem — добавлен `scripts/runbooks/generate_dr_postmortem.py` (создаёт черновики в `docs/runbooks/postmortems/` и описан в `dr_rehearsal_plan.md`); TODO: интеграция Litmus сценариев.

- [ ] (Средний) Scenario Hub & MCP-free архитектура **[НОВОЕ, research]**
  - ✅ Reference-слой Scenario Hub: цели/сценарии/плейбуки, уровни риска и автономности, trust-score (`src/ai/scenario_hub.py`, `docs/architecture/AI_SCENARIO_HUB_REFERENCE.md`).
  - ✅ Tool / Skill Registry как протокол-независимый реестр инструментов/skills (`src/ai/tool_registry.py`, `docs/architecture/TOOL_REGISTRY_REFERENCE.md`).
  - ✅ Примерные планы BA→Dev→QA и DR rehearsal + read-only API `/api/scenarios/examples` (`src/ai/scenario_examples.py`, `src/ai/orchestrator.py`).
  - ☑ YAML/JSON-плейбуки для ключевых сценариев (BA→Dev→QA, DR rehearsal, security-audit) и связка с существующими скриптами/CI (реализованы dry-run playbooks `playbooks/ba_dev_qa_example.yaml`, `playbooks/dr_vault_example.yaml`, `playbooks/security_audit_example.yaml` + CLI `scripts/runbooks/run_playbook.py`; интеграция с CI остаётся planned).
  - TODO: интеграция Scenario Hub / ToolRegistry в Orchestrator и агентов (выбор маршрута по риску, автономности и метрикам).
