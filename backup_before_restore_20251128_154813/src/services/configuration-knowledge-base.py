# [NEXUS IDENTITY] ID: 3177793995073984147 | DATE: 2025-11-19

"""
Configuration Knowledge Base Service
База знаний по типовым конфигурациям 1С
Версия: 1.0.0
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class ConfigurationKnowledgeBase:
    """База знаний по типовым конфигурациям 1С"""

    # Поддерживаемые конфигурации
    SUPPORTED_CONFIGURATIONS = ["erp", "ut", "zup", "buh", "holding"]

    # Маппинг названий
    CONFIG_NAME_MAP = {
        "erp": "ERP Управление предприятием 2",
        "ut": "Управление торговлей",
        "zup": "Зарплата и управление персоналом",
        "buh": "Бухгалтерия предприятия",
        "holding": "Управление холдингом",
    }

    def __init__(self, knowledge_base_path: Optional[str] = None):
        """
        Инициализация базы знаний

        Args:
            knowledge_base_path: Путь к директории с базой знаний
        """
        if knowledge_base_path:
            self.kb_path = Path(knowledge_base_path)
        else:
            # По умолчанию: ./knowledge_base или из env
            default_path = os.getenv("KNOWLEDGE_BASE_PATH", "./knowledge_base")
            self.kb_path = Path(default_path)

        self.kb_path.mkdir(parents=True, exist_ok=True)

        # Кэш загруженных знаний
        self._cache: Dict[str, Dict[str, Any]] = {}

        # Загрузка существующих знаний
        self._load_knowledge_base()

    def _load_knowledge_base(self):
        """Загрузка базы знаний из файлов"""
        for config in self.SUPPORTED_CONFIGURATIONS:
            config_file = self.kb_path / f"{config}.json"

            if config_file.exists():
                try:
