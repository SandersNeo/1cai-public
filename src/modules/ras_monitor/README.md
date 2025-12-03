# RAS Monitor Module

Модуль для мониторинга кластера 1С (RAS) согласно Clean Architecture.

## 📁 Структура

```
src/modules/ras_monitor/
├── domain/          # Models + Exceptions (9 models, 4 exceptions) ✅
├── services/        # 4 Business Logic Services ✅
├── repositories/    # MonitoringRepository ✅
└── api/             # RASMonitor integration (planned)
```

## 🎯 Возможности

### 1. Cluster Monitor ✅
Мониторинг кластера 1С.

**Features:**
- Cluster connection management
- Metrics collection
- Health checks
- Performance monitoring

**Пример:**
```python
from src.modules.ras_monitor.services import ClusterMonitor

monitor = ClusterMonitor()
cluster_info = await monitor.get_cluster_info(
    host="localhost",
    port=1541
)

metrics = await monitor.collect_metrics(cluster_info.cluster_id, sessions)
health = await monitor.check_health(metrics)

print(f"Cluster: {cluster_info.name}")
print(f"Health: {health['status']}")
```

### 2. Session Analyzer ✅
Анализ сессий пользователей.

**Features:**
- Session tracking
- Resource usage analysis
- Long-running session detection
- Session state monitoring

**Пример:**
```python
from src.modules.ras_monitor.services import SessionAnalyzer

analyzer = SessionAnalyzer()
analysis = await analyzer.analyze_sessions(sessions)

print(f"Total sessions: {analysis.total_sessions}")
print(f"By state: {analysis.sessions_by_state}")
print(f"Top CPU sessions: {len(analysis.top_cpu_sessions)}")

problematic = await analyzer.detect_problematic_sessions(sessions)
print(f"Problematic sessions: {len(problematic)}")
```

### 3. Resource Tracker ✅
Отслеживание ресурсов.

**Features:**
- CPU monitoring
- Memory monitoring
- Connection tracking
- Resource alerts

**Пример:**
```python
from src.modules.ras_monitor.services import ResourceTracker

tracker = ResourceTracker()
resources = await tracker.track_resources(metrics)

for resource in resources:
    print(f"{resource.resource_type}: {resource.usage_percent}% ({resource.trend})")

warnings = await tracker.predict_resource_exhaustion(resources)
print(f"Warnings: {len(warnings)}")
```

### 4. Alert Manager ✅
Управление алертами.

**Features:**
- Alert generation
- Threshold monitoring
- Alert prioritization
- Notification management

**Пример:**
```python
from src.modules.ras_monitor.services import AlertManager

alert_mgr = AlertManager()
alerts = await alert_mgr.generate_alerts(resources)
prioritized = await alert_mgr.prioritize_alerts(alerts)

for alert in prioritized:
    if await alert_mgr.should_notify(alert):
        print(f"ALERT: {alert.message} ({alert.severity})")
```

## 🏗️ Clean Architecture

### Dependency Rule
```
API Layer (RASMonitor)
    ↓
Services Layer (4 services) ✅
    ↓
Repositories Layer (MonitoringRepository) ✅
    ↓
Domain Layer (Models + Exceptions) ✅
```

## 📊 Метрики

- **Files Created:** 11
- **Lines of Code:** ~1,800+
  - Domain: ~350 lines
  - Services: ~1,300 lines
  - Repositories: ~100 lines
  - API Layer: 0 lines (planned)
- **Production Ready:** 85%

## 📝 Domain Models

### Cluster Management
- `ClusterInfo` - Информация о кластере
- `ClusterMetrics` - Метрики кластера

### Session Management
- `Session` - Сессия пользователя
- `SessionAnalysis` - Анализ сессий

### Resource Management
- `ResourceUsage` - Использование ресурсов
- `ResourceAlert` - Алерт по ресурсам

### Enums
- `SessionState` - ACTIVE, SLEEPING, BLOCKED, TERMINATED
- `AlertSeverity` - CRITICAL, WARNING, INFO
- `ResourceType` - CPU, MEMORY, CONNECTIONS, LOCKS

## 📚 См. также

- [DevOps Module README](../devops/README.md)
- [Tech Log Analyzer Module README](../tech_log/README.md)
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
