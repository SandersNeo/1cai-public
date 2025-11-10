# Спецификация: Marketplace Packages

> Создано: 2025-11-10  
> Связанный план: `plan.md`

## 1. Обзор
- Marketplace должен содержать минимум два готовых пакета (`onec-markdown-viewer`, `VAEditor`), собранных и опубликованных по единому стандарту.
- Термины: *bundle* — zip архив плагина, *manifest* — `plugin.json`, *submission CLI* — скрипт публикации через API, *moderation* — ручной шаг администратора.

## 2. Требования
### 2.1 Функциональные
- [ ] Скрипт упаковки `scripts/marketplace/package_plugin.py --plugin <id>` формирует zip/sha256 и проверяет структуру.
- [ ] Make-таргеты `package-markdown-viewer` и `package-vaeditor` используют скрипт и кладут артефакты в `dist/marketplace/<id>/`.
- [ ] CLI `scripts/marketplace/publish_plugin.py` (или обёртка make) загружает bundle в MinIO и отправляет `PluginSubmitRequest`.
- [ ] В Marketplace появляются записи с заполненными полями (name, version, description, screenshots, license).
- [ ] Документация `docs/06-features/MARKETPLACE_PACKAGES.md` описывает процесс и требования.

### 2.2 Нефункциональные
- Размер архива ≤ 50 МБ; публикация выполняется < 2 минут в CI.
- Безопасность: манифест содержит SHA256, импортируемые зависимости перечислены; артефакты хранятся в приватном бакете до публикации.
- UX: README пакета включает шаги установки, troubleshooting и ссылку на исходный код.

### 2.3 Ограничения и допущения
- Требуется рабочий доступ к MinIO/S3 и admin-роль в Marketplace API.
- Релизная ветка пакетов — master/main в соответствующих репозиториях @alkoleft, используем разрешённые лицензии (MIT/Apache-2.0).
- CLI использует текущую авторизацию Marketplace (JWT сервисного пользователя).

## 3. Архитектура и дизайн
- Последовательность: packaging → upload → submit → moderation → publish (диаграмма C4 update в `docs/architecture/uml/marketplace-sequence.puml`, обновить при реализации).
- Интеграции: MinIO/S3 (хранение), PostgreSQL (метаданные), Redis (кеш), Admin API (moderation).
- Скрипты используют существующие Python-клиенты (`MarketplaceRepository`, `StorageService`).

## 4. Пользовательские сценарии
- **UC1 — Разработчик пакует `onec-markdown-viewer`**  
  Шаги: клонировать репо → `make package-markdown-viewer` → получить zip и checksum → `make publish-markdown-viewer` → отправка submission → admin approve.  
  Результат: пакет доступен в витрине с документацией.
- **UC2 — Администратор модерирует пакет**  
  Шаги: открыть админ-панель → проверить чек-лист (checksum, лицензия, скриншоты) → нажать Approve → статус `published`.  
  Результат: запись видна клиентам, ссылки скачивания рабочие.
- **UC3 — Пользователь скачивает пакет**  
  Шаги: открыть Marketplace UI/API → скачать zip → проверить checksum → установить в 1C/VS Code.  
  Результат: установка проходит без ошибок, README соответствует поведению.

## 5. Приемочные критерии
- [ ] В vitrine Marketplace есть две карточки с валидными артефактами и скриншотами.
- [ ] `make package-*` и `make publish-*` выполняются успешно в CI/локально.
- [ ] Документация и FAQ обновлены; README содержит раздел Marketplace Showcase.
- [ ] Смоук-тест скачивания и установки пройден (лог в `tests/comprehensive/test_full_system.py`).

## 6. Тестирование
- Unit: тесты для packaging CLI (валидация манифеста, checksum).
- Integration: сценарий `tests/integration/test_marketplace_migrations.py` дополняется проверкой загрузки/модерации.
- Е2Е: скрипт smoke-проверки (скачивание пакета, проверка SHA256).
- Acceptance: чек-лист QA (установка в EDT/VS Code).

## 7. Риски и планы реагирования
- Несовместимость версий плагинов — поддерживаем compatibility matrix и блокируем публикацию при расхождении.
- Недостаток медиаматериалов — заранее запросить у авторов, при необходимости сделать скринкасты сами.
- Сбой MinIO — дублировать артефакты в GitHub Releases (временная мера).

## 8. Связанные документы
- `docs/research/marketplace_integration_plan.md`
- Репозитории: [alkoleft/onec-markdown-viewer](https://github.com/alkoleft/onec-markdown-viewer), [alkoleft/VAEditor](https://github.com/alkoleft/VAEditor) — благодарим авторов за открытые исходники.
- `docs/architecture/01-high-level-design.md` (раздел Marketplace), диаграммы `docs/architecture/uml/marketplace-sequence.puml`.

