# FinOps & Cost Monitoring

## 1. Цели
- Контроль затрат в AWS/Cloud (ежедневные отчёты, бюджет).

## 2. Инструменты
- `scripts/finops/aws_cost_report.py` — использует AWS Cost Explorer API, показывает ежедневные затраты за 7 дней.
- `scripts/finops/aws_cost_to_slack.py` — отправляет отчёт за 3 дня в Slack (`SLACK_WEBHOOK_URL`).
- `scripts/finops/azure_cost_to_slack.py` — аналог для Azure Cost Management (нужны `AZURE_*` переменные).
- Workflow `.github/workflows/finops-report.yml` — ежедневная отправка отчётов AWS/Azure + проверки Budgets (если заданы `AWS_BUDGET_NAMES`).
- Make цель `make finops-slack` — одномоментный запуск локально.

## 3. Требования
```bash
# AWS
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
python scripts/finops/aws_cost_to_slack.py
python scripts/finops/aws_budget_check.py

# Azure
export SLACK_WEBHOOK_URL=...
export AZURE_TENANT_ID=...
export AZURE_CLIENT_ID=...
export AZURE_CLIENT_SECRET=...
export AZURE_SUBSCRIPTION_ID=...
python scripts/finops/azure_cost_to_slack.py
```

## 4. Roadmap
- Azure Budgets / Teams оповещения.
- Grafana dashboards с Cost Explorer.
