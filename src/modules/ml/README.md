# ML Module

## Overview

Machine Learning Continuous Improvement API - metrics collection, model training, A/B testing.

## Status

✅ **Refactored**: Clean Architecture implementation.
- **Domain**: `domain/models.py`
- **Services**: `services/` (Metrics, Training, ABTest, MLFlow)
- **API**: `api/routes.py`

## Architecture

The module follows Clean Architecture principles:

```
src/modules/ml/
├── domain/
│   └── models.py          # Pydantic models
├── services/
│   ├── metrics_service.py # Metrics collection facade
│   ├── training_service.py# Model training facade
│   ├── ab_test_service.py # A/B testing facade
│   └── mlflow_service.py  # MLflow integration facade
├── api/
│   ├── routes.py          # FastAPI endpoints
│   └── dependencies.py    # Dependency injection
└── tests/                 # Tests
```

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
