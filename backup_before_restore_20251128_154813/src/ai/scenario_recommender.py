# [NEXUS IDENTITY] ID: 139558015001871068 | DATE: 2025-11-19

"""
Scenario Recommender с Unified Change Graph
-------------------------------------------

Автоматическое предложение релевантных сценариев на основе узлов графа
и контекста запроса пользователя.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Set

from src.ai.code_graph import CodeGraphBackend, NodeKind

logger = logging.getLogger(__name__)


class ScenarioRecommender:
    """
    Рекомендатель сценариев на основе Unified Change Graph.

    Анализирует узлы графа, связанные с запросом пользователя,
    и предлагает релевантные сценарии из Scenario Hub.
    """

    def __init__(self, backend: Optional[CodeGraphBackend] = None) -> None:
        """
        Args:
            backend: Backend графа (опционально)
        """
        self.backend = backend

    def set_backend(self, backend: CodeGraphBackend) -> None:
        """Установить backend графа."""
        self.backend = backend

    async def recommend_scenarios(
        self,
        query: str,
        *,
        graph_nodes: Optional[List[str]] = None,
        max_recommendations: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Рекомендовать сценарии на основе запроса и узлов графа.

        Args:
            query: Запрос пользователя
            graph_nodes: Список ID узлов графа (опционально, если уже известны)
            max_recommendations: Максимальное количество рекомендаций

        Returns:
            Список рекомендованных сценариев с обоснованием
        """
        start_time = time.time()
        recommendations: List[Dict[str, Any]] = []

        # Если узлы графа не предоставлены, попробуем найти их
        if not graph_nodes and self.backend:
            try:
