# Project Manager Module

Модуль для project management согласно Clean Architecture.

## 📁 Структура

```
src/modules/project_manager/
├── domain/          # Models + Exceptions (planned)
├── services/        # 6 Business Logic Services (planned)
├── repositories/    # EstimationRepository (planned)
└── api/             # ProjectManagerAgent integration (planned)
```

## 🎯 Возможности

### 1. Task Decomposer (Planned)
Декомпозиция задач.

**Features:**
- Task decomposition
- Complexity analysis
- Subtask generation

### 2. Effort Estimator (Planned)
Оценка трудозатрат.

**Features:**
- Effort estimation
- Risk factor analysis
- Confidence calculation

### 3. Sprint Planner (Planned)
Планирование спринтов.

**Features:**
- Sprint planning
- Capacity allocation
- Task prioritization

### 4. Resource Allocator (Planned)
Распределение ресурсов.

**Features:**
- Resource allocation
- Skill matching
- Team optimization

### 5. Risk Assessor (Planned)
Оценка рисков.

**Features:**
- Risk assessment
- Risk scoring
- Mitigation strategies

### 6. Progress Tracker (Planned)
Отслеживание прогресса.

**Features:**
- Progress tracking
- Variance analysis
- Completion metrics

## 🏗️ Clean Architecture

### Dependency Rule
```
API Layer (ProjectManagerAgent)
    ↓
Services Layer (6 services - planned)
    ↓
Repositories Layer (EstimationRepository - planned)
    ↓
Domain Layer (Models + Exceptions - planned)
```

## 📊 Метрики

- **Files Created:** 1 (docs only)
- **Lines of Code:** ~0
  - Domain: 0 lines (planned)
  - Services: 0 lines (planned)
  - Repositories: 0 lines (planned)
- **Production Ready:** 5%

## 📝 Domain Models (Planned)

### Task Management
- `Task` - Task definition
- `TaskDecomposition` - Decomposition result

### Effort Estimation
- `EffortEstimate` - Effort estimate
- `EffortEstimationResult` - Estimation result

### Sprint Planning
- `SprintPlan` - Sprint plan
- `TeamMember` - Team member

### Resource Allocation
- `ResourceAllocation` - Resource allocation

### Risk Management
- `Risk` - Risk definition
- `RiskAssessment` - Risk assessment

### Progress Tracking
- `ProgressReport` - Progress report

## 📚 См. также

- [DevOps Module README](../devops/README.md)
- [Business Analyst Module README](../business_analyst/README.md)
- [QA Module README](../qa/README.md)
- [Architect Module README](../architect/README.md)
- [Security Module README](../security/README.md)
- [Technical Writer Module README](../technical_writer/README.md)
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
