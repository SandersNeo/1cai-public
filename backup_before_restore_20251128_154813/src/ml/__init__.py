# [NEXUS IDENTITY] ID: 8141797161139022922 | DATE: 2025-11-19

"""
Система непрерывного улучшения на базе машинного обучения.
Автоматический анализ эффективности AI-ассистентов и улучшение рекомендаций.
"""

from .ab_testing.tester import ABTestManager
from .experiments.mlflow_manager import MLFlowManager
from .metrics.collector import MetricsCollector
from .models.predictor import MLPredictor
from .training.trainer import ModelTrainer

__all__ = [
    "MetricsCollector",
    "MLPredictor",
    "MLFlowManager",
    "ModelTrainer",
    "ABTestManager"]
