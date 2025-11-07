# 💻 Development - Разработка

Документация для разработчиков

---

## 📚 Содержание раздела

1. **[CHANGELOG.md](./CHANGELOG.md)** - история изменений
2. **[edt-plugin/](./edt-plugin/)** - EDT plugin development
3. **[scripts/](./scripts/)** - Utility scripts

---

## 🛠️ Development Setup

```bash
# Install dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Lint
black src/
flake8 src/
```

---

## 📝 Contributing

См. [Contributing Guide](../01-getting-started/CONTRIBUTING.md)

---

## 🔍 Автоматические проверки

Перед любыми коммитами и пушами запускайте полный аудит:

```bash
python run_full_audit.py --stop-on-failure
```

Скрипт последовательно выполняет:

- Проверку всех ссылок (`check_all_links.py` → `BROKEN_LINKS_REPORT.txt`)
- Комплексный аудит структуры (`comprehensive_project_audit_final.py`)
- Security-проверку (`check_security_comprehensive.py`)
- Сверку README и кода (`check_readme_vs_code.py`)

Опционально добавьте `--include-cleanup`, чтобы удалить временные отчёты из корня.

## 🗄️ Database Migrations

```bash
python scripts/run_migrations.py
```

- Использует Alembic (`alembic.ini`, `db/alembic/`)
- Учитывает `DATABASE_URL` из `.env`
- Запускайте перед стартом backend и при деплое
- Для интеграционных тестов задайте `TEST_DATABASE_URL` (например, на тестовую PostgreSQL), чтобы `pytest -m integration` мог проверить `MarketplaceRepository`

### Управление ролями

```bash
python scripts/manage_roles.py grant-role user-1 admin --assigned-by=system
python scripts/manage_roles.py grant-permission user-1 marketplace:approve
```

- Скрипт использует активное подключение к БД (`DATABASE_URL`)
- Записи сохраняются в таблицах `user_roles` и `user_permissions`
- Для REST-управления используйте endpoints `/admin/users/{user_id}/roles` и `/permissions` (требуется роль `admin`)

## 🔑 Аутентификация (JWT)

Используйте Bearer токены для защищённых endpoints:

```bash
# Получить токен (демо-учётки задаются через AUTH_DEMO_USERS)
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=<your_username>&password=<your_password>"

# Вызвать защищённый endpoint
curl http://localhost:8000/marketplace/plugins \
  -H "Authorization: Bearer <your_token>"

# Проверить текущего пользователя
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer <your_token>"
```

В production установите собственные значения `JWT_SECRET`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` и переопределите `AUTH_DEMO_USERS`.

[← Deployment](../04-deployment/) | 

