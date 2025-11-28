# Architect Module

Модуль для архитектурного анализа согласно Clean Architecture.

## 📁 Структура

```
src/modules/architect/
├── domain/          # Models + Exceptions (10 models, 4 exceptions)
├── services/        # 3 Business Logic Services
├── repositories/    # ArchitecturePatternsRepository
└── api/             # ArchitectAgentEnhanced integration
```

## 🎯 Возможности

### 1. Architecture Analyzer
Глубокий анализ архитектуры с расчетом метрик.

**Features:**
- Coupling analysis
- Cohesion analysis
- Cyclic dependencies detection
- God objects detection
- Orphan modules detection
- Overall score calculation (1-10)

**Пример:**
```python
from src.modules.architect.services import ArchitectureAnalyzer

analyzer = ArchitectureAnalyzer()
result = await analyzer.analyze_architecture(
    config_name="УправлениеТорговлей",
    deep_analysis=True
)

print(f"Overall score: {result.metrics.overall_score}/10")
print(f"Coupling: {result.metrics.coupling_score}")
print(f"Cohesion: {result.metrics.cohesion_score}")
print(f"Health status: {result.health_status}")
print(f"Anti-patterns found: {len(result.anti_patterns)}")
```

### 2. ADR Generator
Генерация Architecture Decision Records.

**Features:**
- ADR generation
- Template rendering (Markdown)
- Alternatives comparison
- Consequences analysis

**Пример:**
```python
from src.modules.architect.services import ADRGenerator
from src.modules.architect.domain.models import ADRStatus

generator = ADRGenerator()
adr = await generator.generate_adr(
    title="Переход на микросервисную архитектуру",
    context="Монолитная архитектура не масштабируется",
    problem="Невозможность независимого развертывания",
    decision="Разделить на микросервисы",
    alternatives=[
        {
            "name": "Модульный монолит",
            "pros": ["Простота", "Меньше overhead"],
            "cons": ["Ограниченная масштабируемость"]
        }
    ],
    consequences={
        "positive": ["Улучшенная масштабируемость"],
        "negative": ["Увеличенная сложность"],
        "risks": ["Проблемы с производительностью"]
    },
    status=ADRStatus.PROPOSED
)

# Render to Markdown
markdown = generator.render_adr_markdown(adr)
print(markdown)
```

### 3. Anti-Pattern Detector
Детекция anti-patterns в архитектуре.

**Features:**
- God object detection
- Circular dependency detection
- Tight coupling detection
- Low cohesion detection
- Refactoring recommendations

**Пример:**
```python
from src.modules.architect.services import AntiPatternDetector

detector = AntiPatternDetector()
patterns = await detector.detect_anti_patterns(
    config_name="УправлениеТорговлей"
)

for pattern in patterns:
    print(f"{pattern.type.value} - {pattern.severity.value}")
    print(f"Location: {pattern.location}")
    print(f"Recommendation: {pattern.recommendation}")
    print(f"Effort: {pattern.refactoring_effort.value}")
```

## 🔌 API Layer Integration

### ArchitectAgentEnhanced

**Новые методы:**
```python
from src.ai.agents.architect_agent_enhanced import (
    ArchitectAgentEnhanced
)

agent = ArchitectAgentEnhanced()

# Architecture analysis
result = await agent.analyze_architecture_enhanced(
    config_name="УправлениеТорговлей",
    deep_analysis=True
)

# ADR generation
adr = await agent.generate_adr_enhanced(
    title="...",
    context="...",
    problem="...",
    decision="...",
    alternatives=[...],
    consequences={...}
)

# Anti-pattern detection
patterns = await agent.detect_anti_patterns_enhanced(
    config_name="УправлениеТорговлей"
)
```

**Dependency Injection:**
```python
from src.modules.architect.services import ArchitectureAnalyzer

custom_analyzer = ArchitectureAnalyzer()
agent = ArchitectAgentEnhanced(
    architecture_analyzer=custom_analyzer
)
```

## 🏗️ Clean Architecture

### Dependency Rule
```
API Layer (ArchitectAgentEnhanced)
    ↓
Services Layer (3 services)
    ↓
Repositories Layer (ArchitecturePatternsRepository)
    ↓
Domain Layer (Models + Exceptions)
```

### SOLID Principles
✅ Single Responsibility - каждый сервис одна задача  
✅ Open/Closed - расширяемость через dependency injection  
✅ Liskov Substitution - все сервисы взаимозаменяемы  
✅ Interface Segregation - минимальные интерфейсы  
✅ Dependency Inversion - зависимость от абстракций  

## 📊 Метрики

- **Files Created:** 11
- **Lines of Code:** ~2,800+
  - Domain: ~400 lines
  - Services: ~1,800 lines
  - Repositories: ~100 lines
  - API Layer: ~100 lines (integration)
- **Production Ready:** 85%

## 🔄 Migration Guide

### From architect_agent_extended.py

**Old (extended):**
```python
from src.ai.agents.architect_agent_extended import (
    ArchitectAgentExtended
)

agent = ArchitectAgentExtended()
result = await agent.analyze_architecture_graph(config_name)
```

**New (enhanced with Clean Architecture):**
```python
from src.ai.agents.architect_agent_enhanced import (
    ArchitectAgentEnhanced
)

agent = ArchitectAgentEnhanced()
result = await agent.analyze_architecture_enhanced(config_name)
# Returns ArchitectureAnalysisResult (Pydantic model)
```

**Backward Compatibility:**
- Legacy методы сохранены (analyze_architecture, generate_c4_diagram, etc.)
- Новые методы с суффиксом `_enhanced`

## 📝 Architecture Metrics

### Coupling Score
- **Range:** 0-1 (lower is better)
- **Target:** < 0.3
- **Formula:** dependencies / max_possible_connections

### Cohesion Score
- **Range:** 0-1 (higher is better)
- **Target:** > 0.7
- **Formula:** shared_data_usage / total_functions

### Overall Score
- **Range:** 1-10
- **Calculation:**
  - Base: 10.0
  - Penalty: coupling * 3
  - Bonus: (cohesion - 0.5) * 2
  - Penalty: cycles * 0.5
  - Penalty: god_objects * 1.0

### Health Status
- **Excellent:** 9-10
- **Good:** 7-8
- **Acceptable:** 5-6
- **Poor:** 3-4
- **Critical:** 1-2

## 🐛 Known Issues

- Neo4j Change Graph integration - stub (requires configuration)
- Mock data для coupling/cohesion analysis (в реальности - Neo4j)

## 🤝 Contributing

При добавлении новых функций:
1. Создайте domain model в `domain/models.py`
2. Реализуйте service в `services/`
3. Добавьте метод в `ArchitectAgentEnhanced`
4. Напишите тесты
5. Обновите документацию

## 📚 См. также

- [DevOps Module README](../devops/README.md) - аналогичная архитектура
- [Business Analyst Module README](../business_analyst/README.md) - аналогичная архитектура
- [QA Module README](../qa/README.md) - аналогичная архитектура
- [Constitution](../../docs/research/constitution.md) - правила проекта
