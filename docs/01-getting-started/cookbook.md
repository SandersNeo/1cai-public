# 🍳 Usage Cookbook — типовые сценарии

Набор «рецептов» для быстрого использования стека без чтения всей документации.

---

## 1. Быстро проверить, что всё в порядке (Linux/macOS)

```bash
make check-runtime         # Python 3.11 + предупреждения по make/docker
make test-unit             # Юнит-тесты
make test-integration      # Интеграционные тесты
make security-audit        # Скрытые каталоги, секреты, git safety, аудит проекта
```

---

## 2. Быстрый локальный старт (Windows)

1. Пройти `docs/01-getting-started/windows_quickstart.md`.  
2. Минимальный набор:

```powershell
cd C:\1cAI
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

docker-compose up -d postgres redis
python src/main.py
python -m pytest tests/unit/ -q
pwsh scripts/windows/security-audit.ps1
```

---

## 3. Проверить BA → Dev → QA поток (E2E)

```bash
python -m pytest tests/system/test_e2e_ba_dev_qa.py -q
```

Документация: `docs/08-e2e-tests/BA_DEV_QA_E2E.md`.

---

## 4. Проверить AI Orchestrator (тесты + латентность)

```bash
# Юнит-тесты оркестратора
python -m pytest tests/unit/test_ai_orchestrator_basic.py -q

# Латентностный smoke-тест (offline)
python scripts/testing/orchestrator_latency_smoke.py --requests 10
```

Подробности: `docs/06-features/AI_PERFORMANCE_GUIDE.md`.

---

## 5. Проверить Kimi/Kimi fallback (при наличии ключей)

```bash
# Бенчмарк Kimi-K2-Thinking
python scripts/testing/kimi_benchmark.py --requests 10 --concurrency 2
```

Если переменные `KIMI_API_KEY` / `KIMI_OLLAMA_URL` не заданы, скрипт просто сообщит, что бенчмарк пропущен.

---

## 6. DR rehearsal + постмортем (staging)

```bash
# Запуск сценария DR rehearsal (например, vault)
python scripts/runbooks/dr_rehearsal_runner.py vault

# Генерация черновика постмортема
python scripts/runbooks/generate_dr_postmortem.py vault --status success
```

План: `docs/runbooks/dr_rehearsal_plan.md`, шаблон: `docs/runbooks/postmortem_template.md`.

---

## 7. Посмотреть пример сценариев Scenario Hub

После запуска backend-а (FastAPI / Orchestrator) можно получить примерные планы
BA→Dev→QA и DR rehearsal в виде JSON:

```bash
curl "http://localhost:8000/api/scenarios/examples?autonomy=A2_non_prod_changes" | jq
```

Подробнее: `docs/architecture/AI_SCENARIO_HUB_REFERENCE.md` и `docs/architecture/TOOL_REGISTRY_REFERENCE.md`.

---

## 8. Запустить YAML-плейбук Scenario Hub (dry-run)

Для локальной проверки структуры плейбука можно выполнить dry-run:

```bash
python scripts/runbooks/run_playbook.py playbooks/ba_dev_qa_example.yaml --autonomy A2_non_prod_changes
```

Аналогично для DR rehearsal:

```bash
python scripts/runbooks/run_playbook.py playbooks/dr_vault_example.yaml --autonomy A2_non_prod_changes
```

И для сценария security-audit:

```bash
python scripts/runbooks/run_playbook.py playbooks/security_audit_example.yaml --autonomy A1_safe_automation
```

Скрипт не выполняет реальные действия — только печатает отчёт по шагам
и уровню риска/автономности сценария.

