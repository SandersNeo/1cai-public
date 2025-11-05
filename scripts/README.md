# 🛠️ Scripts Directory

Утилитарные скрипты для работы с проектом.

---

## 📁 Структура

### `analysis/`
Скрипты для анализа конфигураций и кода:
- `analyze_*.py` - анализ 1C метаданных, BSL расширений, ITS
- `find_*.py` - поиск конфигураций, API endpoints
- `deep_xml_analysis.py` - глубокий анализ XML
- `check_xml_structure.py` - проверка структуры XML

### `parsers/`
Парсеры для различных форматов:
- `parse_1c_config*.py` - парсеры 1C конфигураций (несколько версий)
- `parse_edt_xml.py` - парсер EDT XML
- `improve_bsl_parser.py` - улучшенный BSL парсер
- `improve_parser_with_mcp.py` - парсер с MCP интеграцией

### `testing/`
Тестовые и проверочные скрипты:
- `test_*.py` - тесты для различных компонентов (ITS API, OCR, XML, etc)
- `check_*.py` - проверки результатов
- `run_demo_tests.py` - запуск демо тестов
- `test_gateway.sh` - тест gateway

### `data/`
Скрипты для работы с данными:
- `load_configurations.py` - загрузка конфигураций
- `load_its_documentation.py` - загрузка документации из ИТС

### `migrations/`
Скрипты миграции данных:
- `migrate_json_to_postgres.py` - миграция JSON → PostgreSQL
- `migrate_postgres_to_neo4j.py` - миграция PostgreSQL → Neo4j
- `migrate_to_qdrant.py` - миграция в Qdrant

### `maintenance/`
Скрипты обслуживания проекта:
- `cleanup_*.py` - очистка проекта
- `cleanup_*.ps1` - очистка (PowerShell)
- `archive_*.ps1` - архивирование

### `setup/`
Скрипты настройки окружения:
- `setup_directories.py` - создание структуры директорий

---

## 🚀 Использование

### Анализ конфигурации:
```bash
python scripts/analysis/analyze_1c_metadata_viewer.py
```

### Парсинг EDT XML:
```bash
python scripts/parsers/parse_edt_xml.py
```

### Запуск тестов:
```bash
python scripts/testing/run_demo_tests.py
```

### Миграция данных:
```bash
python scripts/migrations/migrate_json_to_postgres.py
python scripts/migrations/migrate_postgres_to_neo4j.py
python scripts/migrations/migrate_to_qdrant.py
```

### Очистка проекта:
```bash
python scripts/maintenance/cleanup_project.py
```

---

## 📝 Примечания

- Большинство скриптов требуют настроенного окружения (см. `ENV_EXAMPLE.txt`)
- Для миграций нужны запущенные базы данных (PostgreSQL, Neo4j, Qdrant)
- Перед запуском проверьте requirements.txt

---

**См. также:**
- [Getting Started](../GETTING_STARTED.md)
- [Deployment Instructions](../docs/04-deployment/instructions.md)
- [Project Status](../PROJECT_STATUS.md)
