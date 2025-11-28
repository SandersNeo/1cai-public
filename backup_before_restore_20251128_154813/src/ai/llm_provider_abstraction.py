# [NEXUS IDENTITY] ID: 7512410328672895696 | DATE: 2025-11-19

"""
LLM Provider Abstraction Layer
------------------------------

Унифицированный уровень абстракции для работы с разными LLM провайдерами.
Обеспечивает единый интерфейс для выбора провайдера на основе типа запроса,
рисков, стоимости и latency.

Интегрируется с ToolRegistry для описания доступных моделей.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from src.config import USE_ADAPTIVE_SELECTION

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Типы запросов для выбора провайдера."""

    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    REASONING = "reasoning"
    RUSSIAN_TEXT = "russian_text"
    ENGLISH_TEXT = "english_text"
    ANALYSIS = "analysis"
    GENERAL = "general"


class RiskLevel(Enum):
    """Уровни риска провайдера."""

    LOW = "low"  # Локальные модели, полностью контролируемые
    MEDIUM = "medium"  # Российские провайдеры с compliance
    HIGH = "high"  # Зарубежные провайдеры, возможны регуляторные ограничения


@dataclass
class ModelProfile:
    """
    Профиль модели с метаданными для выбора провайдера.

    Содержит информацию о рисках, стоимости, latency и поддерживаемых типах запросов.
    """

    provider_id: str  # Идентификатор провайдера (kimi, qwen, gigachat, etc.)
    model_name: str  # Название модели
    capabilities: Set[QueryType] = field(
        default_factory=set)  # Поддерживаемые типы запросов
    risk_level: RiskLevel = RiskLevel.MEDIUM  # Уровень риска
    cost_per_1k_tokens: float = 0.0  # Стоимость за 1K токенов (USD)
    avg_latency_ms: int = 1000  # Средняя latency в миллисекундах
    max_tokens: int = 4096  # Максимальное количество токенов
    supports_streaming: bool = False  # Поддержка streaming
    # Соответствие требованиям (152-ФЗ, GDPR, etc.)
    compliance: List[str] = field(default_factory=list)
    description: str = ""  # Описание модели

    def to_dict(self) -> Dict[str, Any]:
        """Конвертировать в словарь для сериализации."""
        return {
            "provider_id": self.provider_id,
            "model_name": self.model_name,
            "capabilities": [cap.value for cap in self.capabilities],
            "risk_level": self.risk_level.value,
            "cost_per_1k_tokens": self.cost_per_1k_tokens,
            "avg_latency_ms": self.avg_latency_ms,
            "max_tokens": self.max_tokens,
            "supports_streaming": self.supports_streaming,
            "compliance": self.compliance,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelProfile":
        """Создать из словаря."""
        return cls(
            provider_id=data["provider_id"],
            model_name=data["model_name"],
            capabilities={QueryType(cap) for cap in data.get("capabilities", [])},
            risk_level=RiskLevel(data.get("risk_level", "medium")),
            cost_per_1k_tokens=data.get("cost_per_1k_tokens", 0.0),
            avg_latency_ms=data.get("avg_latency_ms", 1000),
            max_tokens=data.get("max_tokens", 4096),
            supports_streaming=data.get("supports_streaming", False),
            compliance=data.get("compliance", []),
            description=data.get("description", ""),
        )


class LLMProviderAbstraction:
    """
    Унифицированный уровень абстракции для LLM провайдеров.

    Управляет профилями моделей и выбором провайдера на основе типа запроса,
    рисков, стоимости и latency.

    With optional Nested Learning for adaptive selection.
    """

    def __init__(self) -> None:
        """Инициализация абстракции провайдеров."""
        self.profiles: Dict[str, ModelProfile] = {}
        self._load_default_profiles()

        # Nested Learning integration (optional)
        self._nested = None
        if USE_ADAPTIVE_SELECTION:
            try:
