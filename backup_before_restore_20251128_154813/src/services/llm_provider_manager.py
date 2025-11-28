# [NEXUS IDENTITY] ID: -7923453034864487305 | DATE: 2025-11-19

from __future__ import annotations

"""
Управление конфигурацией провайдеров LLM и fallback-цепочками.

Файл работает поверх `config/llm_providers.yaml` и (опционально) читает состояние
из `output/current_llm_backend.json`.

При отсутствии конфигурации модуль остаётся пассивным, чтобы не ломать текущий
функционал.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)

CONFIG_PATH = Path("config/llm_providers.yaml")
STATE_PATH = Path("output/current_llm_backend.json")


@dataclass
class ProviderConfig:
    name: str
    provider_type: str
    priority: int
    base_url: str
    enabled: bool = True
    status: str = "active"
    metadata: Dict[str, str] = field(default_factory=dict)

    @property
    def is_self_hosted(self) -> bool:
        return self.provider_type in {"self_hosted", "self-hosted"}


class LLMProviderManager:
    """Загрузка конфигураций и предоставление удобного API."""

    def __init__(
        self, config_path: Path = CONFIG_PATH, state_path: Path = STATE_PATH
    ) -> None:
        self.config_path = config_path
        self.state_path = state_path
        self.providers: Dict[str, ProviderConfig] = {}
        self.fallback_matrix: Dict[str, Dict[str, List[str] | str]] = {}
        self.health_config: Dict[str, int] = {}
        self.active_provider: Optional[str] = None

        self._load_config()
        self._load_state()

    def _load_config(self) -> None:
        if not self.config_path.exists():
            logger.debug("LLM provider config not found: %s", self.config_path)
            return

        try:
