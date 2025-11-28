# [NEXUS IDENTITY] ID: 4853070400390671839 | DATE: 2025-11-19

"""
A/B тестирование для ML моделей.
Позволяет тестировать новые модели в продакшене с минимальными рисками.
"""

import hashlib
import json
import logging
import math
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
# Статистика
from scipy import stats
# База данных для результатов A/B тестов
from sqlalchemy import (JSON, Boolean, Column, DateTime, Float, Integer,
                        String, create_engine)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.infrastructure.logging.structured_logging import StructuredLogger
from src.modules.ml.domain.predictor import MLPredictor
from src.modules.ml.infrastructure.metrics_collector import MetricsCollector
from src.modules.ml.infrastructure.mlflow_manager import MLFlowManager

logger = StructuredLogger(__name__).logger
Base = declarative_base()


class ABTestStatus(Enum):
    """Статус A/B теста"""

    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TestType(Enum):
    """Типы A/B тестов"""

    MODEL_COMPARISON = "model_comparison"
    FEATURE_TEST = "feature_test"
    HYPERPARAMETER_TEST = "hyperparameter_test"
    THRESHOLD_TEST = "threshold_test"


@dataclass
class ABTestConfig:
    """Конфигурация A/B теста"""

    test_name: str
    description: str
    test_type: TestType
    control_model: MLPredictor
    treatment_model: MLPredictor
    traffic_split: float  # 0.0 - 1.0, доля трафика для treatment
    primary_metric: str
    success_criteria: Dict[str, float]
    duration_days: int
    min_sample_size: int
    significance_level: float = 0.05


@dataclass
class ABTestResult:
    """Результат A/B теста"""

    test_id: str
    control_metric: float
    treatment_metric: float
    improvement: float
    p_value: float
    confidence_interval: Tuple[float, float]
    is_significant: bool
    power: float
    sample_size_control: int
    sample_size_treatment: int


class ABTestRecord(Base):
    """Модель записи A/B теста в БД"""

    __tablename__ = "ab_tests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_name = Column(String, nullable=False)
    test_type = Column(String, nullable=False)
    status = Column(String, nullable=False)

    # Конфигурация
    traffic_split = Column(Float, nullable=False)
    primary_metric = Column(String, nullable=False)
    success_criteria = Column(JSON, nullable=False)
    duration_days = Column(Integer, nullable=False)
    min_sample_size = Column(Integer, nullable=False)
    significance_level = Column(Float, nullable=False)

    # Модели
    control_model_id = Column(String, nullable=False)
    treatment_model_id = Column(String, nullable=False)

    # Статистика
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    sample_size_control = Column(Integer, default=0)
    sample_size_treatment = Column(Integer, default=0)

    # Результаты
    control_metric_mean = Column(Float)
    treatment_metric_mean = Column(Float)
    improvement = Column(Float)
    p_value = Column(Float)
    confidence_interval_low = Column(Float)
    confidence_interval_high = Column(Float)
    is_significant = Column(Boolean)
    power = Column(Float)

    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class ABTestSession(Base):
    """Запись сессии A/B теста"""

    __tablename__ = "ab_test_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_id = Column(UUID(as_uuid=True), nullable=False)
    session_id = Column(String, nullable=False)
    user_id = Column(String)
    group = Column(String, nullable=False)  # 'control' или 'treatment'
    assigned_model = Column(String, nullable=False)

    # Результаты
    predicted_value = Column(Float)
    actual_value = Column(Float)
    prediction_error = Column(Float)
    user_feedback = Column(Float)
    response_time = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)


class ABTestingDatabase:
    """БД для A/B тестов"""

    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

    def create_ab_test(self, config: ABTestConfig) -> str:
        """Создание нового A/B теста"""
        session = self.SessionLocal()
        try:
