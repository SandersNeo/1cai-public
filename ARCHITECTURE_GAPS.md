## План устранения заглушек auth/persistence (marketplace и API)

### 1. Авторизация и идентификация пользователя
- ✅ Внедрить единый Auth Service (FastAPI dependency) с поддержкой JWT access token (refresh в планах).
- ✅ Для внутренних сервисов — зависимость `CurrentUser` (`src/security/auth.py`).
- ✅ Обновить контроллеры (`marketplace`, `github_integration`) — заглушки `user_123`/`admin` удалены.
- ✅ Добавить глобальный middleware для action logging + rate limiting по user_id/IP.
- ✅ M2M/service-токены (при интеграции с другими сервисами).

### 2. Хранение данных marketplace
- ✅ Создать таблицы в PostgreSQL:
  - `plugins` (id, owner_id, status, metadata, created_at, updated_at)
  - `plugin_versions` (plugin_id, version, changelog, artifact_path)
  - `plugin_metrics` (downloads, favorites, rating, trend)
  - `plugin_complaints` (plugin_id, reporter_id, reason, status)
- ✅ Подключить репозиторий (`MarketplaceRepository`, asyncpg) и заменить in-memory storage.
- ✅ Реализовать кэш/Rate limiting (Redis) для выборок.
- ✅ Перенести binary-артефакты в S3/MinIO (сейчас заглушка download_url) — presigned URL по `artifact_path`.

### 3. Модерация и роли
- Определить роли: `user`, `moderator`, `admin`.
- Ввести таблицу `user_roles` или claims в JWT.
- Реализовать проверки ролей в endpoint'ах публикации/аппрува/удаления.
- ✅ События модерации писать в audit-лог (PostgreSQL `security_audit_log` + файл JSON).
- ✅ REST/CLI управление ролями и permissions (`/admin/users/...`).

### 4. API слои
- ✅ Обновить сервисы, которые возвращают статические данные (`get_marketplace_stats`, `download_plugin`) — перейти на реальные запросы в БД/S3.
- ✅ Тренды/featured/calculations перешли на SQL (простая сортировка).
- ✅ Добавить фоновые задачи (Celery/Apscheduler) для расчёта трендов, рейтингов (пока refresh кешей каждые N минут).
- ✅ Настроить Alembic миграции (первый пакет); ➡️ добавить unit/integration тесты для marketplace и миграций.

### 5. Тестирование
- ✅ Написать unit-тесты для ключевых сервисов marketplace (создание, обновление, жалобы) — `tests/unit/test_marketplace_api.py`.
- ✅ Добавить e2e для авторизации и ролевого доступа — `tests/integration/test_marketplace_e2e.py`.
- ✅ Использовать фикстуры с временной БД (pytest-postgresql) и Redis (fakeredis) — реализовано в CI.

### 6. Документация / DevOps
- ✅ Обновить `README`, `docs/06-features` с указанием требований к auth & storage.
- ✅ Добавить переменные окружения в `env.example` (JWT_SECRET, STORAGE_BUCKET, RATE_LIMITS_*).
- ✅ Обновить docker-compose (поднять PostgreSQL/Redis/MinIO для миграций и marketplace).
- ✅ Добавить rate limiting к критическим endpoints (/plugins POST, /artifact POST, /models/create, /ab-tests/create).
- ✅ Добавить чек в CI: прогон миграций + unit/e2e тестов — добавлен job `migrations-check` и marketplace тесты в CI.
- ✅ Code Review — добавлена поддержка TypeScript, Python, JavaScript (`src/api/code_analyzers.py`).
- ✅ Copilot API — реализована оптимизация кода и генерация процедур.
- ✅ Gateway — улучшена аутентификация (использование переменных окружения для API ключей).
