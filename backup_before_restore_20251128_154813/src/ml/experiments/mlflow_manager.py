# [NEXUS IDENTITY] ID: -3957510110976409550 | DATE: 2025-11-19

"""
MLflow менеджер для экспериментов и трекинга моделей.
Интеграция с MLflow для мониторинга экспериментов и управления моделями.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import mlflow
import mlflow.sklearn
import mlflow.tensorflow
import numpy as np
import pandas as pd
from mlflow.exceptions import MlflowException
from mlflow.tracking import MlflowClient

from src.config import settings
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class MLFlowManager:
    """Менеджер MLflow экспериментов и моделей"""

    def __init__(self, tracking_uri: Optional[str] = None):
        """Инициализация MLflow клиента"""
        self.tracking_uri = tracking_uri or settings.MLFLOW_TRACKING_URI
        self.client = MlflowClient(tracking_uri=self.tracking_uri)

        # Установка tracking URI
        mlflow.set_tracking_uri(self.tracking_uri)

        # Настройка экспериментов
        self._setup_experiments()

        logger.info(
            "MLflow инициализирован", extra={
                "tracking_uri": self.tracking_uri})

    def _setup_experiments(self):
        """Создание и настройка экспериментов"""

        experiments = [
            {
                "name": "requirement_analysis",
                "description": "Модели предсказания сложности требований",
            },
            {
                "name": "risk_assessment",
                "description": "Модели оценки архитектурных рисков",
            },
            {
                "name": "architecture_patterns",
                "description": "Модели выбора архитектурных паттернов",
            },
            {
                "name": "recommendation_quality",
                "description": "Модели оценки качества рекомендаций",
            },
            {"name": "ab_testing", "description": "A/B тестирование моделей"},
        ]

        for exp_config in experiments:
            try:
