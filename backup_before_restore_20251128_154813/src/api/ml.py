# [NEXUS IDENTITY] ID: 6220636123436690875 | DATE: 2025-11-19

"""
API эндпоинты для ML системы непрерывного улучшения.
Версия: 2.1.0

Улучшения:
- Structured logging
- Улучшена обработка ошибок
- Input validation
- Timeout handling
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import APIRouter, BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.config import settings
from src.middleware.rate_limiter import limiter
from src.ml.ab_testing.tester import ABTestConfig, ABTestManager, TestType
from src.ml.experiments.mlflow_manager import MLFlowManager
from src.ml.metrics.collector import (AssistantRole, MetricsCollector,
                                      MetricType)
from src.ml.models.predictor import MLPredictor, create_model
from src.ml.training.trainer import ModelTrainer, TrainingType
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

# Создаем router для ML API
router = APIRouter(prefix="/api/v1/ml", tags=["Machine Learning"])


# Pydantic модели для API
class MetricRecordRequest(BaseModel):
    """Запрос для записи метрики"""

    metric_type: str
    assistant_role: str
    value: float
    project_id: str = Field(..., description="ID проекта")
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    feedback_score: Optional[float] = None


class ModelCreateRequest(BaseModel):
    """Запрос для создания модели"""

    model_name: str
    model_type: str
    prediction_type: str
    features: List[str]
    target: Optional[str] = None
    hyperparameters: Optional[Dict[str, Any]] = None


class TrainingRequest(BaseModel):
    """Запрос для обучения модели"""

    model_name: str
    model_type: str
    features: List[str]
    target: str
    training_data: List[Dict[str, Any]]
    training_type: str = "initial"
    test_size: float = 0.2
    hyperparameters: Optional[Dict[str, Any]] = None
    preprocessing_config: Optional[Dict[str, Any]] = None


class PredictionRequest(BaseModel):
    """Запрос для предсказания"""

    model_name: str
    input_data: Dict[str, Any] = Field(
        ..., description="Входные данные для предсказания"
    )


class ABTestCreateRequest(BaseModel):
    """Запрос для создания A/B теста"""

    test_name: str
    description: str
    test_type: str
    control_model_name: str
    treatment_model_name: str
    traffic_split: float
    primary_metric: str
    success_criteria: Dict[str, float]
    duration_days: int
    min_sample_size: int
    significance_level: float = 0.05


class ABTestPredictionRequest(BaseModel):
    """Запрос для предсказания в A/B тесте"""

    test_id: str
    user_id: str
    session_id: str
    input_data: Dict[str, Any]


# Глобальные экземпляры сервисов
metrics_collector: Optional[MetricsCollector] = None
model_trainer: Optional[ModelTrainer] = None
mlflow_manager: Optional[MLFlowManager] = None
ab_test_manager: Optional[ABTestManager] = None

# Глобальные модели (в продакшене можно использовать кэш)
trained_models: Dict[str, MLPredictor] = {}
active_ab_tests: Dict[str, str] = {}  # test_id -> user_id -> model_name


def get_ml_services():
    """Зависимость для получения ML сервисов"""
    global metrics_collector, model_trainer, mlflow_manager, ab_test_manager

    if metrics_collector is None:
        metrics_collector = MetricsCollector()

    if mlflow_manager is None:
        mlflow_manager = MLFlowManager()

    if ab_test_manager is None:
        ab_test_manager = ABTestManager(
            database_url=settings.DATABASE_URL,
            mlflow_manager=mlflow_manager,
            metrics_collector=metrics_collector,
        )

    return {
        "metrics_collector": metrics_collector,
        "model_trainer": model_trainer,
        "mlflow_manager": mlflow_manager,
        "ab_test_manager": ab_test_manager,
    }


# FastAPI приложение
ml_api = FastAPI(
    title="ML Continuous Improvement API",
    description="API для системы непрерывного улучшения на базе машинного обучения",
    version="1.0.0",
)


@router.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "ML Continuous Improvement API",
        "version": "1.0.0",
        "status": "active",
        "services": [
            "metrics_collection",
            "model_training",
            "ab_testing",
            "predictions",
        ],
    }


@router.get("/health")
async def health_check():
    """Проверка здоровья системы"""
    services = get_ml_services()

    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {},
    }

    try:
            "Validation error recording metric",
            extra = {
                "error": str(e),
                "error_type": type(e).__name__,
                "metric_type": (
                    request.metric_type if hasattr(
                        request, "metric_type") else None
                ),
                "assistant_role": (
                    request.assistant_role
                    if hasattr(request, "assistant_role")
                    else None
                ),
                "project_id": (
                    request.project_id if hasattr(
                        request, "project_id") else None
                ),
            },
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            "Unexpected error recording metric",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "metric_type": (
                    request.metric_type if hasattr(request, "metric_type") else None
                ),
                "assistant_role": (
                    request.assistant_role
                    if hasattr(request, "assistant_role")
                    else None
                ),
                "project_id": (
                    request.project_id if hasattr(request, "project_id") else None
                ),
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="An error occurred while recording metric"
        )


@router.get("/metrics/summary")
async def get_metrics_summary(hours_back: int = 24, services=Depends(get_ml_services)):
    """Получение сводки метрик с input validation и timeout handling"""
    # Input validation
    if (
        not isinstance(hours_back, int) or hours_back < 1 or hours_back > 720
    ):  # Max 30 days
        logger.warning(
            "Invalid hours_back in get_metrics_summary",
            extra={
                "hours_back": hours_back,
                "hours_back_type": type(hours_back).__name__,
            },
        )
        raise HTTPException(
            status_code=400, detail="hours_back must be between 1 and 720"
        )

    try:
            "Error getting metrics summary",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "hours_back": hours_back,
            },
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/{assistant_role}")
async def get_assistant_metrics(
    assistant_role: str,
    metric_type: Optional[str] = None,
    hours_back: int = 24,
    services=Depends(get_ml_services),
):
    """Получение метрик конкретного ассистента с input validation и timeout handling"""
    # Input validation
    if not isinstance(assistant_role, str) or not assistant_role.strip():
        logger.warning(
            "Invalid assistant_role in get_assistant_metrics",
            extra={
                "assistant_role_type": (
                    type(assistant_role).__name__ if assistant_role else None
                )
            },
        )
        raise HTTPException(status_code=400, detail="assistant_role cannot be empty")

    if not isinstance(hours_back, int) or hours_back < 1 or hours_back > 720:
        logger.warning(
            "Invalid hours_back in get_assistant_metrics",
            extra={
                "hours_back": hours_back,
                "hours_back_type": type(hours_back).__name__,
            },
        )
        raise HTTPException(
            status_code=400, detail="hours_back must be between 1 and 720"
        )

    if metric_type is not None:
        if not isinstance(metric_type, str) or not metric_type.strip():
            logger.warning("Invalid metric_type in get_assistant_metrics")
            metric_type = None
        else:
            # Limit metric_type length
            if len(metric_type) > 100:
                metric_type = metric_type[:100]

    try:
            "Timeout getting assistant metrics",
            extra={"assistant_role": assistant_role, "hours_back": hours_back},
        )
        raise HTTPException(status_code=504, detail="Timeout getting assistant metrics")
    except Exception as e:
        logger.error(
            "Error getting assistant metrics",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "assistant_role": assistant_role,
                "hours_back": hours_back,
            },
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


# ===== МОДЕЛИ =====


@router.post("/models/create")
@limiter.limit("5/minute")  # Rate limit: 5 model creations per minute
async def create_model(request: ModelCreateRequest, services=Depends(get_ml_services)):
    """Создание модели ML"""
    try: