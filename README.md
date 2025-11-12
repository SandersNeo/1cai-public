# 🤖 1C AI Stack

> Платформа, которая собирает DevOps-, AI- и эксплуатационные практики вокруг 1C:Enterprise в одну управляемую систему: разбор конфигураций, MCP-инструменты, CI/CD, безопасность и наблюдаемость.
> Внутри — рабочие сервисы, make-таргеты и документация, которые мы используем каждый день для реальных 1С-ландшафтов.

**Кому полезно:** DevOps-командам 1С, архитекторам платформы и ML/аналитикам, которым нужно быстрее внедрять изменения в продуктивные 1С-ландшафты.

### Что уже работает
- **Многослойный анализ конфигураций.** EDT parser, bsl-language-server и диагностические скрипты в `src/` и `scripts/analysis/` превращают 1C-конфигурации в метаданные, отчёты и графы зависимостей (`docs/06-features/EDT_PARSER_GUIDE.md`).
- **Автоматизация и MCP-инструменты.** `src/ai/mcp_server.py`, spec-driven workflow и готовые CLI помогают создавать задачи, генерировать код и запускать тесты из IDE или CI (`docs/06-features/MCP_SERVER_GUIDE.md`).
- **Промышленный контур.** Helm charts, Argo CD, Linkerd, Vault и Terraform-модули в `infrastructure/` + регламенты в `docs/ops/` позволяют разворачивать и поддерживать стек в облаке без ручных «магических» шагов.

![Контейнерная схема платформы](docs/architecture/uml/c4/png/container_overview.png)

## За 5 минут: пробный запуск
1. Установить Python 3.11, Docker и Docker Compose — подробности в [`docs/setup/python_311.md`](docs/setup/python_311.md).
2. Проверить окружение: `make check-runtime` (используются скрипты из `scripts/setup/check_runtime.py`).
3. Запустить минимальный стенд:
   ```bash
   make docker-up      # инфраструктура: БД, брокеры, Neo4j, Qdrant
   make migrate        # первичная миграция данных
   make servers        # Graph API + MCP server
   open http://localhost:6001/mcp
   ```
   > Для Windows есть аналоги в `scripts/windows/`. После запуска доступен живой MCP endpoint, логи сервисов и тестовые данные — можно сразу проверять сценарии.

## Сценарии использования
| Роль | Первое действие | Ключевые материалы |
| ---- | ---------------- | ------------------ |
| DevOps / SRE | Пройти `make gitops-apply`, подключить Vault/Linkerd | `docs/ops/devops_platform.md`, `docs/ops/gitops.md`, `docs/ops/service_mesh.md`, `infrastructure/helm/1cai-stack` |
| 1С-разработчик / архитектор | Разобрать конфигурацию и получить документацию | `docs/06-features/EDT_PARSER_GUIDE.md`, `scripts/analysis/generate_documentation.py`, `docs/architecture/README.md` |
| ML / аналитика | Сформировать датасет и прогнать проверки качества | `docs/06-features/ML_DATASET_GENERATOR_GUIDE.md`, `docs/06-features/TESTING_GUIDE.md`, `scripts/analysis/` |
| Операционный менеджер / on-call | Подготовить регламенты и тренировки | `docs/runbooks/dr_rehearsal_plan.md`, `docs/process/oncall_rotations.md`, `docs/observability/SLO.md` |

## Ключевые блоки платформы
- **MCP & AI tooling** — инструменты поиска метаданных, генерации кода и AST (`src/ai/`, `docs/06-features/AST_TOOLING_BSL_LANGUAGE_SERVER.md`, `docs/06-features/MCP_SERVER_GUIDE.md`).
- **Инфраструктура** — Helm charts, Terraform, Argo CD, Linkerd, Vault (`infrastructure/helm/`, `infrastructure/terraform/`, `infrastructure/argocd/`, `scripts/service_mesh/`).
- **Надёжность и наблюдаемость** — runbooks, DR rehearsal, DORA/Prometheus/Alertmanager (`docs/runbooks/`, `docs/process/`, `observability/`).
- **Безопасность и FinOps** — Rego/Conftest, Checkov/Trivy, бюджетные отчёты и политики (`policy/`, `scripts/security/`, `scripts/finops/`).

## Чего ждать дальше
- Расширение spec-driven практик и интеграции с GitHub Spec Kit — см. `docs/research/spec_kit_analysis.md`, `docs/research/constitution.md`.
- Новые тестовые раннеры (YAxUnit, edt-test-runner) и сценарии — слежение в `docs/06-features/TESTING_GUIDE.md`, `docs/research/alkoleft_todo.md`.
- UI/презентационный слой для быстрой навигации — наработки в `docs/09-archive/ui-ux-backup/`.

## Документация и ресурсы
- Полный индекс: [`docs/README.md`](docs/README.md).
- Архитектура: [`docs/architecture/README.md`](docs/architecture/README.md), Structurizr DSL и PlantUML в `docs/architecture/c4/` и `docs/architecture/uml/`.
- Практики тестирования и качества: [`docs/06-features/TESTING_GUIDE.md`](docs/06-features/TESTING_GUIDE.md), `scripts/tests/`.
- Политики безопасности: [`docs/security/policy_as_code.md`](docs/security/policy_as_code.md), workflows `.github/workflows/secret-scan.yml`, `trufflehog.yml`.
- Наблюдаемость и метрики: `observability/docker-compose.observability.yml`, `docs/observability/SLO.md`, `docs/status/dora_history.md`.

## Как взаимодействовать
- Бэклог и актуальные задачи — [`docs/research/alkoleft_todo.md`](docs/research/alkoleft_todo.md).
- Issues и pull-requests приветствуются; ориентируйтесь на [recent commits](https://github.com/DmitrL-dev/1cai/commits/main) и `docs/05-development/CHANGELOG.md`.
- Перед изменением диаграмм обязательно запускайте `make render-uml` (workflow «PlantUML Render Check» использует те же скрипты).
- Для оперативных вопросов — внутренний канал команды (контакты описаны в приватной документации).