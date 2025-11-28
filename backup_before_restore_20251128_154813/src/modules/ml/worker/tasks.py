import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from celery import Celery, chord, group
from celery.schedules import crontab
from celery.utils.log import get_task_logger

from src.config import settings
from src.ml.experiments.mlflow_manager import MLFlowManager
from src.ml.metrics.collector import MetricsCollector
from src.ml.training.trainer import ModelTrainer

# Adjust path to include src
sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__))))))


# Celery Configuration
celery_app = Celery(
    "ml_module_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    timezone="UTC",
    enable_utc=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_send_task_events=True,
    task_send_sent_event=True,
    beat_schedule={
        "retrain-models-parallel-daily": {
            "task": "src.modules.ml.worker.tasks.retrain_all_models_parallel",
            "schedule": crontab(hour=2, minute=0),
            "options": {"queue": "ml_heavy"},
        },
        "update-feature-store-hourly": {
            "task": "src.modules.ml.worker.tasks.update_feature_store",
            "schedule": crontab(minute=0),
            "options": {"queue": "ml_light"},
        },
        "check-model-drift-halfhourly": {
            "task": "src.modules.ml.worker.tasks.check_model_drift",
            "schedule": crontab(minute="*/30"),
            "options": {"queue": "ml_light"},
        },
    },
)

task_logger = get_task_logger(__name__)

# Service Initialization
mlflow_manager = None
metrics_collector = None
model_trainer = None


def init_services():
    """Initialize ML services"""
    global mlflow_manager, metrics_collector, model_trainer

    if mlflow_manager is None:
        mlflow_manager = MLFlowManager()
        metrics_collector = MetricsCollector()
        model_trainer = ModelTrainer(mlflow_manager=mlflow_manager)
        task_logger.info("ML Module services initialized")


# ============================================================================
# TASKS
# ============================================================================


@celery_app.task(
    name="src.modules.ml.worker.tasks.retrain_single_model",
    bind=True,
    max_retries=2,
    default_retry_delay=300,
)
def retrain_single_model(self, model_type: str) -> Dict[str, Any]:
    """Train a single model"""
    init_services()
    task_logger.info("Starting training", extra={"model_type": model_type})
    start_time = datetime.utcnow()

    try:
