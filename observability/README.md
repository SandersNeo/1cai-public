# 📡 Observability Stack

Конфигурации для Prometheus, Grafana, Alertmanager и вспомогательных инструментов.

| Файл/папка | Назначение |
|------------|------------|
| `docker-compose.observability.yml` | Локальный стек наблюдаемости (`make observability-up`). |
| `prometheus.yml`, `alertmanager.yml`, `alerts.yml` | Настройки метрик и алертов. |
| `grafana/dashboards/` | JSON-дашборды (например, `finops_cost.json`).

## Запуск локально
```bash
make observability-up
# Стоп
make observability-down
```

После запуска:
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000` (admin/admin — смените пароль)
- Alertmanager: `http://localhost:9093`

Больше деталей и инструкции по Kubernetes см. в [docs/observability/README.md](../docs/observability/README.md).
