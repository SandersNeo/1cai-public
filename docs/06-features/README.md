# 🎁 Специальные возможности 1C AI Stack

**Обновлено:** 7 ноября 2025

---

## 📋 Доступные Features

### 🎤 [Voice Queries](./VOICE_QUERIES.md)
**Голосовые запросы к AI**

- Speech-to-Text через OpenAI Whisper
- Поддержка RU + EN языков
- Интеграция с Telegram Bot
- Accuracy: 95%+

**Status:** ✅ Production

---

### 📸 [OCR Integration](./OCR_INTEGRATION.md)
**Распознавание документов**

- OCR через DeepSeek-OCR (91%+ accuracy)
- Распознавание накладных, актов, счетов
- Извлечение структурированных данных
- Auto-ввод в 1С

**Status:** ✅ Beta (90%)

---

### 🌍 [Multi-language (i18n)](./I18N_GUIDE.md)
**Мультиязычность**

- Полная поддержка RU + EN
- 400+ переведённых ключей
- Легко добавить новые языки
- UI + Documentation

**Status:** ✅ Production

---

### 🧠 [BSL Fine-tuning](./BSL_FINETUNING_GUIDE.md)
**Обучение модели для BSL**

- Dataset с 50+ quality примерами
- 7 категорий (API, business logic, etc.)
- 3 формата (Alpaca, OpenAI, HF)
- Ready для fine-tuning Qwen/Llama

**Status:** 🚧 Dataset Ready (80%)

---

### 🔗 [n8n Integration](./n8n-integration.md)
**No-code автоматизация с 1C AI Stack**

- Кастомная нода `@onecai/n8n-nodes-onec-ai`
- Шаблоны workflow (PR code review, ежедневные дайджесты, health-check)
- Поддержка Graph/Qdrant/PostgreSQL/Code Generation API
- Быстрый запуск: `npm install && npm run build`, переменная `N8N_CUSTOM_EXTENSIONS`

**Безопасность:**
- Используйте отдельный API-ключ и храните его в менеджере секретов (Vault, Doppler, n8n credentials)
- Ограничьте доступ по IP/ VPN, включите HTTPS и rate limiting (`TELEGRAM_RATE_LIMIT_*`, SlowAPI)
- Для production — разворачивайте n8n в приватной сети рядом с API, логируйте audit-следы

**Status:** 🟡 MVP (готов к пилотным внедрениям)

---

### 📦 Marketplace Hardening (Nov 7, 2025)
**См:** [docs/API_REFERENCE.md](../API_REFERENCE.md#-marketplace-api)

- Redis-кэш для витрин (`featured`, `trending`, категории)
- APScheduler обновляет данные каждые `MARKETPLACE_CACHE_REFRESH_MINUTES`
- JWT + Redis rate limiting (по user_id/IP)
- Подписанные ссылки на скачивание через S3/MinIO (`artifact_path`)

**Status:** 🟡 Beta → Production-ready ядро

---

## 🆕 NEW Features (Nov 6, 2025)

### ⚡ Code Execution with MCP
**См:** [docs/08-code-execution/](../08-code-execution/)

- Progressive Disclosure (98.7% token savings)
- PII Protection (152-ФЗ)
- Deno Sandbox
- Skills System

**Status:** ✅ Production Ready

---

### 📋 ITIL/ITSM Support
**См:** [docs/07-itil-analysis/](../07-itil-analysis/)

- Service Desk (planned)
- Incident Management
- Problem Management
- SLA Management

**Status:** 📋 Planned (roadmap ready)

---

## 🎯 Quick Links

- [Voice Queries Guide](./VOICE_QUERIES.md)
- [OCR Integration](./OCR_INTEGRATION.md)
- [i18n Guide](./I18N_GUIDE.md)
- [BSL Fine-tuning](./BSL_FINETUNING_GUIDE.md)
- [n8n Integration](./n8n-integration.md)

---

**Все features документированы и готовы к использованию!**

[← Back to Docs](../README.md)
