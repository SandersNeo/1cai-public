# Модуль Анализа Производительности (Performance Analyzer)

## Описание
Модуль предназначен для измерения метрик производительности приложения, в частности времени "холодного" старта и накладных расходов на импорты.

## Структура
Модуль реализован в соответствии с Clean Architecture:

*   `domain/`: Содержит модели данных (`ImportMetric`, `StartupReport`).
*   `services/`: Содержит бизнес-логику профилирования (`StartupProfiler`).
*   `api/`: Содержит точку входа CLI (`cli.py`).

## Использование

### Запуск из командной строки

```bash
python -m src.modules.performance_analyzer.api.cli --modules src.ai src.modules
```

### Программное использование

```python
from src.modules.performance_analyzer.services.profiler import StartupProfiler

profiler = StartupProfiler()
report = profiler.run_analysis(["src.ai"])
print(f"Time: {report.total_time_ms} ms")
```
