# 🔧 Troubleshooting Guide

**Решение типичных проблем**

---

## 🐛 Проблемы при установке

### Ошибка: `ModuleNotFoundError: No module named 'fastapi'`

**Решение:**
```bash
pip install -r requirements.txt

# Или для Telegram бота
pip install -r requirements-telegram.txt
```

---

### Ошибка: `python: command not found`

**Решение:**
```bash
# Windows
# Установите Python 3.11.x с python.org

# Linux
sudo apt-get install python3.11

# Mac
brew install python@3.11
```

---

## 🐳 Проблемы с Docker

### Ошибка: `Cannot connect to the Docker daemon`

**Решение:**
```bash
# Windows: Запустите Docker Desktop

# Linux: Запустите Docker service
sudo systemctl start docker
sudo systemctl enable docker
```

---

### Ошибка: `port is already allocated` (порт 5432, 6379, etc.)

**Решение:**
```bash
# Вариант 1: Остановите другие сервисы на этом порту
docker ps  # Найдите конфликтующий контейнер
docker stop <container_id>

# Вариант 2: Измените порт в docker-compose.yml
# PostgreSQL:
ports:
  - "15432:5432"  # Используйте 15432 вместо 5432
```

---

### Контейнеры постоянно перезапускаются

**Решение:**
```bash
# Проверьте логи
docker-compose logs postgres
docker-compose logs redis

# Частые причины:
# 1. Недостаточно памяти
docker stats

# 2. Неправильные credentials в .env
cat .env | grep POSTGRES_PASSWORD
```

---

## 🤖 Проблемы с Telegram ботом

### Бот не отвечает

**Checklist:**
```bash
# 1. Токен корректный?
cat .env | grep TELEGRAM_BOT_TOKEN
# Должен начинаться с цифр, содержать ':'

# 2. БД запущена?
docker ps | grep postgres
# STATUS должен быть "Up"

# 3. Бот запущен?
# В консоли должно быть:
# "Bot started successfully"

# 4. Проверьте статус бота
# Telegram: @BotFather → /mybots → выберите бота → Bot Settings
# Должен быть "Active"
```

---

### Ошибка: `TelegramBadRequest: Wrong file identifier`

**Решение:**
```python
# Проблема с кэшированием file_id
# Решение: очистите Redis кэш
docker exec -it 1c-ai-redis redis-cli FLUSHDB
```

---

### Бот отвечает медленно (>10 секунд)

**Причины:**
1. **OpenAI API медленный** → используйте локальные модели
2. **Нет кэша** → Redis не запущен
3. **Большая БД** → оптимизируйте запросы

**Решение:**
```bash
# Проверьте Redis
docker exec -it 1c-ai-redis redis-cli PING
# Должен ответить PONG

# Проверьте latency к OpenAI
curl -w "@curl-format.txt" https://api.openai.com/v1/models
```

---

## 🗄️ Проблемы с базами данных

### PostgreSQL: "password authentication failed"

**Решение:**
```bash
# 1. Проверьте .env
cat .env | grep POSTGRES_PASSWORD

# 2. Проверьте docker-compose.yml
cat docker-compose.yml | grep POSTGRES_PASSWORD

# 3. Пересоздайте контейнер
docker-compose down postgres
docker volume rm 1c-ai-postgres-data
docker-compose up -d postgres
```

---

### Redis: "NOAUTH Authentication required"

**Решение:**
```bash
# Redis в MVP не требует пароля
# Проверьте настройки:
docker exec -it 1c-ai-redis redis-cli CONFIG GET requirepass
```

---

### Neo4j: "Unable to connect"

**Решение:**
```bash
# 1. Проверьте что Neo4j запущен
docker ps | grep neo4j

# 2. Проверьте пароль
cat .env | grep NEO4J_PASSWORD

# 3. Дождитесь инициализации (~30 сек)
docker logs -f 1c-ai-neo4j
# Ждите "Started"
```

---

## 🔐 Проблемы с безопасностью

### Ошибка: "Invalid API key"

**Решение:**
```bash
# 1. Проверьте .env
cat .env | grep API_KEY

# 2. Проверьте формат ключа
# OpenAI: должен начинаться с "sk-"
# Anthropic: должен начинаться с "sk-ant-"

# 3. Проверьте что ключ активен
# OpenAI: https://platform.openai.com/api-keys
```

---

### Rate Limit Exceeded

**Решение:**
```bash
# Для Telegram:
# Увеличьте лимиты в .env
TELEGRAM_RATE_LIMIT_MIN=20
TELEGRAM_RATE_LIMIT_DAY=200

# Для OpenAI:
# Проверьте квоты: https://platform.openai.com/account/limits
```

---

## 🚀 Проблемы с deployment

### Kubernetes: Pods в состоянии "CrashLoopBackOff"

**Решение:**
```bash
# 1. Проверьте логи
kubectl logs <pod-name>

# 2. Проверьте secrets
kubectl get secrets -n 1c-ai-stack

# 3. Проверьте ресурсы
kubectl describe pod <pod-name>
```

---

### GitHub Actions: Build fails

**Решение:**
```bash
# 1. Проверьте secrets в GitHub
# Settings → Secrets → Actions
# Должны быть: DOCKER_USERNAME, DOCKER_PASSWORD

# 2. Проверьте .github/workflows/
cat .github/workflows/build.yml

# 3. Проверьте логи
# GitHub → Actions → выберите failed run
```

---

## 📱 Проблемы с feature-specific

### Voice Queries не работают

**Решение:**
```bash
# Проверьте что OpenAI API ключ настроен
cat .env | grep OPENAI_API_KEY

# Без OpenAI - voice queries не работают
# (требуется Whisper API)
```

---

### OCR не распознает текст

**Частые причины:**
1. **Плохое качество изображения** → сделайте фото с хорошим освещением
2. **Нет OpenAI ключа** → настройте или используйте альтернативу
3. **Неподдерживаемый формат** → используйте JPG, PNG

---

## 🔍 Диагностика

### Полная диагностика системы

```bash
# 1. Проверка Docker
docker ps

# 2. Проверка сети
docker network ls | grep 1c-ai

# 3. Проверка volumes
docker volume ls | grep 1c-ai

# 4. Проверка здоровья всех сервисов
curl http://localhost:8000/health  # FastAPI
curl http://localhost:6001/health  # MCP Server

# 5. Проверка БД
docker exec -it 1c-ai-postgres pg_isready
docker exec -it 1c-ai-redis redis-cli PING
```

---

### Логи для отладки

```bash
# Все логи
docker-compose logs

# Конкретный сервис
docker-compose logs postgres
docker-compose logs redis
docker-compose logs telegram-bot

# Follow (real-time)
docker-compose logs -f telegram-bot
```

---

## 📞 Не помогло?

### Создайте issue с максимумом информации:

```markdown
**Описание проблемы:**
[опишите что не работает]

**Шаги для воспроизведения:**
1. ...
2. ...

**Ожидаемое поведение:**
[что должно было произойти]

**Фактическое поведение:**
[что произошло]

**Окружение:**
- OS: [Windows 11 / Ubuntu 22.04 / macOS]
- Python: [3.11.5]
- Docker: [20.10.21]

**Логи:**
```
[вставьте релевантные логи]
```
```

**Ссылка:** https://github.com/DmitrL-dev/1cai-public/issues/new

---

**Обновлено:** 6 ноября 2025  
**Следующее обновление:** По мере накопления проблем

