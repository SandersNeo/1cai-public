# План подготовки Marketplace-пакетов (onec-markdown-viewer, VAEditor)

## Цели

- Сформировать требования к публикации расширений `onec-markdown-viewer` и `VAEditor` в нашем Marketplace.
- Определить необходимые артефакты (bundle, manifest, документация, медиаматериалы).
- Согласовать процесс модерации, обновлений и метрик в связке с текущим `MarketplaceRepository`.

## Текущее состояние

- API/хранилище Marketplace реализованы (`src/api/marketplace.py`, `src/db/marketplace_repository.py`, MinIO/S3 артефакты, Redis cache, аудит).  
- UI/CLI упаковщика отсутствует; пакеты `onec-markdown-viewer` и `VAEditor` в репозитории не представлены.  
- Документация по стандарту упаковки (structure, manifest.json, README, changelog) не подготовлена.

## Требования к пакетам

1. **Структура**: zip-архив с подпапками `plugin/`, `docs/`, `assets/`.  
2. **Manifest** (`plugin.json`):
   - `id`, `name`, `version`, `category`, `supported_platforms`, `min_version`, `permissions`, `commands`.  
   - Ссылки на исходный код и лицензии.
3. **Документация**:
   - README (установка/использование), CHANGELOG, FAQ.  
   - Скриншоты (PNG 1280×720) + иконка 512×512 PNG.
4. **Артефакты**:
   - Собранный плагин (jar/vsix) + вспомогательные файлы.  
   - SHA256 checksum.
5. **Метаданные для API**: описание, ключевые слова, лицензия, категория (`integration`/`ui_theme`).

## Процесс публикации

1. Подготовить bundle локально (скрипт `tools/package_plugin.py`).  
2. Загрузить артефакт в S3/MinIO (`/marketplace/plugins/{id}/artifact`).  
3. Заполнить `PluginSubmitRequest` через CLI (`scripts/marketplace/publish_plugin.py`).  
4. Проход модерации (роль `admin`): проверка файла, метаданных, безопасности.  
5. После одобрения: рассылка уведомлений, обновление витрины.

## План работ

- Шаг 1. Ревизия исходных репозиториев (структура, зависимости, лицензия).  
- Шаг 2. Разработка шаблона манифеста и чек-листа артефактов.  
- Шаг 3. Скрипт упаковки (zip + checksum) + make-таргет `make package-<plugin>`.  
- Шаг 4. CLI/automation для загрузки и публикации (использовать существующие API).  
- Шаг 5. Обновление документации (README, docs/architecture/… раздел Marketplace).  
- Шаг 6. Подготовка маркетинговых материалов (описание, скриншоты, pricing/monetization).  
- Шаг 7. Smoke-тесты: скачивание пакета, проверка целостности, review workflow.

## Дополнительные задачи

- Настроить мониторинг скачиваний и отзывов (метрики уже есть в API → нужно подключить дашборд).  
- Рассмотреть опцию платной подписки (интеграция с billing API).  
- Подготовить SLA на обновления и процедуру отзывов/депубликации.
