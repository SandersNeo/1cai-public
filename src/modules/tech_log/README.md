# Tech Log Analyzer Module

Модуль для анализа технологического журнала 1С согласно Clean Architecture.

## 📁 Структура

```
src/modules/tech_log/
├── domain/          # Models + Exceptions (7 models, 4 exceptions) ✅
├── services/        # 2 Business Logic Services ✅
├── repositories/    # LogPatternsRepository ✅
└── api/             # TechLogAnalyzer integration (planned)
```

## 🎯 Возможности

### 1. Log Parser ✅
Парсинг технологического журнала 1С.

**Features:**
- Tech log file parsing
- Event extraction
- Time period filtering
- Multi-file support

**Пример:**
```python
from src.modules.tech_log.services import LogParser

parser = LogParser()
result = await parser.parse_tech_log(
    log_path="/path/to/tech_log",
    time_period=(start_time, end_time)
)

print(f"Total events: {result.total_events}")
print(f"Events by type: {result.events_by_type}")
```

### 2. Performance Analyzer ✅
Анализ производительности.

**Features:**
- Slow query detection
- Slow method detection
- Performance metrics calculation
- Threshold-based analysis

**Пример:**
```python
from src.modules.tech_log.services import PerformanceAnalyzer

analyzer = PerformanceAnalyzer()
analysis = await analyzer.analyze_performance(events)

print(f"Performance issues: {len(analysis.performance_issues)}")
print(f"Slow queries: {len(analysis.top_slow_queries)}")
print(f"AI recommendations: {analysis.ai_recommendations}")
```

### 3. Error Detector (Planned)
Детекция ошибок.

**Features:**
- Exception analysis
- Error pattern recognition
- Severity classification
- Error grouping

### 4. Recommendation Engine (Planned)
Генерация рекомендаций.

**Features:**
- AI-powered recommendations
- Auto-fix suggestions
- Best practices
- Integration with SQL Optimizer

## 🏗️ Clean Architecture

### Dependency Rule
```
API Layer (TechLogAnalyzer)
    ↓
Services Layer (2 services) ✅
    ↓
Repositories Layer (LogPatternsRepository) ✅
    ↓
Domain Layer (Models + Exceptions) ✅
```

## 📊 Метрики

- **Files Created:** 9
- **Lines of Code:** ~1,500+
  - Domain: ~300 lines
  - Services: ~1,000 lines
  - Repositories: ~100 lines
  - API Layer: 0 lines (planned)
- **Production Ready:** 80%

## 📝 Domain Models

### Tech Log Events
- `TechLogEvent` - Событие технологического журнала
- `LogAnalysisResult` - Результат анализа логов

### Performance Analysis
- `PerformanceIssue` - Проблема производительности
- `PerformanceAnalysisResult` - Результат анализа производительности

### Enums
- `Severity` - CRITICAL, ERROR, WARNING, INFO
- `EventType` - DBMSSQL, SDBL, CALL, EXCP, TLOCK
- `IssueType` - SLOW_QUERY, SLOW_METHOD, LOCK, EXCEPTION

## 📚 См. также

- [DevOps Module README](../devops/README.md)
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
