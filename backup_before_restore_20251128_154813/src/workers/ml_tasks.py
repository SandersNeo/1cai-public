# [NEXUS IDENTITY] ID: -79685008108269552 | DATE: 2025-11-19

"""
Celery Worker для background обучения моделей и ML задач.
Обрабатывает асинхронные ML задачи: обучение, переобучение, оптимизация гиперпараметров.
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Any, Dict, List

# ML библиотеки
import pandas as pd
# Celery
from celery import Celery
from celery.schedules import crontab

from config import settings
from ml.experiments.mlflow_manager import MLFlowManager
from ml.metrics.collector import AssistantRole, MetricsCollector, MetricType
from ml.training.trainer import ModelTrainer
from src.utils.structured_logging import StructuredLogger

# Локальные импорты (хак для sys.path)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# isort: off

# isort: on

# Настройка Celery
celery_app = Celery(
    "ml_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["workers.ml_tasks"],
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
    # Cron-like периодические задачи
    beat_schedule={
        "retrain-models-daily": {
            "task": "workers.ml_tasks.retrain_all_models",
            "schedule": crontab(hour=2, minute=0),  # Ежедневно в 2:00 UTC
        },
        "update-feature-store": {
            "task": "workers.ml_tasks.update_feature_store",
            "schedule": crontab(minute=0),  # Каждый час
        },
        "cleanup-old-experiments": {
            "task": "workers.ml_tasks.cleanup_old_experiments",
            "schedule": crontab(hour=1, minute=0),  # Ежечасно в 1:00
        },
        "check-model-drift": {
            "task": "workers.ml_tasks.check_model_drift",
            "schedule": crontab(minute=30),  # Каждые 30 минут
        },
        "retrain-underperforming": {
            "task": "workers.ml_tasks.retrain_underperforming_models",
            "schedule": crontab(hour=3, minute=0),  # Ежедневно в 3:00
        },
    },
    beat_schedule_filename="/tmp/celerybeat-schedule",
)

# Логгер
task_logger = StructuredLogger(__name__).logger

# Инициализация сервисов
mlflow_manager = None
metrics_collector = None
model_trainer = None


def init_services():
    """Инициализация сервисов (вызывается при старте worker)"""
    global mlflow_manager, metrics_collector, model_trainer

    if mlflow_manager is None:
        mlflow_manager = MLFlowManager()
        task_logger.info("MLflow Manager инициализирован")

    if metrics_collector is None:
        metrics_collector = MetricsCollector()
        task_logger.info("Metrics Collector инициализирован")

    if model_trainer is None:
        model_trainer = ModelTrainer(
            mlflow_manager=mlflow_manager,
            metrics_collector=metrics_collector,
            celery_app=celery_app,
        )
        task_logger.info("Model Trainer инициализирован")


# Инициализация при загрузке модуля
init_services()


@celery_app.task(bind=True)
def train_model(self, config: Dict[str, Any]):
    """Обучение модели ML"""

    task_logger.info(
        "Начато обучение модели", extra={
            "model_name": config.get("model_name")})

    try:
