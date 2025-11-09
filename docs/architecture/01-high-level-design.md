# 1C AI Stack — High Level Design (HLD)

> Обновлено: 2025-11-09  
> Ответственный: Архитектурная группа (контакт: architecture@1cai.dev)

Документ описывает архитектуру 1C AI Stack для технических специалистов. Здесь приведены цели продукта, ключевые компоненты, потоки данных, требования к инфраструктуре и схемы взаимодействия. Все диаграммы представлены в формате PlantUML и располагаются в `docs/architecture/uml/`.

---

## 1. Цели и принципы

### 1.1 Бизнес-цели
- Автоматизация разработки, тестирования и сопровождения проектов на платформе «1С:Предприятие».
- Сокращение времени вывода изменений в продакшн (DevOps-подход для 1С).
- Снижение технического долга за счет статического анализа и рекомендаций AI.
- Централизация знаний и лучшая поддержка команд заказчика.

### 1.2 Архитектурные принципы
- **Modular-first** — чёткое разделение по сервисам (API, воркеры, интеграции).
- **AI Augmentation** — AI подсистемы усиливают разработчиков, но не заменяют процессы контроля.
- **Observability by Design** — в систему встроены метрики, трассировки и алерты.
- **Security & Compliance** — RBAC, аудит, защита данных (интеграции, токены, приватные репозитории).
- **Scalability** — горизонтальное масштабирование API и фоновых воркеров; очереди и кластеры БД.

---

## 2. Системный контекст

![System Context](uml/system-context.puml)

**Внешние участники:**
1. **1C Developers / Analysts** — работают в EDT, используют плагин и AI ассистентов.
2. **Ops / DevOps** — управляют деплойментом, мониторингом.
3. **1C IT Staff** — взаимодействуют через UI/Telegram/n8n.
4. **ITS Portal** — источник официальной документации.
5. **Внешние AI сервисы** — модели OpenAI/Qwen, если требуется.

**Система** включает API, воркеры, ML-пайплайны, интеграции (n8n, EDT-плагин, ITS Scraper), базы данных, веторные и графовые хранилища, мониторинг и CI/CD.

---

## 3. Обзор подсистем

### 3.1 API слой
- `src/api/*.py`: Graph API, Auth, Admin, Test Generation, Marketplace.
- Интерфейсы:
  - REST/OAS3 (FastAPI)
  - WebSocket (реальный тайм для IDE)
  - MCP (Model Context Protocol) — универсальная интеграция с IDE (Cursor, VSCode).

### 3.2 Фоновые воркеры
- `src/workers`, `scripts/analysis/*`, `scripts/audit/*`
- Выполняют:
  - Анализ кода/архитектуры (BSL, EDT проекты).
  - Обновления знаний (Neo4j, Qdrant).
  - ML-пайплайны (обучение моделей, генерация датасетов).

### 3.3 Интеграции
- **EDT Plugin** (`edt-plugin/`): View + Actions (`QuickAnalysis`, `ShowCallGraph`, `AnalysisDashboard`).
- **ITS Scraper** (`integrations/its_scraper/`): асинхронный сбор статей, адаптивный rate-limit, stream JSONL, Prometheus-метрики, S3 writers, stateful queue/resume.
- **n8n Node** (`integrations/n8n/`): кастомный коннектор к AI Stack API (credentials, smoke-test, Workflows).
- **Telegram Bot**, **Marketplace** (пакеты/расширения 1С).

### 3.4 Хранилища
- **PostgreSQL** — основная РСУБД (конфигурация, MFA, журналы).
- **Neo4j** — граф зависимостей 1С объектов/функций.
- **Qdrant** — векторные представления кода/документов для семантического поиска.
- **MinIO/S3** — артефакты, бэкапы, выгрузки ITS Scraper.
- **Redis** — кеш, очереди, rate-limiter.

### 3.5 ML/AI сервисы
- `src/ml/*`: тренировка, inference (torch, transformers).
- `scripts/ml/config_utils.py`, `Makefile` — запуск тренировок и оценок.
- Поддержка Qwen, GPT, локальных моделей; pipeline orchestrator.

### 3.6 Observability
- GitHub Actions — CI (lint/test/build, seguridad, модельные проверки).
- Prometheus + Grafana (`monitoring/grafana`): system, business, celery, scraper, etc.
- Loki / Sentry (опционально) — логирование и алертинг.

---

## 4. Компонентная диаграмма

![Component Overview](uml/component-overview.puml)

Основные кластеры:
1. **API Gateway** (FastAPI) → Слой авторизации, маршрутизации, API/Graph/MCP.
2. **Workers/Analyzer** → Celery/Async jobs, ML pipelines, audits.
3. **Integrations** → EDT Plugin, ITS Scraper, n8n, Telegram.
4. **Data Stores** → Postgres, Neo4j, Qdrant, MinIO, Redis.
5. **Monitoring** → Prometheus, Grafana, Alertmanager.

