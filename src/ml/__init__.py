# [NEXUS IDENTITY] ID: 8141797161139022922 | DATE: 2025-11-19

"""
Система непрерывного улучшения на базе машинного обучения.
Автоматический анализ эффективности AI-ассистентов и улучшение рекомендаций.
"""

from .metrics.collector import MetricsCollector
from .models.predictor import MLPredictor
from .experiments.mlflow_manager import MLFlowManager
from .training.trainer import ModelTrainer
from .ab_testing.tester import ABTestManager

__all__ = [
    "MetricsCollector",
    "MLPredictor",
    "MLFlowManager",
    "ModelTrainer",
    "ABTestManager",
]
