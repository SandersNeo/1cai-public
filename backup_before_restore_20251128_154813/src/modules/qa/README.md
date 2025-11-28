# QA Engineer Module

Модуль для QA Engineer операций согласно Clean Architecture.

## 📁 Структура

```
src/modules/qa/
├── domain/          # Models + Exceptions (8 models, 3 exceptions)
├── services/        # 2 Business Logic Services
├── repositories/    # TestTemplatesRepository
└── api/             # QAEngineerAgentEnhanced integration
```

## 🎯 Возможности

### 1. Smart Test Generator
AI-powered генерация тестов для BSL функций.

**Features:**
- AI test generation для BSL кода
- YAxUnit test generation
- Vanessa BDD scenario generation
- Edge case detection
- Parameter extraction
- Complexity calculation

**Пример:**
```python
from src.modules.qa.services import SmartTestGenerator

generator = SmartTestGenerator()
result = await generator.generate_tests_for_function(
    function_code="""
    Функция РассчитатьСумму(Сумма1, Сумма2)
        Возврат Сумма1 + Сумма2;
    КонецФункции
    """,
    function_name="РассчитатьСумму"
)

print(f"Positive tests: {len(result.positive_tests)}")
print(f"Negative tests: {len(result.negative_tests)}")
print(f"Edge cases: {len(result.edge_case_tests)}")
print(f"Coverage estimate: {result.coverage_estimate}")
print(f"Complexity: {result.complexity}")
```

### 2. Test Coverage Analyzer
Анализ покрытия тестами с интеграцией SonarQube/Vanessa.

**Features:**
- Coverage analysis
- SonarQube integration (optional)
- Vanessa integration (optional)
- Coverage grading (A-F)
- Recommendations generation

**Пример:**
```python
from src.modules.qa.services import TestCoverageAnalyzer

analyzer = TestCoverageAnalyzer()
report = await analyzer.analyze_coverage(
    config_name="УправлениеТорговлей",
    test_results=None  # Optional: результаты от Vanessa
)

print(f"Total coverage: {report.total_coverage}%")
print(f"Grade: {report.grade}")
print(f"Recommendations: {report.recommendations}")
```

## 🔌 API Layer Integration

### QAEngineerAgentEnhanced

**Новые методы:**
```python
from src.ai.agents.qa_engineer_agent_enhanced import (
    QAEngineerAgentEnhanced
)

agent = QAEngineerAgentEnhanced()

# Test generation
result = await agent.generate_tests_enhanced(
    function_code="...",
    function_name="РассчитатьСумму"
)

# Coverage analysis
report = await agent.analyze_coverage_enhanced(
    config_name="УправлениеТорговлей"
)
```

**Dependency Injection:**
```python
from src.modules.qa.services import SmartTestGenerator

custom_generator = SmartTestGenerator()
agent = QAEngineerAgentEnhanced(
    test_generator=custom_generator
)
```

## 🏗️ Clean Architecture

### Dependency Rule
```
API Layer (QAEngineerAgentEnhanced)
    ↓
Services Layer (2 services)
    ↓
Repositories Layer (TestTemplatesRepository)
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
- **Lines of Code:** ~1,500+
  - Domain: ~250 lines
  - Services: ~800 lines
  - Repositories: ~100 lines
  - API Layer: ~50 lines (integration)
- **Production Ready:** 75%

## 🔄 Migration Guide

### From qa_engineer_agent_extended.py

**Old (extended):**
```python
from src.ai.agents.qa_engineer_agent_extended import (
    SmartTestGenerator
)

generator = SmartTestGenerator()
result = await generator.generate_tests_for_function(code, name)
```

**New (enhanced with Clean Architecture):**
```python
from src.ai.agents.qa_engineer_agent_enhanced import (
    QAEngineerAgentEnhanced
)

agent = QAEngineerAgentEnhanced()
result = await agent.generate_tests_enhanced(code, name)
# Returns TestGenerationResult (Pydantic model)
```

**Backward Compatibility:**
- Legacy методы сохранены (generate_vanessa_tests, etc.)
- Новые методы с суффиксом `_enhanced`

## 📝 Test Templates

### YAxUnit Template
```bsl
Процедура {test_name}() Экспорт
    
    // Arrange (подготовка)
    {arrange_code}
    
    // Act (действие)
    {act_code}
    
    // Assert (проверка через YAxUnit)
    {assert_code}
    
КонецПроцедуры
```

### Vanessa BDD Template
```gherkin
# language: ru

Функционал: {feature_name}
    Как {actor}
    Я хочу {action}
    Чтобы {business_value}

Сценарий: {scenario_name}
    Когда {when_step}
    Тогда {then_step}
```

## 🐛 Known Issues

- SonarQube integration - stub (requires configuration)
- Vanessa integration - stub (requires configuration)
- Qwen3-Coder integration - optional (for AI generation)

## 🤝 Contributing

При добавлении новых функций:
1. Создайте domain model в `domain/models.py`
2. Реализуйте service в `services/`
3. Добавьте метод в `QAEngineerAgentEnhanced`
4. Напишите тесты
5. Обновите документацию

## 📚 См. также

- [DevOps Module README](../devops/README.md) - аналогичная архитектура
- [Business Analyst Module README](../business_analyst/README.md) - аналогичная архитектура
- [Constitution](../../docs/research/constitution.md) - правила проекта
