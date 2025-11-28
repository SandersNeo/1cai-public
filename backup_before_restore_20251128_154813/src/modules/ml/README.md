# ML Module

# ML Module

## Overview

Machine Learning Continuous Improvement API - metrics collection, model training, A/B testing.

## Status

⚠️ **Partial Refactoring**: Domain models extracted. Services remain in original file due to complexity (978 lines, multiple interdependent services).

## Architecture

- **Domain Layer**: ✅ `domain/models.py` - Complete Pydantic models
- **Services Layer**: ⚠️ Remains in `src/api/ml.py` (MetricsCollector, ModelTrainer, ABTestManager, MLFlowManager)
- **API Layer**: ⚠️ Remains in `src/api/ml.py` (30+ endpoints)

## Features

- **Metrics Collection**: Performance tracking for all AI assistants
- **Model Training**: Automated ML model training with MLflow versioning
- **A/B Testing**: Statistical testing framework with traffic splitting
- **MLflow Integration**: Experiment tracking and model registry
- **Predictions**: Real-time model inference with explanations
- **Health Monitoring**: Service health checks

## Endpoints

- `/api/v1/ml/metrics/*` - Metrics collection and retrieval
- `/api/v1/ml/models/*` - Model management (create, train, predict, list)
- `/api/v1/ml/ab-tests/*` - A/B testing (create, predict, analyze)
- `/api/v1/ml/health` - Health check

## Usage

```python
from src.modules.ml import router
app.include_router(router)
```

## Migration Plan

Future refactoring will extract to dedicated service files:

1. `services/metrics_service.py` - MetricsCollector
2. `services/training_service.py` - ModelTrainer
3. `services/ab_test_service.py` - ABTestManager
4. `services/mlflow_service.py` - MLFlowManager
5. `api/routes.py` - All FastAPI routes

**Reason for Partial Migration**: The ML module has 978 lines with complex interdependencies between 4 major services and 30+ endpoints. Full extraction requires careful dependency management and testing.
