# [NEXUS IDENTITY] ID: 2572462847296730521 | DATE: 2025-11-19

"""
Легковесная версия архитекторского агента.

В production-режиме используется `ArchitectAgentExtended`, однако для unit-тестов
нам достаточно стабильного и детерминированного поведения без внешних
зависимостей (Neo4j и др.). Поэтому класс ниже:

1. Пытается использовать расширенную реализацию, если она доступна.
2. Иначе возвращает синтетический анализ на основе простых эвристик.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ArchitectAgent:
    """Упрощённый архитектурный агент, совместимый с тестовым окружением."""

    def __init__(self) -> None:
        self._delegate: Optional[Any] = None

        try:
