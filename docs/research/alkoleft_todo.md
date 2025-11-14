# TODO: Бэклог развития платформы

> **Примечание:** Этот файл содержит общий бэклог задач проекта. Название файла исторически связано с тем, что часть задач касается интеграции внешних инструментов из экосистемы [@alkoleft](https://github.com/alkoleft) (открытые инструменты для разработки на 1С: MCP-серверы, тест-раннеры, парсеры BSL и др.). Подробнее о внешних зависимостях см. [`alkoleft_inventory.md`](./alkoleft_inventory.md) и ADR в [`docs/architecture/adr/`](../architecture/adr/).

## Задачи по интеграции внешних инструментов

- [ ] (Высокий) Реализация плана по `bsl-language-server` и `metadata.js` ([детали](./bsl_language_server_plan.md))
  - 👣 План сформирован, далее — выполнение шагов 1–6
- [ ] (Средний) Подготовка Marketplace-пакетов (`onec-markdown-viewer`, `VAEditor`) — требования и публикация ([план](./marketplace_integration_plan.md))
- [ ] (Низкий) Оценка архивных утилит (`cfg_tools`, `ones_universal_tools`) — перенос в CLI ([план оценки](./archive_tools_assessment.md))
- [ ] (Средний) Мониторинг GitHub-репозиториев @alkoleft (webhook/API) ([план](./github_monitoring_plan.md))
  - ✅ CLI `scripts/monitoring/github_monitor.py` создаёт снимок и сравнивает релизы; далее — автоматизация (cron/CI, уведомления).

## Общий бэклог платформы

- [ ] (Высокий) DevOps платформа (K8s/IaC/CI/GitOps)
  - ✅ Kind кластер, Helm chart, Terraform шаблон, Jenkins/GitLab pipeline.
  - ✅ GitOps: Argo CD manifests (`infrastructure/argocd`), скрипты `scripts/gitops/*`, make `gitops-*`.
  - TODO: Argo CD ApplicationSet для multi-env, Terraform модуль Argo CD, Vault интеграция.
- [ ] (Средний) Spec-driven workflow: проверки заполнения шаблонов, интеграция с CI (TODO в `docs/research/spec_kit_analysis.md`).
  - ✅ Скрипты `init_feature.py` / `check_feature.py`, make-таргеты `feature-init` / `feature-validate`, CI job `spec-driven-validation`.
- [ ] (Средний) Release automation и репортинг
  - ✅ `scripts/release/create_release.py`, make `release-*`, workflow `release.yml`, `docs/research/release_playbook.md`.
- [ ] (Средний) Secret scanning и политика безопасности
  - ✅ Workflows `secret-scan.yml` (Gitleaks) и `trufflehog.yml` (Trufflehog); расширить конституцию пунктами по least privilege.
  - ✅ Policy-as-code: `policy/kubernetes/*.rego`, Semgrep (`security/semgrep.yml`), make `policy-check`, CI интеграция.
  - TODO: внедрить OPA/Conftest для Terraform планов и GitOps; формализовать исключения.
- [ ] (Низкий) Сбор и публикация DORA-метрик
  - ✅ `scripts/metrics/collect_dora.py`, workflow `dora-metrics.yml`; настроить визуализацию (следующий шаг).
- [ ] (Средний) Observability & Runbooks
  - ✅ `docs/observability/SLO.md`, `docs/runbooks/alert_slo_runbook.md`, `docs/runbooks/postmortem_template.md`; внедрить автоматический экспорт метрик и alert канал.
  - ✅ Инфраструктура: `observability/docker-compose.observability.yml` (локально), `infrastructure/helm/observability-stack` (K8s), правила `observability/alerts.yml`, конфиг `observability/alertmanager.yml`.
  - TODO: Интеграция с Prometheus/Grafana (`observability.yml`) и Telegram (workflow `telegram-alert.yaml`) + секреты в CI/CD.
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
  - ☐ BA-03 Process & Journey Modelling (BPMN 2.0, CJM, экспорт).
  - ☐ BA-04 Analytics & KPI Toolkit (SQL/BI, OKR/ROI, Observability).
  - ☐ BA-05 Traceability & Compliance (risk register, heatmap).
  - ☐ BA-06 Integrations & Collaboration (Jira/Confluence/ServiceNow).
  - ☐ BA-07 Documentation & Enablement (guides, примеры, дашборды).
- [ ] (Высокий) Runtime & Compliance
  - ✅ `scripts/setup/check_runtime.py`, make `check-runtime`, инструкция `docs/setup/python_311.md`.
  - TODO: Обновить конституцию правилами по установленной версии Python; автоматизировать проверку наличия `make`, `docker compose`.
- [ ] (Средний) DR/Resilience
  - ✅ План `docs/runbooks/dr_rehearsal_plan.md`, скрипт `scripts/runbooks/dr_rehearsal_runner.py`, workflow `dr-rehearsal.yml`.
  - TODO: Автоматический отчёт в postmortem, интеграция Litmus сценариев.
