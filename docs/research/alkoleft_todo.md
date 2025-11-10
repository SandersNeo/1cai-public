# TODO: Интеграция экосистемы @alkoleft

- [ ] (Высокий) Реализация плана по `bsl-language-server` и `metadata.js` ([детали](./bsl_language_server_plan.md))
  - 👣 План сформирован, далее — выполнение шагов 1–6
- [ ] (Средний) Подготовка Marketplace-пакетов (`onec-markdown-viewer`, `VAEditor`) — требования и публикация ([план](./marketplace_integration_plan.md))
- [ ] (Низкий) Оценка архивных утилит (`cfg_tools`, `ones_universal_tools`) — перенос в CLI ([план оценки](./archive_tools_assessment.md))
- [ ] (Средний) Мониторинг GitHub-репозиториев @alkoleft (webhook/API) ([план](./github_monitoring_plan.md))
  - ✅ CLI `scripts/monitoring/github_monitor.py` создаёт снимок и сравнивает релизы; далее — автоматизация (cron/CI, уведомления).
- [ ] (Средний) Spec-driven workflow: проверки заполнения шаблонов, интеграция с CI (TODO в `docs/research/spec_kit_analysis.md`).
  - ✅ Скрипты `init_feature.py` / `check_feature.py`, make-таргеты `feature-init` / `feature-validate`, CI job `spec-driven-validation`.
