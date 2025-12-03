# Technical Writer Module

Модуль для генерации технической документации согласно Clean Architecture.

## 📁 Структура

```
src/modules/technical_writer/
├── domain/          # Models + Exceptions (13 models, 5 exceptions) ✅
├── services/        # 4 Business Logic Services ✅
├── repositories/    # TemplatesRepository ✅
└── api/             # TechnicalWriterAgent integration (planned)
```

## 🎯 Возможности

### 1. API Documentation Generator ✅
Генерация API документации.

**Features:**
- OpenAPI 3.0 spec generation
- Markdown docs generation
- Examples generation
- Postman collection generation

**Пример:**
```python
from src.modules.technical_writer.services import APIDocGenerator

generator = APIDocGenerator()
docs = await generator.generate_api_docs(
    code="Функция GetUsers()...",
    module_type="http_service"
)

print(f"Endpoints: {docs.endpoints_count}")
print(docs.markdown_docs)
```

### 2. User Guide Generator ✅
Генерация руководств пользователя.

**Features:**
- Section generation (audience-specific)
- FAQ generation
- Markdown assembly

**Пример:**
```python
from src.modules.technical_writer.services import UserGuideGenerator
from src.modules.technical_writer.domain.models import Audience

generator = UserGuideGenerator()
guide = await generator.generate_user_guide(
    feature="User Management",
    target_audience=Audience.END_USER
)

print(guide.guide_markdown)
```

### 3. Release Notes Generator ✅
Генерация release notes.

**Features:**
- Conventional Commits parsing
- Categorization (features, fixes, breaking)
- Migration guide generation

**Пример:**
```python
from src.modules.technical_writer.services import ReleaseNotesGenerator

generator = ReleaseNotesGenerator()
notes = await generator.generate_release_notes(
    git_commits=[
        {"message": "feat: add new feature"},
        {"message": "fix: bug fix"}
    ],
    version="v1.2.0"
)

print(notes.markdown)
```

### 4. Code Documentation Generator ✅
Генерация документации для кода.

**Features:**
- BSL function documentation
- Parameter extraction
- Return type detection

**Пример:**
```python
from src.modules.technical_writer.services import CodeDocGenerator

generator = CodeDocGenerator()
doc = await generator.document_function(
    function_code="Функция GetUserByID(UserID)...",
    language="bsl"
)

print(doc.documented_code)
```

  - Services: 0 lines (planned)
  - Repositories: 0 lines (planned)
- **Production Ready:** 30%

## 🔄 Migration Guide

### From technical_writer_agent_extended.py

**Old:**
```python
from src.ai.agents.technical_writer_agent_extended import (
    APIDocumentationGenerator
)

generator = APIDocumentationGenerator()
result = await generator.generate_api_docs(code)
```

**New (planned):**
```python
from src.modules.technical_writer.services import APIDocGenerator

generator = APIDocGenerator()
result = await generator.generate_api_docs(code)
# Returns APIDocumentation (Pydantic model)
```

## 📝 Domain Models

### API Documentation
- `APIEndpoint` - API endpoint definition
- `APIParameter` - Parameter definition
- `APIExample` - Usage example
- `APIDocumentation` - Complete API docs

### User Guide
- `GuideSection` - Guide section
- `FAQItem` - FAQ item
- `UserGuide` - Complete user guide

### Release Notes
- `ReleaseNotes` - Release notes with features/fixes/breaking

### Code Documentation
- `Parameter` - Function parameter
- `FunctionDocumentation` - Function docs

## 🐛 Known Issues

- Services layer - not implemented (planned)
- Repositories layer - not implemented (planned)
- API layer integration - not implemented (planned)

## 🤝 Contributing

При добавлении новых функций:
1. Создайте domain model в `domain/models.py`
2. Реализуйте service в `services/`
3. Добавьте метод в `TechnicalWriterAgent`
4. Напишите тесты
5. Обновите документацию

## 📚 См. также

- [DevOps Module README](../devops/README.md)
- [Business Analyst Module README](../business_analyst/README.md)
- [QA Module README](../qa/README.md)
- [Architect Module README](../architect/README.md)
- [Security Module README](../security/README.md)
- [Constitution](../../docs/research/constitution.md)

---

## 🚀 8. Unified Intelligence (v3.0)

**Мы совершили квантовый скачок. Платформа превратилась в Единую Интеллектуальную ОС.**
Больше никаких разрозненных инструментов. Только **Single Pane of Glass**.

### 1. 🚀 Unified Workspace (Единое Окно)
Мы объединили **VS Code**, **NocoBase**, **Portainer** и **Gitea** в один бесшовный портал.
Вы пишете код, управляете задачами и следите за серверами, не переключая вкладки.

![Unified Dashboard](../../../docs/assets/images/portal_dashboard_v3.png)

### 2. 🧠 RLTF (Reinforcement Learning from Task Feedback)
Система перешла от "выполнения команд" к **самообучению**.
*   **Feedback Loop:** Каждое ваше действие (Save, Commit, Run) — это сигнал для обучения.
*   **Action Prediction:** ИИ предугадывает ваш следующий шаг (например, предлагает "Commit" после успешного теста).
*   **Context Awareness:** "Глаза" системы видят, что происходит в браузере в реальном времени.

### 3. 🔍 Global Search (Brain Index)
Мгновенный поиск по всему:
*   📦 **Код** (Git)
*   ✅ **Задачи** (NocoBase)
*   📄 **Документация** (Wiki)

![Global Search](../../../docs/assets/images/portal_global_search.png)

**Итог:** Это больше не набор скриптов. Это **Secure Enterprise OS**, которая думает вместе с вами.