---

## 5. Потоки данных

### 5.1 Обновление знаний из ITS

![ITS Scraper Sequence](uml/its-scraper-sequence.puml)

1. Периодический запуск (`cron` / GitHub Actions / CLI).
2. ITS Scraper собирает статьи (адаптивный rate-limit, очередь).
3. Локальное сохранение + stream → S3, JSONL (если включено).
4. ML-инженеры/воркеры используют новые данные (embeddings → Qdrant, facts → Neo4j).
5. Мониторинг публикует метрики (`its_scraper_*`).

### 5.2 Анализ кода / Audit pipeline

![Data Flow](uml/data-flow.puml)

1. EDT Plugin инициирует анализ → API → Orchestrator.
2. Workers парсят EDT XML → Neo4j/Qdrant/Postgres.
3. Результаты отправляются в Dashboard (Grafana) и в AI ассистента.
4. Telegram/Bot уведомляет заинтересованных лиц (опционально).

---

## 6. Деплоймент

![Deployment](uml/deployment.puml)

### 6.1 Dev/Stage
- Docker Compose (`docker-compose.stage1.yml`)
- Локальные контейнеры: API, Workers, Redis, Postgres, Neo4j, Qdrant, Prometheus, Grafana, MinIO.
- Hot-reload для API, воркеров, интеграций.

### 6.2 Production
- Kubernetes (или Nomad) кластеры.
- Gateway под балансировкой (Nginx/Ingress).
- Autoscaling для workers + ML pods.
- Statefull сервисы (Postgres, Neo4j, Qdrant) — управляются через Helm, с бэкапами и мониторингом.
- Секреты в Vault/Secrets Manager.

---

## 7. Безопасность и соответствие

- RBAC + SCIM: роли, permission матрица (`admin`, `security_officer`, `developer`, `analyst`, `read_only`).
- OAuth2/JWT + Service-to-Service tokens (`X-Service-Token`).
- Аудит действий (базы + JSONL), Security Agent Framework для статического и динамического тестирования.
- Сканирование секретов, large files, политика `.gitignore`.
- Мониторинг CORS, rate limiting (`slowapi`, `Redis`), CSRF для админских функций.
- ITS Scraper уважает robots.txt, rate limit, хранит лог метрик.

---

## 8. Эксплуатация и поддержка

- `docs/MONITORING_GUIDE.md` — описание всех Grafana dashboard (system, business, celery, scraper).
- `Makefile` — универсальный entrypoint (install/test/lint/train/scraper).
- `run_full_audit.py` — комплексные проверки перед релизом.
- CI/CD:
  - PR → линтеры + тесты + security scans.
  - main → интеграционные тесты, публикация артефактов, деплой.
  - public/main → синхронизация документации/примеров.
- Incident Response — Alertmanager → Telegram/Email, fallback процедуры.

---

## 9. Процедуры обновления документации

1. **При функциональных изменениях**:
   - Обновить соответствующие разделы HLD (компонент, data flow, deployment).
   - Дополнить блок «Что нового» в `README.md` и `CHANGELOG.md`.
   - Если добавлены/изменены интеграции — обновить `docs/03-integrations/*`.
2. **Диаграммы**:
   - Обновить `.puml` файлы в `uml/`.
   - Сгенерировать PNG/SVG при необходимости (`plantuml uml/*.puml`).
3. **Мониторинг**:
   - При добавлении дашборда — описать в `docs/MONITORING_GUIDE.md`.
4. **ITS Scraper**:
   - Любые изменения в pipeline должны отражаться в секции 5.1 и соответствующей PlantUML диаграмме.
5. **Версии документа** — фиксировать дату/версию в верхней части файла (как в шапке).

---

## 10. План дальнейшего развития

- CI smoke-tests с использованием mock-сервера для ITS Scraper, n8n, EDT плагина.
- Расширение plug-in writers (BigQuery, Elasticsearch, Kafka).
- Добавление Sequence диаграмм для Marketplace/ML pipelines.
- Автоматический генератор HLD (сбор данных из сервисов → doc update).
- Расширение документации по продуктам (EDT Plugin, Security Framework, ML Ops, Integrations).

---

## 11. Ссылки

- [docs/03-integrations/ITS_SCRAPER.md](../03-integrations/ITS_SCRAPER.md)
- [docs/MONITORING_GUIDE.md](../MONITORING_GUIDE.md)
- [docs/CASE_STUDIES.md](../CASE_STUDIES.md)
- [docs/SUPPORT.md](../SUPPORT.md)
- [README.md](../../README.md)

---

## Примечание

Документ должен оставаться актуальным. Перед релизами выполняйте аудит:
1. Сверка реальных сервисов ↔ диаграммы.
2. Проверка валидности ссылок.
3. Обновление PlantUML и описание потоков при появлении новых сценариев.

