# 🚀 1C AI Stack - Quick Start

> **Быстрое начало работы с проектом**

---

## 📖 Main Documentation

- **README:** [README.md](README.md) - главная документация проекта
- **Full Docs:** [docs/README.md](docs/README.md) - полная документация
- **Getting Started:** [docs/01-getting-started/](docs/01-getting-started/) - подробные инструкции

---

## 🚀 Quick Start

### 1. Клонирование и установка

```bash
# Клонировать проект
git clone https://github.com/DmitrL-dev/1cai-public.git
cd 1cai-public

# Установить зависимости
pip install -r requirements.txt

# Создать .env файл
cp env.example .env
# Отредактируйте .env и добавьте свои API ключи
```

### 2. Запуск сервисов (Docker)

```bash
# Запустить базы данных
docker-compose up -d

# Проверить статус
docker-compose ps
```

### 3. Запуск backend

```bash
# Вариант 1: MCP Server (для Cursor/Claude Desktop)
python src/ai/mcp_server.py

# Вариант 2: FastAPI Server (REST API)
python src/main.py

# Вариант 3: Telegram Bot
python src/telegram/bot_minimal.py
```

### 4. Проверка

```bash
# REST API
curl http://localhost:8000/health

# MCP Server
curl http://localhost:6001/mcp
```

---

## 📁 Структура проекта

```
1cai-public/
├── src/                    # Основной код
│   ├── ai/                 # AI модули
│   ├── api/                # REST API
│   ├── telegram/           # Telegram Bot
│   └── services/           # Сервисы
├── docs/                   # Документация
│   ├── 01-getting-started/ # Начало работы
│   ├── 02-architecture/    # Архитектура
│   ├── 03-ai-agents/       # AI агенты
│   ├── 04-deployment/      # Деплоймент
│   ├── 05-development/     # Разработка
│   ├── 06-features/        # Фичи
│   ├── 07-itil-analysis/   # ITIL/ITSM
│   └── 08-code-execution/  # Code Execution
├── tests/                  # Тесты
├── scripts/                # Скрипты
├── docker-compose.yml      # Docker конфигурация
├── requirements.txt        # Python зависимости
└── README.md              # Главная документация
```

---

## 🔗 Полезные ссылки

### Документация:
- [Installation Guide](docs/01-getting-started/installation.md) - полная установка
- [Quick Start Guide](docs/01-getting-started/quickstart.md) - быстрый старт
- [Telegram Setup](docs/01-getting-started/telegram-setup.md) - настройка бота
- [Architecture](docs/02-architecture/ARCHITECTURE_OVERVIEW.md) - архитектура
- [API Reference](docs/API_REFERENCE.md) - API документация

### Специальные возможности (NEW!):
- [Code Execution](docs/08-code-execution/) - выполнение кода (98.7% экономия токенов)
- [ITIL/ITSM Analysis](docs/07-itil-analysis/) - Enterprise ITSM
- [OCR Integration](docs/06-features/OCR_INTEGRATION.md) - распознавание документов
- [Voice Queries](docs/06-features/VOICE_QUERIES.md) - голосовые запросы

### Помощь:
- [FAQ](FAQ.md) - часто задаваемые вопросы
- [Troubleshooting](TROUBLESHOOTING.md) - решение проблем
- [Security](SECURITY.md) - безопасность

---

## 💡 Основные возможности

### 🤖 8 AI-Агентов
1. AI Architect - архитектурные решения
2. Developer Agent - генерация кода
3. QA Engineer - тесты
4. DevOps Agent - CI/CD
5. Business Analyst - требования
6. SQL Optimizer - оптимизация запросов
7. Tech Log Analyzer - анализ логов
8. Security Scanner - безопасность

### 🔌 Интеграции
- Telegram Bot (voice + OCR)
- MCP Server (Cursor, VSCode)
- EDT Plugin (Eclipse)
- REST API

### 📊 Технологии
- Python 3.11.x
- FastAPI
- PostgreSQL, Redis, Neo4j, Qdrant
- OpenAI API (GPT-4, Whisper)
- Qwen2.5-Coder (Ollama)
- DeepSeek-OCR

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/DmitrL-dev/1cai-public/issues)
- **Discussions:** [GitHub Discussions](https://github.com/DmitrL-dev/1cai-public/discussions)
- **Documentation:** [docs/](docs/)

---

**License:** MIT  
**Version:** 5.1.0  
**Updated:** November 7, 2025
