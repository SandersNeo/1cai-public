# Testing Guide

> Обновлено: 10 ноября 2025

## 1. Обзор

Единый справочник по тестам 1C AI Stack. Покрывает Python-юниты и интеграцию, BSL/YAxUnit, нагрузку, безопасность и white-box анализ. Структура соответствует workflow `comprehensive-testing.yml`.

## 2. Матрица тестов

| Категория | Директория | Команда локально | Джоб в CI |
|-----------|------------|-------------------|-----------|
| Unit | `tests/unit/` | `make test-unit` / `pytest tests/unit/ -v` | `unit-tests` |
| Integration | `tests/integration/` | `make test-integration` / `pytest tests/integration/ -v` | `integration-tests` |
| System & E2E | `tests/system/`, `tests/comprehensive/`, `tests/acceptance/` | `pytest tests/system/ -v` и т.д. | `system-tests`, `acceptance-tests` |
| Performance & Load | `tests/performance/`, `tests/load/` | `pytest tests/performance/ -v -s`; `k6 run tests/load/k6_load_test.js` | `performance-tests` |
| Security | `tests/security/` | `pytest tests/security/ -v`; `bandit -r src/` | `security-tests` |
| White-box | `tests/whitebox/` | `pytest tests/whitebox/ -v -s` | `whitebox-analysis` |
| BSL / YAxUnit | `tests/bsl/` | `make test-bsl` / `python scripts/tests/run_bsl_tests.py` | `bsl-tests` |
| Full audit | скрипты и отчёты в корне | `python run_full_audit.py --stop-on-failure` | `full-project-audit` |

## 3. Предварительные требования

- Python 3.11.x (см. проверку в `src/main.py`).
- Виртуальное окружение + `make install` (или `pip install -r requirements.txt`).
- Docker (PostgreSQL, Redis, Neo4j, Qdrant) — запускайте `make docker-up` перед интеграционными тестами.
- `.env` с настройками БД/Redis/AI.
- Для BSL: OneScript, YAxUnit/Vanessa, рабочий workspace 1C, заполненный `tests/bsl/testplan.json`.

## 4. Python тесты

### Быстрые команды
```bash
make test           # все pytest-суиты
make test-unit      # только unit
make test-integration
make coverage       # pytest + HTML/term отчёт
```

Эквивалент без `make`:
```bash
pytest
pytest tests/integration/ -v
pytest --cov=src --cov-report=html --cov-report=term
```

**Отчёты:**
- Coverage HTML → `htmlcov/index.html` (после `make coverage`).
- Pytest вывод — в консоли; добавьте `-q` или `-k pattern` для фильтрации.
- Сохранение отчётов: `pytest --junitxml=output/test-results.xml` (используется в CI для загрузки артефактов).
- Для отладки падения теста используйте `pytest -vv --maxfail=1`, при необходимости включите `--pdb`.
- Интеграционные тесты требуют активных сервисов; если используется Docker, убедитесь в переменных `DATABASE_URL`, `REDIS_URL`.

## 5. BSL / YAxUnit тесты

1. Настройте `tests/bsl/testplan.json` (см. `tests/bsl/README.md`).
2. Запустите:
   - `make test-bsl` — shell для Windows/Linux (вызовет `run_bsl_tests.py`).
   - или `python scripts/tests/run_bsl_tests.py --manifest tests/bsl/testplan.json --artifacts-dir output/bsl-tests`.
   - Для PowerShell без `make` используйте `pwsh scripts/windows/bsl-ls-up.ps1` и `pwsh scripts/windows/bsl-ls-check.ps1`.
3. Логи создаются в `output/bsl-tests/<runner>.log`. Если файл манифеста отсутствует или пуст, скрипт завершится успешно (skip) — используем до подключения реальных сценариев.
4. Для каждый runner указывайте рабочую директорию, переменные окружения (`YAXUNIT_OPTS`, лицензия и т.д.) и таймауты.
5. Для анализа результатов:
   - `cat output/bsl-tests/<runner>.log` — ищите `FAILED`/`PASSED`.
   - Добавляйте `--junit` отчёты (см. пример в `tests/bsl/README.md`) и прикладывайте к CI артефактам.

## 6. CI интеграция

Файл `.github/workflows/comprehensive-testing.yml` запускает 10 параллельных джоб:
- `unit-tests`, `integration-tests`, `system-tests`, `performance-tests`, `security-tests`, `acceptance-tests`, `whitebox-analysis`, `spec-driven-validation`, `full-project-audit`, `bsl-tests`.
- Каждая job использует Python 3.11 и устанавливает необходимые пакеты.
- BSL-джоб работает на `windows-latest`, загружает артефакты из `output/bsl-tests`.
- `spec-driven-validation` гарантирует, что документы в `docs/research/features/<slug>/` заполнены — если job падает, удалите шаблонные маркеры и снова запустите `make feature-validate`.

Дополнительный workflow `.github/workflows/docs-lint.yml` проверяет оформление (`markdownlint`) и ссылки (`lychee`). Перед PR прогоните `markdownlint` и `lychee` локально, чтобы избежать падения CI.

Перед merge убедитесь, что локально проходят те же категории, которые затрагивает изменение. Если добавляете новые директории с тестами — обновите workflow и таблицу выше.

## 7. Артефакты и логирование

| Тип | Путь |
|-----|------|
| Pytest HTML coverage | `htmlcov/index.html` |
| BSL логи | `output/bsl-tests/*.log` |
| Audit отчёты | `BROKEN_LINKS_REPORT.txt`, `COMPREHENSIVE_AUDIT_FINAL.txt`, `SECURITY_AUDIT_REPORT.txt`, `README_CODE_VERIFICATION.txt` |
| Performance | Вывод `pytest -s` + `tests/load/k6_load_test.js` (stdout, экспортируйте вручную) |
| Feature validation | Лог job `spec-driven-validation` (содержит перечень незаполненных файлов) |
| Docs lint | Отчёты `markdownlint` и `lychee` (см. вкладку Actions → Documentation Quality) |

Рекомендуется сохранять значимые артефакты в CI (используйте `actions/upload-artifact`).

## 8. Troubleshooting

| Симптом | Причина | Решение |
|---------|---------|---------|
| `ModuleNotFoundError` в pytest | зависимости не установлены | `make install` / `pip install -r requirements.txt` |
| Интеграционные тесты не находят БД | Docker не поднят или `DATABASE_URL` пуст | `make docker-up`, проверьте `.env` |
| `Permission denied` для BSL runner | OSCRIPT/YAxUnit не установлены или нет доступа | Проверить пути в `testplan.json`, запуск от администратора (Windows) |
| `Manifest ... not found` | нет `tests/bsl/testplan.json` | Создать файл, даже если пустой массив `[]` |
| `k6` не установлен | пакет не поставлен локально | Установите k6 (Linux: репозиторий k6; Windows: Chocolatey) |
| `spec-driven-validation` падает | остались шаблонные маркеры/ TODO | Заполните файлы фичи и запустите `make feature-validate` |
| `docs-lint` → markdownlint | форматирование Markdown | Запустите `markdownlint "**/*.md"` и исправьте подсказки |
| `docs-lint` → lychee | битая ссылка / 429 | Проверьте URL, добавьте в `.lychee.toml` (только при необходимости) |

## 9. Благодарности

- [alkoleft/yaxunit](https://github.com/alkoleft/yaxunit) и [alkoleft/mcp-onec-test-runner](https://github.com/alkoleft/mcp-onec-test-runner) за основу BSL тестирования.
- Сообщество GitHub Spec Kit за подход к тестовым спецификациям и матрицам.
