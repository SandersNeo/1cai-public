# Анализ репозитория github/spec-kit

> Источник: [github/spec-kit](https://github.com/github/spec-kit)

## 1. Назначение и ключевые компоненты

-| Область | Описание |
-| --- | --- |
-| CLI-команды (`/speckit.*`) | В каталоге `scripts/` реализованы оболочки для генерации плана (`plan`), задач (`tasks`) и исполнения (`implement`). Они читают шаблоны, создают папку `specs/<feature>/` с контрактами, планом, research и задачами. |
-| Шаблоны (`templates/`) | Markdown-шаблоны для спецификации (plan, spec, tasks, CLAUDE), быстро задают структуру документации. |
-| `memory/constitution.md` | "Конституция" для AI-агентов — набор правил, которым должен следовать Claude/Copilot. |
-| Документация (`docs/`, README) | Большой гайд (>25к строк) по spec-driven development: как генерировать план, как проверять, как работать с AI. |
-| Dev контейнер и GitHub Actions | `.devcontainer`, markdownlint, scripts `check-prerequisites.sh` и проч. обеспечивают единое окружение и проверки. |

## 2. Полезные практики для 1C AI Stack

1. **Стандартизация спецификаций** — структура `specs/<id>/plan.md`, `tasks.md`, `research.md` лучше нашего разрозненного `docs/research`. Можно адаптировать шаблоны:
   - `templates/plan-template.md` → шаблон для новых фич (линковать ADR, сценарии).
   - `templates/tasks-template.md` → автоматический чек-лист для реализации.
2. **CLI для планирования** — `/speckit.plan` силён тем, что автоматизирует подготовку документов. Мы можем:
   - Создать скрипт `scripts/research/create_feature.sh`, который разворачивает директорию с нашим набором шаблонов + TODO-листом.
   - Использовать идеи `scripts/common.sh`, `setup-plan.sh`, `create-new-feature.sh` для проверки окружения.
3. **Конституция и память** — у нас есть набор "критических правил" (13+ правил). Стоит перенести их в `memory/constitution.md`, чтобы все агенты/скрипты ссылались на единый документ (аналог spec-kit).
4. **Документация по AI-процессам** — README spec-kit показывает, как подробно описывать сценарий. Мы можем расширить наш `docs/research/README_LOCAL.md` и `docs/research/bsl_language_server_plan.md` аналогично: пошаговые команды, пример задач, troubleshooting.
5. **CI-проверки** — включить markdownlint/docs workflow по аналогии с ними, чтобы контролировать крупные документы.

## 3. Риски и ограничения

- **Зависимость от внешних CLI** — spec-kit полагается на Claude/Copilot. Необходимо адаптировать скрипты для наших MCP-агентов или сделать "офлайновый" вариант.
- **Объём документации** — интеграция добавит много markdown-файлов; нужно обновлять наши правила публикации (ссылки и благодарности обязательно).
- **Дублирование с текущими скриптами** — у нас уже есть ADR/uml-генерация; нужно аккуратно объединять, чтобы не мешать нашим workflow.

## 4. Предлагаемые шаги

1. **Шаблоны** ✅
   - Добавлены `templates/feature-plan.md`, `feature-spec.md`, `feature-tasks.md`, `feature-research.md` и `templates/README.md` с благодарностью GitHub/spec-kit.
   - Скрипт `scripts/research/init_feature.py` создаёт `docs/research/features/<slug>/` с авто-подстановкой заголовков и даты.
2. **Конституция** ✅
   - Документ `docs/research/constitution.md` создан, добавлены ссылки в README/CHANGELOG.
3. **CLI/Automation** ✅ (MVP)
   - Make-таргеты `make feature-init` и `make feature-validate` вызывают `scripts/research/init_feature.py` и `scripts/research/check_feature.py`.
   - Подключен job `spec-driven-validation` в CI (`comprehensive-testing.yml`), который выполняет `make feature-validate`.
4. **Интеграция AI** ⬜
   - Исследовать адаптацию `/speckit.plan` под MCP/Claude: возможно, использовать наших агентов для авто-заполнения разделов (future task).
5. **Документация** ✅
   - README, Documentation Hub, `docs/scripts/README.md`, `CHANGELOG.md`, `docs/research/README_LOCAL.md` обновлены ссылками на новый workflow.
   - TODO: расширить FAQ/Troubleshooting с учётом spec-driven подхода.

## 5. Вывод

Spec-kit — отличный ориентир для структурирования планирования и внедрения фич. Адаптация его подходов (шаблоны, конституция, CLI) даст нам:
- единый стандарт создания спецификаций;
- автоматизированный чек-лист перед разработкой;
- интеграцию правил проверки в процессы AI.

Рекомендуется реализовать предложенные шаги в ближайших спринтах и прописать их в TODO/roadmap.

## 6. DevOps / SRE Best Practices (итерация 200 источников)

| Направление | Best practice (сводка) | Текущий статус | Следующие шаги |
|-------------|------------------------|----------------|----------------|
| **Культура и управление** | Общие OKR Dev+Ops, trunk-based, blameless postmortem, on-call ротация | Частично: spec-driven workflow, конституция, но нет формальной on-call/OKR и постмортемов | Создать раздел в конституции по постмортемам; задокументировать on-call/дежурства; добавить “DevOps KPIs” |
| **Работа с требованиями** | RFC/ADR, раннее участие QA/Sec, traceability | Есть шаблоны `templates/feature-*.md`; traceability пока вручную | Добавить чек-лист готовности (definition of done) и автоматизированную ссылку на issue/PR |
| **CI/CD и качество** | Ступенчатые пайплайны, build once → promote, smoke после деплоя, отчёты | CI покрывает тесты, docs lint, spec validation; релизы автоматизированы (`release.yml`); smoke-tests компилируют модули и дергают `/health`; есть `make smoke-up` для docker check; HTML/JUnit/Allure артефакты; Jenkins/GitLab pipelines (`infrastructure/jenkins/Jenkinsfile`, `infrastructure/gitlab/.gitlab-ci.yml`) | Подготовить smoke job с поднятием минимального сервиса в CI; внедрить Allure отчёты на другие пакеты |
| **Infrastructure as Code / GitOps** | Terraform/Ansible/Helm, GitOps, secrets management, rollback playbook | Docker-compose + Make; теперь есть kind кластер (`infrastructure/kind`), Helm chart и Terraform (`infrastructure/terraform`); Vault интеграция в values; rollback playbook в `docs/research/release_playbook.md`; GitOps ещё нет | Подготовить ADR по GitOps; сформировать rollback playbook; проверить секреты (Vault/ENV) |
| **Observability & Monitoring** | RED/USE метрики, логи, трассировки, SLO/Error Budgets, alert runbooks | `github-monitor.yml`, `dora-metrics.yml`, `/metrics` (Prometheus Instrumentator), локальный стек (`make observability-up`), Kubernetes стек (`make helm-observability`, Helm chart `infrastructure/helm/observability-stack` с Prometheus/Loki/Tempo/Grafana/OTEL), CI `observability-test.yml`, Telegram алерты (`telegram-alert.yaml`), Alertmanager (`observability/alertmanager.yml` + `observability/alerts.yml`), `docs/observability/SLO.md`, `docs/runbooks/alert_slo_runbook.md`; TODO: реальный alert канал (prod) | Добавить сбор SLI (Prometheus exporter/Logs), завести продовый alert-канал |
| **Security (DevSecOps)** | Shift-left (SAST/DAST), dependency & secret scanning, policy-as-code | Bandit, Safety, run_full_audit; workflows `secret-scan.yml` (Gitleaks) и `trufflehog.yml` (Trufflehog); Conftest Rego политики (`policy/kubernetes/*.rego`), Semgrep (`security/semgrep.yml`), make `policy-check`, CI интеграция | Расширить конституцию пунктами по least privilege; рассмотреть OPA/policy-as-code для Terraform/GitOps |
| **Resilience & DR** | Chaos engineering, резервирование, регулярные restore, документированные DR Playbooks | Бэкап-скрипты есть (`backup-restore.sh`), но нет регулярных restore/chaos | План геймдэя; добавить пункт “restore rehearsal” в TODO; зафиксировать процедуру |
| **Feedback & Continuous Improvement** | Метрики delivery (lead time, deploy freq, MTTR, CFR), UX feedback, DevEx | Скрипт `collect_dora.py` + workflow `dora-metrics.yml` собирают метрики; ретроспективы не описаны | Добавить визуализацию/дашборд, включить DORA summary в README/ретро; описать feedback loop |
