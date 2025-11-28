# SQL Optimizer Module

Модуль для оптимизации SQL запросов согласно Clean Architecture.

## 📁 Структура

```
src/modules/sql_optimizer/
├── domain/          # Models + Exceptions (9 models, 4 exceptions) ✅
├── services/        # 2 Business Logic Services ✅
├── repositories/    # OptimizationRepository ✅
└── api/             # SQLOptimizer integration (planned)
```

## 🎯 Возможности

### 1. Query Analyzer ✅
Анализ SQL запросов.

**Features:**
- Query complexity analysis
- Anti-pattern detection
- Missing index detection
- Cost estimation

**Пример:**
```python
from src.modules.sql_optimizer.services import QueryAnalyzer
from src.modules.sql_optimizer.domain.models import SQLQuery

analyzer = QueryAnalyzer()
query = SQLQuery(
    query_text="SELECT * FROM Users WHERE age > 25",
    query_type="SELECT"
)

analysis = await analyzer.analyze_query(query)

print(f"Complexity: {analysis.complexity}")
print(f"Issues: {analysis.issues}")
print(f"Missing indexes: {analysis.missing_indexes}")
print(f"Estimated cost: {analysis.estimated_cost}")
```

### 2. Query Rewriter ✅
Переписывание и оптимизация запросов.

**Features:**
- Query rewriting
- Anti-pattern fixes
- Performance improvements
- Optimization suggestions

**Пример:**
```python
from src.modules.sql_optimizer.services import QueryRewriter

rewriter = QueryRewriter()
optimized = await rewriter.rewrite_query(query, analysis)

print(f"Original: {optimized.original_query}")
print(f"Optimized: {optimized.optimized_query}")
print(f"Improvements: {optimized.improvements}")
print(f"Estimated speedup: {optimized.estimated_speedup}x")
```

### 3. Index Optimizer (Planned)
Оптимизация индексов.

**Features:**
- Index recommendations
- Index impact analysis
- Composite index suggestions
- Index usage statistics

### 4. Performance Predictor (Planned)
Предсказание производительности.

**Features:**
- Execution time prediction
- Resource usage estimation
- Bottleneck detection
- Scaling predictions

## 🏗️ Clean Architecture

### Dependency Rule
```
API Layer (SQLOptimizer)
    ↓
Services Layer (2 services) ✅
    ↓
Repositories Layer (OptimizationRepository) ✅
    ↓
Domain Layer (Models + Exceptions) ✅
```

## 📊 Метрики

- **Files Created:** 9
- **Lines of Code:** ~1,600+
  - Domain: ~400 lines
  - Services: ~1,000 lines
  - Repositories: ~150 lines
  - API Layer: 0 lines (planned)
- **Production Ready:** 75%

## 📝 Domain Models

### Query Models
- `SQLQuery` - SQL запрос
- `QueryAnalysis` - Анализ запроса
- `OptimizedQuery` - Оптимизированный запрос

### Optimization Models
- `IndexRecommendation` - Рекомендация по индексу
- `PerformancePrediction` - Предсказание производительности
- `OptimizationResult` - Результат оптимизации

### Enums
- `QueryComplexity` - SIMPLE, MODERATE, COMPLEX, VERY_COMPLEX
- `OptimizationImpact` - HIGH, MEDIUM, LOW
- `IndexType` - BTREE, HASH, FULLTEXT, CLUSTERED

## 📚 См. также

- [Tech Log Analyzer Module README](../tech_log/README.md)
- [RAS Monitor Module README](../ras_monitor/README.md)
- [Constitution](../../docs/research/constitution.md)
