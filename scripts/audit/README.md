# Audits & Quality Checks

Автоматизированные проверки структуры репозитория, лицензий и безопасности. Обязательны перед публикацией (см. [`docs/research/constitution.md`](../../docs/research/constitution.md)).

| Скрипт | Назначение |
|--------|-----------|
| `comprehensive_project_audit.py` | Полный аудит (структура, документация, зависимости, секреты). Используйте перед релизом. |
| `project_structure_audit.py` | Проверяет соответствие структуре каталогов и обязательных файлов. |
| `architecture_audit.py` | Валидирует архитектурные артефакты, наличие актуальных диаграмм/ADR. |
| `check_architecture_files.py` | Быстрая сверка, что упомянутые архитектурные файлы существуют. |
| `code_quality_audit.py` | Собирает линт/тест результаты, проверяет отчёты. |
| `license_compliance_audit.py` | Проверяет лицензии зависимостей. |
| `check_git_safety.py` | Убеждается, что чувствительные файлы не попали в репозиторий. |

## Запуск
```bash
# Полный аудит
python scripts/audit/comprehensive_project_audit.py

# Проверка структуры
python scripts/audit/project_structure_audit.py
```

Результаты складываются в `output/audit/`. Используйте их в `make preflight` и перед синхронизацией с публичным репозиторием.
