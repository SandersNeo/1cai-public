# Data Loaders

Скрипты подготовки исходных данных (конфигурации 1С, документация ITS) перед миграциями и анализом.

| Скрипт | Назначение |
|--------|-----------|
| `load_configurations.py` | Загружает выгрузки конфигураций в локальное хранилище/БД (подготовка к миграциям). |
| `load_its_documentation.py` | Качает материалы ITS, формирует структуру для анализа (`output/its-scraper/`). |

## Пример использования
```bash
python scripts/data/load_configurations.py --src data/raw --dest data/processed
python scripts/data/load_its_documentation.py --output output/its-scraper
```

Перед запуском убедитесь, что заданы пути и credentials (см. `env.example`). Результаты используются скриптами из `scripts/migrations/` и `scripts/analysis/`.
