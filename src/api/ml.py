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
metrics_collector: Optional["MetricsCollector"] = None
model_trainer: Optional["ModelTrainer"] = None
mlflow_manager: Optional["MLFlowManager"] = None
ab_test_manager: Optional["ABTestManager"] = None

# Глобальные модели (в продакшене можно использовать кэш)
trained_models: Dict[str, "MLPredictor"] = {}
active_ab_tests: Dict[str, str] = {}  # test_id -> user_id -> model_name


def get_ml_services():
    """Зависимость для получения ML сервисов"""
    global metrics_collector, model_trainer, mlflow_manager, ab_test_manager

    # Lazy imports
    from src.ml.ab_testing.tester import ABTestManager
    from src.ml.experiments.mlflow_manager import MLFlowManager
    from src.ml.metrics.collector import MetricsCollector

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
        # Проверка MLflow
        health_status["services"]["mlflow"] = {
            "status": "healthy",
            "tracking_uri": services["mlflow_manager"].tracking_uri,
        }
    except Exception as e:
        health_status["services"]["mlflow"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"

    try:
        # Проверка метрик
        summary = await services["metrics_collector"].get_performance_summary(
            hours_back=1
        )
        health_status["services"]["metrics"] = {
            "status": "healthy",
            "metrics_collected": len(summary),
        }
    except Exception as e:
        health_status["services"]["metrics"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"

    try:
        # Проверка A/B тестов
        active_tests = len(services["ab_test_manager"].active_tests)
        health_status["services"]["ab_testing"] = {
            "status": "healthy",
            "active_tests": active_tests,
        }
    except Exception as e:
        health_status["services"]["ab_testing"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        health_status["status"] = "degraded"

    return JSONResponse(content=health_status)


# ===== МЕТРИКИ =====


@router.post("/metrics/record")
async def record_metric(
    request: MetricRecordRequest, services=Depends(get_ml_services)
):
    """
    Запись метрики эффективности с валидацией входных данных

    Best practices:
    - Валидация enum значений
    - Sanitization входных данных
    - Улучшенная обработка ошибок
    """
    try:
        # Input validation and sanitization (best practice)
        # Validate metric_type
        try:
            from src.ml.metrics.collector import MetricType
            metric_type = MetricType(request.metric_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid metric_type: {request.metric_type}. Valid types: {[e.value for e in MetricType]}",
            )

        # Validate assistant_role
        try:
            from src.ml.metrics.collector import AssistantRole
            assistant_role = AssistantRole(request.assistant_role.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid assistant_role: {request.assistant_role}. Valid roles: {[e.value for e in AssistantRole]}",
            )

        # Sanitize project_id
        project_id = request.project_id.strip()[:100]  # Limit length
        if not project_id:
            raise HTTPException(status_code=400, detail="Project ID cannot be empty")

        # Запись метрики в зависимости от типа
        if metric_type == MetricType.REQUIREMENT_ANALYSIS_ACCURACY:
            metric_id = await services[
                "metrics_collector"
            ].record_requirement_analysis_accuracy(
                assistant_role=assistant_role,
                predicted_requirements=request.context.get(
                    "predicted_requirements", []
                ),
                actual_requirements=request.context.get("actual_requirements", []),
                project_id=request.project_id,
                context=request.context,
            )
        elif metric_type == MetricType.DIAGRAM_QUALITY_SCORE:
            metric_id = await services[
                "metrics_collector"
            ].record_diagram_quality_score(
                assistant_role=assistant_role,
                generated_diagram=request.context.get("diagram", ""),
                user_feedback=request.feedback_score,
                project_id=request.project_id,
                context=request.context,
            )
        elif metric_type == MetricType.RISK_ASSESSMENT_PRECISION:
            metric_id = await services[
                "metrics_collector"
            ].record_risk_assessment_precision(
                assistant_role=assistant_role,
                predicted_risks=request.context.get("predicted_risks", []),
                actual_risks=request.context.get("actual_risks", []),
                project_id=request.project_id,
                context=request.context,
            )
        elif metric_type == MetricType.RESPONSE_TIME:
            metric_id = await services["metrics_collector"].record_response_time(
                assistant_role=assistant_role,
                response_time=request.value,
                project_id=request.project_id,
                context=request.context,
            )
        elif metric_type == MetricType.USER_SATISFACTION:
            metric_id = await services["metrics_collector"].record_user_satisfaction(
                assistant_role=assistant_role,
                satisfaction_score=request.value,
                project_id=request.project_id,
                user_id=request.user_id,
                context=request.context,
            )
        else:
            raise ValueError(f"Неподдерживаемый тип метрики: {metric_type}")

        return {
            "status": "success",
            "metric_id": metric_id,
            "message": f"Метрика {metric_type.value} успешно записана",
        }

    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except ValueError as e:
        logger.warning(
            "Validation error recording metric",
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
        # Timeout для получения сводки (30 секунд)
        summary = await asyncio.wait_for(
            services["metrics_collector"].get_performance_summary(hours_back),
            timeout=30.0,
        )

        logger.debug(
            "Retrieved metrics summary",
            extra={
                "hours_back": hours_back,
                "summary_keys": (
                    list(summary.keys()) if isinstance(summary, dict) else None
                ),
            },
        )

        return {
            "status": "success",
            "hours_back": hours_back,
            "summary": summary,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except asyncio.TimeoutError:
        logger.error(
            "Timeout getting metrics summary", extra={"hours_back": hours_back}
        )
        raise HTTPException(status_code=504, detail="Timeout getting metrics summary")
    except Exception as e:
        logger.error(
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
        role = AssistantRole(assistant_role.lower())

        # Timeout для получения метрик (30 секунд)
        if metric_type:
            from src.ml.metrics.collector import MetricType
            metric_enum = MetricType(metric_type.lower())
            metrics = await asyncio.wait_for(
                asyncio.to_thread(
                    services["metrics_collector"].db.get_metrics,
                    metric_type=metric_enum,
                    assistant_role=role,
                    hours_back=hours_back,
                ),
                timeout=30.0,
            )
        else:
            # Все метрики для роли
            metrics = {}
            from src.ml.metrics.collector import MetricType
            for m_type in MetricType:
                try:
                    m_data = await asyncio.wait_for(
                        asyncio.to_thread(
                            services["metrics_collector"].db.get_metrics,
                            metric_type=m_type,
                            assistant_role=role,
                            hours_back=hours_back,
                        ),
                        timeout=30.0,
                    )
                    metrics[m_type.value] = m_data
                except Exception as e:
                    logger.debug(
                        "Error getting metric type",
                        extra={
                            "metric_type": m_type.value,
                            "error": str(e),
                            "error_type": type(e).__name__,
                        },
                    )
                    continue

        logger.debug(
            "Retrieved assistant metrics",
            extra={
                "assistant_role": role.value,
                "hours_back": hours_back,
                "metrics_count": len(metrics) if isinstance(metrics, dict) else None,
            },
        )

        return {
            "status": "success",
            "assistant_role": role.value,
            "hours_back": hours_back,
            "metrics": metrics,
        }

    except ValueError as e:
        logger.warning(
            "Invalid enum value in get_assistant_metrics",
            extra={
                "error": str(e),
                "assistant_role": assistant_role,
                "metric_type": metric_type,
            },
        )
        raise HTTPException(
            status_code=400, detail=f"Invalid assistant_role or metric_type: {str(e)}"
        )
    except asyncio.TimeoutError:
        logger.error(
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
        from src.ml.models.predictor import create_model

        # Создание модели
        model = create_model(
            model_type=request.model_type,
            model_name=request.model_name,
            prediction_type=request.prediction_type,
            features=request.features,
            target=request.target,
            model_params=request.hyperparameters,
            mlflow_manager=services["mlflow_manager"],
        )

        # Сохранение в глобальном кэше
        trained_models[request.model_name] = model

        return {
            "status": "success",
            "model_name": request.model_name,
            "model_type": request.model_type,
            "prediction_type": request.prediction_type,
            "features": request.features,
            "message": "Модель успешно создана",
        }

    except Exception as e:
        logger.error(
            "Ошибка создания модели",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "model_name": (
                    request.model_name if hasattr(request, "model_name") else None
                ),
                "model_type": (
                    request.model_type if hasattr(request, "model_type") else None
                ),
            },
            exc_info=True,
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/models/train")
async def train_model(
    request: TrainingRequest,
    background_tasks: BackgroundTasks,
    services=Depends(get_ml_services),
):
    """Обучение модели"""
    try:
        # Создание training job
        import pandas as pd
        from src.ml.training.trainer import TrainingType

        training_data_df = pd.DataFrame(request.training_data)

        training_type_enum = TrainingType(request.training_type.lower())

        job_id = services["model_trainer"].create_training_job(
            model_name=request.model_name,
            model_type=request.model_type,
            features=request.features,
            target=request.target,
            training_data=training_data_df,
            training_type=training_type_enum,
            hyperparameters=request.hyperparameters,
            preprocessing_config=request.preprocessing_config,
        )

        return {
            "status": "submitted",
            "job_id": job_id,
            "message": "Задача обучения поставлена в очередь",
        }

    except Exception as e:
        logger.error(
            "Ошибка обучения модели",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "model_name": (
                    request.model_name if hasattr(request, "model_name") else None
                ),
                "training_type": (
                    request.training_type if hasattr(request, "training_type") else None
                ),
            },
            exc_info=True,
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/models/{model_name}/predict")
async def predict_model(
    model_name: str, request: PredictionRequest, services=Depends(get_ml_services)
):
    """Предсказание с помощью модели"""
    try:
        # Проверка наличия модели
        if model_name not in trained_models:
            raise ValueError(f"Модель {model_name} не найдена")

        model = trained_models[model_name]

        # Проверка обучения модели
        if not model.is_trained:
            raise ValueError(f"Модель {model_name} не обучена")

        # Подготовка данных для предсказания
        import pandas as pd
        input_df = pd.DataFrame([request.input_data])

        # Предсказание
        predictions = model.predict(input_df)

        # Получение вероятностей для классификации
        probabilities = None
        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(input_df)

        # Объяснение предсказания
        explanation = model.explain_prediction(input_df)

        result = {
            "status": "success",
            "model_name": model_name,
            "predictions": (
                predictions.tolist() if hasattr(predictions, "tolist") else predictions
            ),
            "explanation": explanation,
        }

        if probabilities is not None:
            result["probabilities"] = probabilities.tolist()

        return result

    except Exception as e:
        logger.error(
            "Ошибка предсказания модели",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "model_name": model_name,
            },
            exc_info=True,
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/models")
async def list_models():
    """Список всех доступных моделей"""
    models_info = []

    for model_name, model in trained_models.items():
        info = {
            "model_name": model_name,
            "prediction_type": model.prediction_type,
            "features": model.features,
            "target": model.target,
            "is_trained": model.is_trained,
            "config": model.config,
        }

        # Добавление важности признаков если доступно
        importance = model.get_feature_importance()
        if importance:
            info["feature_importance"] = importance

        models_info.append(info)

    return {"status": "success", "models": models_info, "total_count": len(models_info)}


# ===== A/B ТЕСТИРОВАНИЕ =====


@router.post("/ab-tests/create")
@limiter.limit("3/minute")  # Rate limit: 3 AB test creations per minute
async def create_ab_test(
    request: ABTestCreateRequest, services=Depends(get_ml_services)
):
    """Создание A/B теста"""
    try:
        # Проверка наличия моделей
        if request.control_model_name not in trained_models:
            raise ValueError(
                f"Контрольная модель {request.control_model_name} не найдена"
            )

        if request.treatment_model_name not in trained_models:
            raise ValueError(
                f"Treatment модель {request.treatment_model_name} не найдена"
            )

        control_model = trained_models[request.control_model_name]
        treatment_model = trained_models[request.treatment_model_name]

        # Создание конфигурации A/B теста
        from src.ml.ab_testing.tester import ABTestConfig, TestType

        config = ABTestConfig(
            test_name=request.test_name,
            description=request.description,
            test_type=TestType(request.test_type.lower()),
            control_model=control_model,
            treatment_model=treatment_model,
            traffic_split=request.traffic_split,
            primary_metric=request.primary_metric,
            success_criteria=request.success_criteria,
            duration_days=request.duration_days,
            min_sample_size=request.min_sample_size,
            significance_level=request.significance_level,
        )

        # Создание теста
        test_id = services["ab_test_manager"].create_ab_test(config)

        return {
            "status": "success",
            "test_id": test_id,
            "test_name": request.test_name,
            "message": "A/B тест успешно создан",
        }

    except Exception as e:
        logger.error(
            "Ошибка создания A/B теста",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "test_name": (
                    request.test_name if hasattr(request, "test_name") else None
                ),
            },
            exc_info=True,
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/ab-tests/{test_id}/predict")
async def ab_test_prediction(
    test_id: str, request: ABTestPredictionRequest, services=Depends(get_ml_services)
):
    """Предсказание в A/B тесте"""
    try:
        # Назначение модели пользователю
        assignment = services["ab_test_manager"].assign_model_to_user(
            test_id=test_id, user_id=request.user_id, session_id=request.session_id
        )

        model = assignment["model"]
        group = assignment["group"]

        # Выполнение предсказания
        input_df = pd.DataFrame([request.input_data])
        predictions = model.predict(input_df)

        # Логирование результата
        services["ab_test_manager"].log_prediction_result(
            test_id=test_id,
            session_id=request.session_id,
            predicted_value=(
                float(predictions[0])
                if hasattr(predictions, "__getitem__")
                else predictions
            ),
        )

        return {
            "status": "success",
            "test_id": test_id,
            "group": group,
            "model_name": assignment["model_name"],
            "prediction": (
                predictions.tolist() if hasattr(predictions, "tolist") else predictions
            ),
        }

    except Exception as e:
        logger.error(
            "Ошибка предсказания A/B теста",
            extra={"error": str(e), "error_type": type(e).__name__, "test_id": test_id},
            exc_info=True,
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/ab-tests/{test_id}/results")
async def get_ab_test_results(test_id: str, services=Depends(get_ml_services)):
    """Получение результатов A/B теста"""
    try:
        # Анализ результатов
        result = services["ab_test_manager"].analyze_test_results(test_id)
        summary = services["ab_test_manager"].get_test_summary(test_id)

        return {
            "status": "success",
            "test_id": test_id,
            "summary": summary,
            "analysis": {
                "control_metric": result.control_metric,
                "treatment_metric": result.treatment_metric,
                "improvement_percent": result.improvement,
                "p_value": result.p_value,
                "confidence_interval": result.confidence_interval,
                "is_significant": result.is_significant,
                "power": result.power,
            },
        }

    except Exception as e:
        logger.error(
            "Ошибка получения результатов A/B теста",
            extra={"error": str(e), "error_type": type(e).__name__, "test_id": test_id},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ab-tests/{test_id}/promote-winner")
async def promote_winning_model(test_id: str, services=Depends(get_ml_services)):
    """Продвижение выигрышной модели"""
    try:
        winning_model = services["ab_test_manager"].promote_winning_model(test_id)

        return {
            "status": "success",
            "test_id": test_id,
            "winning_model": winning_model.model_name,
            "message": "Выигрышная модель продвинута в продакшен",
        }

    except Exception as e:
        logger.error(
            "Ошибка продвижения модели",
            extra={"error": str(e), "error_type": type(e).__name__, "test_id": test_id},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ab-tests")
async def list_ab_tests(services=Depends(get_ml_services)):
    """Список всех A/B тестов"""
    tests_info = []

    for test_id, config in services["ab_test_manager"].active_tests.items():
        summary = services["ab_test_manager"].get_test_summary(test_id)
        tests_info.append(summary)

    return {"status": "success", "tests": tests_info, "total_count": len(tests_info)}


# ===== ИНТЕГРАЦИЯ С AI АССИСТЕНТАМИ =====


@router.post("/assistants/enhance-analysis")
async def enhance_assistant_analysis(
    request: Dict[str, Any], services=Depends(get_ml_services)
):
    """Улучшение анализа AI ассистента с помощью ML"""
    try:
        assistant_role = request.get("assistant_role")
        analysis_type = request.get("analysis_type")
        input_data = request.get("input_data")

        # Выбор модели в зависимости от типа анализа и роли ассистента
        model_name = f"{assistant_role}_{analysis_type}_predictor"

        if model_name in trained_models:
            model = trained_models[model_name]

            # Повышение качества анализа на основе исторических данных
            if model.is_trained:
                input_df = pd.DataFrame([input_data])
                predictions = model.predict(input_df)

                return {
                    "status": "success",
                    "enhanced_analysis": {
                        "ml_predictions": (
                            predictions.tolist()
                            if hasattr(predictions, "tolist")
                            else predictions
                        ),
                        "model_used": model_name,
                        "confidence": 0.85,  # Можно вычислить из модели
                    },
                }

        return {
            "status": "no_enhancement",
            "message": "ML модель для данного типа анализа не найдена или не обучена",
        }

    except Exception as e:
        logger.error(
            "Ошибка улучшения анализа",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "assistant_role": (
                    assistant_role if "assistant_role" in locals() else None
                ),
                "analysis_type": analysis_type if "analysis_type" in locals() else None,
            },
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


# Экспорт router
__all__ = ["router", "ml_api"]

# Экспорт приложения
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(ml_api, host="0.0.0.0", port=8001)
