# Revolutionary Components Module

Модуль для интеграции революционных AI компонентов в основное приложение.

## Компоненты

- **Event-Driven Architecture** - замена Celery на NATS
- **Self-Evolving AI** - самообучающаяся система
- **Self-Healing Code** - автоматическое исправление багов
- **Distributed Agent Network** - P2P сеть агентов
- **Code DNA** - генетическое представление кода
- **Predictive Code Generation** - предиктивная генерация

## Структура

```
src/modules/revolutionary/
├── domain/
│   └── models.py          # Pydantic модели
├── services/
│   └── orchestrator.py    # Оркестратор компонентов
├── api/
│   └── routes.py          # FastAPI роуты
└── README.md
```

## Feature Flags

```bash
# Включить революционные компоненты
export USE_REVOLUTIONARY_ORCHESTRATOR=true
export USE_EVENT_DRIVEN=true
export USE_SELF_EVOLVING=true
export USE_SELF_HEALING=true
export USE_DISTRIBUTED_AGENTS=true
export USE_CODE_DNA=true
export USE_PREDICTIVE_GENERATION=true
```

## Использование

```python
from src.modules.revolutionary.services.orchestrator import RevolutionaryOrchestrator

# Инициализация
orchestrator = RevolutionaryOrchestrator()
await orchestrator.initialize()

# Использование компонентов
await orchestrator.evolve()
await orchestrator.heal()
```

## Метрики

Все компоненты экспортируют Prometheus метрики с префиксом `revolutionary_*`:

- `revolutionary_event_bus_messages_total` - количество сообщений в Event Bus
- `revolutionary_self_evolving_cycles_total` - циклы эволюции
- `revolutionary_self_healing_bugs_fixed_total` - исправленные баги
- и другие...

## Мониторинг

Grafana dashboard: `monitoring/grafana/dashboards/revolutionary_components.json`
