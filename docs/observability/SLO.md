# Service Level Objectives (SLO)

> Обновлено: 10 ноября 2025

## 1. Обзор

SLO определяют целевые показатели доступности и производительности ключевых сервисов 1C AI Stack. SLI (Service Level Indicators) собираются из health-check API и метрик middleware. Error Budget рассчитывается еженедельно.

## 2. API Gateway (Graph API)

| Показатель | Цель | Источник | Комментарии |
|------------|------|----------|-------------|
| Доступность (Availability) | 99.0% за 7 дней | `/health` + мониторинг ответов (200) | Ошибки 5xx/timeout учитываются как недоступность |
| Время ответа (Latency) | < 500 мс p95 | middleware `MetricsMiddleware` | Подключить экспортер в Prometheus/Logs |
| Ошибки запросов | < 1% 5xx | API логи | Считаем отношение 5xx/всего |

## 3. MCP Server

| Показатель | Цель | Источник |
|------------|------|----------|
| Доступность | 98.5% за 7 дней | `/mcp` health | Планируется включить в smoke-tests |
| Среднее время вызова инструмента | < 2 c | логирование `src/ai/mcp_server.py` |

## 4. Marketplace API

| Показатель | Цель | Источник |
|------------|------|----------|
| Доступность | 99.0% | `/marketplace/health` (TODO) |
| Время обновления кеша | ≤ 2 min от планового | APScheduler логи |
| Ошибки модерации | 0 критических | `security_audit_log` |

## 5. Error Budget

- Ошибки = минуты недоступности + превышение латентности > p95.
- Error budget = `(1 - SLO) * 7 дней`.
- При превышении бюджета → freeze фичей, фокус на reliability.

## 6. Мониторинг и отчётность

1. Workflow `dora-metrics.yml` и `github-monitor.yml` — weekly отчёты.
2. Необходимо добавить метрики в observability-стек (Prometheus/Grafana или logs). До внедрения используем health-check + smoke-tests.
3. Каждую неделю публикуем summary в `docs/status/` (TODO).

## 7. Следующие шаги

- [ ] Подключить экспортер/логирование для латентности (FastAPI middleware → Prometheus).
- [ ] Настроить alert runbook (см. `docs/runbooks/alert_slo_runbook.md`).
- [ ] Автоматизировать расчёт SLO (скрипт анализа логов).
- [ ] Настроить выгрузку в Grafana/Prometheus (workflow `observability.yml`).

## 8. Prometheus & Grafana (локально)

- Используйте `make observability-up`, чтобы поднять стек (`observability/docker-compose.observability.yml`).
  - Prometheus: `http://localhost:9090`
  - Grafana: `http://localhost:3000` (логин/пароль: `admin`/`admin` — измените после первого входа).
- Контейнер `smoke-api` экспортирует метрики на `/metrics`; Prometheus забирает их согласно `observability/prometheus.yml`.
- Для остановки используйте `make observability-down`.
- TODO: добавить дешборды Grafana и автоматическую публикацию.

## 9. Следующие шаги

- [ ] Подключить экспортер/логирование для латентности (FastAPI middleware → Prometheus).
- [ ] Настроить alert runbook (см. `docs/runbooks/alert_slo_runbook.md`).
- [ ] Автоматизировать расчёт SLO (скрипт анализа логов).
- [ ] Настроить интеграцию с Grafana (дашборды) и alert channel.
