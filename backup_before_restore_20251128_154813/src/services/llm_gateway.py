# [NEXUS IDENTITY] ID: 3241570084266474318 | DATE: 2025-11-19

"""
LLM Gateway — центральная точка выбора провайдера с поддержкой fallback-цепочек.

Версия: 2.2.0
Refactored: Enhanced resilience (timeouts, circuit breakers) and security.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

import yaml

from src.ai.intelligent_cache import IntelligentCache
from src.monitoring.prometheus_metrics import (llm_gateway_fallbacks_total,
                                               llm_gateway_latency_seconds,
                                               llm_gateway_requests_total,
                                               llm_provider_health,
                                               llm_provider_latency_ms)
from src.resilience.error_recovery import CircuitBreaker

from .llm_health_monitor import LLMHealthMonitor, ProviderHealthStatus
from .llm_provider_manager import (LLMProviderManager, ProviderConfig,
                                   load_llm_provider_manager)

logger = logging.getLogger(__name__)


@dataclass
class LLMGatewayResponse:
    provider: str
    model: str
    response: str
    metadata: Dict[str, Any]


class LLMGateway:
    """
    LLM шлюз: определяет порядок провайдеров и возвращает структурированный ответ.
    """

    def __init__(
        self,
        manager: Optional[LLMProviderManager] = None,
        enable_cache: bool = True,
        enable_health_monitoring: bool = True,
        enable_circuit_breaker: bool = True,
        client_factory: Optional[Callable[[str], Any]] = None,
    ) -> None:
        self.manager = manager or load_llm_provider_manager()
        self._ensure_manager()
        self.simulation_config = self._load_simulation_config()

        self._clients: Dict[str, Any] = {}
        self._client_factory = client_factory

        self.cache: Optional[IntelligentCache] = None
        if enable_cache:
            try:
