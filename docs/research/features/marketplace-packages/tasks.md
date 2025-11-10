# Задачи: Marketplace Packages

> Создано: 2025-11-10  
> Ведущий: Дмитрий Литвинов

## 1. Основные задачи
- [ ] Подготовить шаблон манифеста и структуру bundle для каждого пакета.
- [ ] Реализовать packaging/publish CLI и make-таргеты.
- [ ] Обновить документацию и FAQ, провести QA/смоук тесты.

## 2. Детализация
| ID | Описание | Тип | Ответственный | Статус |
|----|----------|-----|---------------|--------|
| T-001 | Ревизия репозиториев `onec-markdown-viewer` и `VAEditor`, фиксация лицензий и зависимостей | research | Дмитрий Л. | in_progress |
| T-002 | Создать шаблон `plugin.json`, структуру `dist/marketplace/<id>/` и packaging-скрипт | dev | Дмитрий Л. | pending |
| T-003 | Добавить make-таргеты `package-*`, `publish-*`, интеграция с MinIO | dev | Ирина С. | pending |
| T-004 | Написать `docs/06-features/MARKETPLACE_PACKAGES.md`, обновить README/FAQ | doc | Мария К. | pending |
| T-005 | QA: smoke-download, проверка checksum, обновление `tests/comprehensive/test_full_system.py` | test | QA команда | pending |
| T-006 | Маркетинговые материалы (скриншоты, видео) и публикация в витрине | doc/mkt | DevRel | pending |

## 3. Зависимости
- Репозитории @alkoleft, разрешение использовать артефакты.
- Доступ к MinIO/S3 и учётные записи Marketplace admin.
- Поддержка DevRel (медиа) и QA (смоук-тест).

## 4. Координация и коммуникация
- Канал Telegram `#marketplace`, еженедельный статус по вторникам.
- GitHub issues с меткой `marketplace-package`, ревью через pull request.
- Созвон с @alkoleft при изменениях в исходных репозиториях.

## 5. Готовность к релизу
- [ ] Все задачи помечены статусом `done`.
- [ ] Проверены скрипты качества (`make quality`, `run_full_audit.py`, `make feature-validate`).
- [ ] Документация, changelog и благодарности обновлены.

