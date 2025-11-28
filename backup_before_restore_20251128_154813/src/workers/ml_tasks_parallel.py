# [NEXUS IDENTITY] ID: -14388066513942874 | DATE: 2025-11-19

"""
Celery Worker для параллельного обучения ML моделей
Использует Celery Groups для одновременного обучения нескольких моделей

Улучшения по сравнению с ml_tasks.py:
- Параллельное обучение вместо последовательного
- Экономия времени: 75 мин → 15 мин (-80%)
- Chord для цепочки задач: train → evaluate → cleanup

Дата: 2025-11-06
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
# ML библиотеки
import pandas as pd
# Celery
from celery import Celery, chord, group
from celery.schedules import crontab
from celery.utils.log import get_task_logger

from config import settings
from ml.experiments.mlflow_manager import MLFlowManager
from ml.metrics.collector import MetricsCollector
from ml.training.trainer import ModelTrainer

# Локальные импорты
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# isort: off

# isort: on

# Настройка Celery
celery_app = Celery(
    "ml_worker_parallel",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Конфигурация Celery
celery_app.conf.update(
    # Временные зоны
    timezone="UTC",
    enable_utc=True,
    # Сериализация
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # Времена выполнения
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 минут
    task_soft_time_limit=25 * 60,  # 25 минут
    # Ретрай задач
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Мониторинг
    worker_send_task_events=True,
    task_send_sent_event=True,
    # ОБНОВЛЕННОЕ РАСПИСАНИЕ с параллелизмом
    beat_schedule={
        # Главная задача: параллельное обучение всех моделей
        "retrain-models-parallel-daily": {
            "task": "workers.ml_tasks_parallel.retrain_all_models_parallel",
            "schedule": crontab(hour=2, minute=0),  # Ежедневно в 2:00 UTC
            "options": {"queue": "ml_heavy"},
        },
        # Обновление feature store (остается как было)
        "update-feature-store-hourly": {
            "task": "workers.ml_tasks_parallel.update_feature_store",
            "schedule": crontab(minute=0),  # Каждый час
            "options": {"queue": "ml_light"},
        },
        # Проверка model drift
        "check-model-drift-halfhourly": {
            "task": "workers.ml_tasks_parallel.check_model_drift",
            "schedule": crontab(minute="*/30"),  # Каждые 30 минут
            "options": {"queue": "ml_light"},
        },
    },
    beat_schedule_filename="/tmp/celerybeat-schedule-parallel",
)

# Логгер
task_logger = get_task_logger(__name__)

# Инициализация сервисов
mlflow_manager = None
metrics_collector = None
model_trainer = None


def init_services():
    """Инициализация сервисов (вызывается при старте worker)"""
    global mlflow_manager, metrics_collector, model_trainer

    if mlflow_manager is None:
        mlflow_manager = MLFlowManager()
        metrics_collector = MetricsCollector()
        model_trainer = ModelTrainer(mlflow_manager=mlflow_manager)

        task_logger.info("ML services initialized")


# ============================================================================
# PARALLEL TRAINING TASKS
# ============================================================================


@celery_app.task(
    name="workers.ml_tasks_parallel.retrain_single_model",
    bind=True,
    max_retries=2,
    default_retry_delay=300,  # 5 минут
)
def retrain_single_model(self, model_type: str) -> Dict[str, Any]:
    """
    Обучение одной модели (для параллельного выполнения)

    Args:
        model_type: Тип модели ('classification', 'regression', etc.)

    Returns:
        Dict с результатами обучения
    """
    init_services()

    task_logger.info(
        "Starting training for model", extra={
            "model_type": model_type})
    start_time = datetime.utcnow()

    try:
