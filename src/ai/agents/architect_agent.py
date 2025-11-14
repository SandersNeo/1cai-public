"""
Легковесная версия архитекторского агента.

В production-режиме используется `ArchitectAgentExtended`, однако для unit-тестов
нам достаточно стабильного и детерминированного поведения без внешних
зависимостей (Neo4j и др.). Поэтому класс ниже:

1. Пытается использовать расширенную реализацию, если она доступна.
2. Иначе возвращает синтетический анализ на основе простых эвристик.
"""

from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ArchitectAgent:
    """Упрощённый архитектурный агент, совместимый с тестовым окружением."""

    def __init__(self) -> None:
        self._delegate: Optional[Any] = None

        try:
            from src.ai.agents.architect_agent_extended import (
                ArchitectAgentExtended,
            )

            self._delegate = ArchitectAgentExtended()
            logger.debug("ArchitectAgentExtended найден и будет использоваться.")
        except Exception as exc:  # noqa: BLE001
            # В тестах внешние зависимости (Neo4j и т.п.) могут отсутствовать.
            logger.info(
                "ArchitectAgentExtended недоступен (%s). "
                "Используем fallback-реализацию.",
                exc,
            )
            self._delegate = None

    async def analyze_system(self, description: str) -> Dict[str, Any]:
        """
        Выполняет базовый архитектурный анализ.

        Если доступен расширенный агент, делегирует ему работу. В противном
        случае вычисляет набор простых метрик: размеры, сложности, риски.
        """

        if self._delegate and hasattr(self._delegate, "analyze_system"):
            return await self._delegate.analyze_system(description)  # type: ignore[no-any-return]

        cleaned = " ".join(line.strip() for line in description.splitlines() if line.strip())
        word_count = len(cleaned.split())

        modules = max(1, word_count // 20)
        load_factor = min(1.0, word_count / 200.0)
        score = round(10 - load_factor * 3, 2)

        return {
            "analysis": {
                "summary": cleaned or "Описание системы не предоставлено",
                "modules_estimated": modules,
                "scalability_risk": "medium" if load_factor > 0.6 else "low",
                "recommended_patterns": [
                    "modular-monolith",
                    "event-driven" if load_factor > 0.5 else "layered",
                ],
            },
            "architecture": {
                "overall_score": score,
                "metrics": {
                    "complexity_index": round(1 + load_factor * 4, 2),
                    "coupling": round(0.4 + load_factor * 0.3, 2),
                    "cohesion": round(0.7 - load_factor * 0.2, 2),
                },
                "recommendations": [
                    "Задокументировать ключевые модули и их контракты.",
                    "Добавить нагрузочное тестирование критичных участков.",
                    "Внедрить мониторинг очередей и фоновых задач.",
                ],
            },
        }


__all__ = ["ArchitectAgent"]