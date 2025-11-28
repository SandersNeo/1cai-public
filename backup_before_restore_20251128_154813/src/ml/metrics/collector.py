# [NEXUS IDENTITY] ID: 2257211876705318003 | DATE: 2025-11-19

"""
Сборщик метрик эффективности AI-ассистентов.
Отслеживает качество анализа требований, генерации диаграмм и оценки рисков.
"""

import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
from sqlalchemy import JSON, Column, DateTime, Float, String, create_engine
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.config import settings
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

# SQLAlchemy модели для хранения метрик
Base = declarative_base()


class MetricType(Enum):
    """Типы метрик эффективности"""

    REQUIREMENT_ANALYSIS_ACCURACY = "requirement_analysis_accuracy"
    DIAGRAM_QUALITY_SCORE = "diagram_quality_score"
    RISK_ASSESSMENT_PRECISION = "risk_assessment_precision"
    RECOMMENDATION_QUALITY = "recommendation_quality"
    RESPONSE_TIME = "response_time"
    USER_SATISFACTION = "user_satisfaction"


class AssistantRole(Enum):
    """Роли AI-ассистентов"""

    ARCHITECT = "architect"
    DEVELOPER = "developer"
    TESTER = "tester"
    PM = "product_manager"


@dataclass
class MetricRecord:
    """Запись о метрике"""

    metric_type: MetricType
    assistant_role: AssistantRole
    value: float
    timestamp: datetime
    project_id: str
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    feedback_score: Optional[float] = None


class MetricEvent(Base):
    """Модель события метрики в БД"""

    __tablename__ = "metric_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_type = Column(String, nullable=False)
    assistant_role = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    project_id = Column(String, nullable=False)
    user_id = Column(String)
    context = Column(JSON)
    feedback_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class MetricsDatabase:
    """БД для хранения метрик"""

    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        Base.metadata.create_all(bind=self.engine)

    def save_metric(self, record: MetricRecord) -> str:
        """Сохранение метрики в БД"""
        session = self.SessionLocal()
        try:
