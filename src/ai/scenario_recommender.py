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

from src.ai.code_analysis.graph import CodeGraphBackend, NodeKind

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
                from src.ai.code_analysis.graph_query_helper import GraphQueryHelper

                helper = GraphQueryHelper(self.backend)
                found_nodes = await helper.find_nodes_by_query(query, max_results=10)
                graph_nodes = [node.id for node in found_nodes]
            except Exception as e:
                logger.debug("Failed to find graph nodes: %s", e)

        # Анализируем узлы графа для определения типа задачи
        task_type = self._infer_task_type(query, graph_nodes or [])

        # Рекомендуем сценарии на основе типа задачи
        scenarios = self._get_scenarios_by_task_type(task_type)

        for scenario_id, scenario_info in scenarios.items():
            if len(recommendations) >= max_recommendations:
                break

            # Вычисляем релевантность
            relevance_score = self._calculate_relevance(
                query, graph_nodes or [], scenario_info
            )

            if relevance_score > 0.3:  # Порог релевантности
                recommendations.append(
                    {
                        "scenario_id": scenario_id,
                        "scenario_name": scenario_info["name"],
                        "relevance_score": relevance_score,
                        "reason": scenario_info.get("reason", ""),
                        "graph_nodes_matched": self._find_matching_nodes(
                            graph_nodes or [], scenario_info
                        ),
                    }
                )

        # Сортируем по релевантности
        recommendations.sort(key=lambda x: x["relevance_score"], reverse=True)

        # Метрики: отслеживание рекомендаций
        try:
            from src.monitoring.prometheus_metrics import track_scenario_recommendation

            # Определить категорию размера графа
            graph_size = len(graph_nodes) if graph_nodes else 0
            if graph_size < 100:
                graph_size_category = "small"
            elif graph_size < 1000:
                graph_size_category = "medium"
            else:
                graph_size_category = "large"

            # Время выполнения
            duration = time.time() - start_time
            track_scenario_recommendation(
                duration=duration,
                graph_size_category=graph_size_category,
                recommendations_count=len(recommendations),
                status="success",
            )
        except ImportError:
            pass  # Метрики опциональны

        return recommendations

    def _infer_task_type(self, query: str, graph_nodes: List[str]) -> str:
        """
        Определить тип задачи на основе запроса и узлов графа.

        Returns:
            Тип задачи (ba_dev_qa, code_review, dr_rehearsal, security_audit, etc.)
        """
        query_lower = query.lower()

        # Ключевые слова для разных типов задач
        if any(
            word in query_lower
            for word in ["требование", "requirement", "процесс", "process", "bpmn"]
        ):
            return "ba_dev_qa"

        if any(
            word in query_lower
            for word in ["review", "код", "code", "проверка", "check"]
        ):
            return "code_review"

        if any(
            word in query_lower
            for word in ["dr", "disaster", "recovery", "резерв", "отказ"]
        ):
            return "dr_rehearsal"

        if any(
            word in query_lower
            for word in ["security", "безопасность", "audit", "аудит"]
        ):
            return "security_audit"

        # Анализ узлов графа
        if graph_nodes:
            # Если есть узлы с тестами, возможно нужен QA сценарий
            if any("test" in node.lower() for node in graph_nodes):
                return "ba_dev_qa"

            # Если есть узлы с модулями, возможно нужен code review
            if any("module" in node.lower() for node in graph_nodes):
                return "code_review"

        return "ba_dev_qa"  # По умолчанию

    def _get_scenarios_by_task_type(self, task_type: str) -> Dict[str, Dict[str, Any]]:
        """Получить сценарии для типа задачи."""
        scenarios = {
            "ba_dev_qa": {
                "name": "BA→Dev→QA Workflow",
                "reason": "Полный цикл разработки от требований до тестирования",
                "keywords": ["requirement", "development", "testing", "bpmn"],
            },
            "code_review": {
                "name": "Code Review",
                "reason": "Проверка кода на безопасность и качество",
                "keywords": ["code", "review", "security", "quality"],
            },
            "dr_rehearsal": {
                "name": "DR Rehearsal",
                "reason": "Проверка готовности к аварийному восстановлению",
                "keywords": ["disaster", "recovery", "resilience", "backup"],
            },
            "security_audit": {
                "name": "Security Audit",
                "reason": "Комплексная проверка безопасности",
                "keywords": ["security", "audit", "vulnerability", "compliance"],
            },
        }

        # Возвращаем сценарии для данного типа задачи
        if task_type in scenarios:
            return {task_type: scenarios[task_type]}

        # Если тип задачи неизвестен, возвращаем все
        return scenarios

    def _calculate_relevance(
        self,
        query: str,
        graph_nodes: List[str],
        scenario_info: Dict[str, Any],
    ) -> float:
        """
        Вычислить релевантность сценария для запроса.

        Returns:
            Оценка релевантности от 0.0 до 1.0
        """
        score = 0.0
        query_lower = query.lower()

        # Проверка ключевых слов в запросе
        keywords = scenario_info.get("keywords", [])
        matched_keywords = sum(1 for keyword in keywords if keyword in query_lower)
        if keywords:
            score += (matched_keywords / len(keywords)) * 0.5

        # Проверка узлов графа (если есть)
        if graph_nodes:
            # Упрощённая проверка: если есть узлы, связанные со сценарием
            # (в реальности нужно проверять связи в графе)
            score += 0.3

        # Базовая релевантность
        score += 0.2

        return min(score, 1.0)

    def _find_matching_nodes(
        self, graph_nodes: List[str], scenario_info: Dict[str, Any]
    ) -> List[str]:
        """Найти узлы графа, релевантные сценарию."""
        # Упрощённая реализация: возвращаем первые несколько узлов
        # В реальности нужно проверять связи в графе
        return graph_nodes[:3] if graph_nodes else []


class ImpactAnalyzer:
    """
    Анализатор влияния изменений через Unified Change Graph.

    Определяет, какие компоненты системы могут быть затронуты
    изменениями в указанных узлах графа.
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

    async def analyze_impact(
        self,
        node_ids: List[str],
        *,
        max_depth: int = 3,
        include_tests: bool = True,
    ) -> Dict[str, Any]:
        """
        Проанализировать влияние изменений в узлах графа.

        Args:
            node_ids: Список ID узлов, которые изменяются
            max_depth: Максимальная глубина поиска зависимостей
            include_tests: Включать тесты в анализ

        Returns:
            Отчёт о влиянии изменений
        """
        start_time = time.time()
        if not self.backend:
            return {
                "affected_nodes": [],
                "affected_tests": [],
                "impact_level": "unknown",
                "recommendations": [],
            }

        affected_nodes: Set[str] = set(node_ids)
        affected_tests: Set[str] = set()

        # Найти все зависимые узлы
        for node_id in node_ids:
            try:
                # Найти узлы, которые зависят от данного узла
                dependent_nodes = await self._find_dependent_nodes(
                    node_id, max_depth=max_depth
                )
                affected_nodes.update(dependent_nodes)

                # Найти тесты, связанные с узлом
                if include_tests:
                    tests = await self._find_related_tests(node_id)
                    affected_tests.update(tests)
            except Exception as e:
                logger.debug("Failed to analyze impact for node %s: %s", node_id, e)

        # Определить уровень влияния
        impact_level = self._determine_impact_level(
            len(affected_nodes), len(affected_tests)
        )

        # Сгенерировать рекомендации
        recommendations = self._generate_recommendations(
            affected_nodes, affected_tests, impact_level
        )

        result = {
            "affected_nodes": list(affected_nodes),
            "affected_tests": list(affected_tests),
            "impact_level": impact_level,
            "recommendations": recommendations,
            "total_affected": len(affected_nodes),
            "total_tests_affected": len(affected_tests),
        }

        # Метрики: отслеживание анализа влияния
        try:
            from src.monitoring.prometheus_metrics import track_impact_analysis

            duration = time.time() - start_time
            track_impact_analysis(
                duration=duration,
                max_depth=max_depth,
                include_tests=include_tests,
                affected_nodes_count=len(affected_nodes),
                status="success",
            )
        except ImportError:
            pass  # Метрики опциональны

        return result

    async def _find_dependent_nodes(
        self, node_id: str, *, max_depth: int = 3
    ) -> List[str]:
        """Найти узлы, которые зависят от данного узла."""
        if not self.backend:
            return []

        dependent: Set[str] = set()
        visited: Set[str] = {node_id}

        # BFS для поиска зависимых узлов
        queue = [(node_id, 0)]
        while queue:
            current_id, depth = queue.pop(0)
            if depth >= max_depth:
                continue

            try:
                # Найти рёбра, которые идут от текущего узла
                # (в реальности нужно использовать backend.get_edges)
                # Упрощённая версия: возвращаем пустой список
                pass
            except Exception as e:
                logger.debug("Failed to find dependent nodes: %s", e)

        return list(dependent)

    async def _find_related_tests(self, node_id: str) -> List[str]:
        """Найти тесты, связанные с узлом."""
        if not self.backend:
            return []

        try:
            # Найти узлы тестов, связанные с данным узлом
            test_nodes = await self.backend.find_nodes(kind=NodeKind.TEST)
            # Упрощённая версия: возвращаем первые несколько
            return [node.id for node in test_nodes[:5]]
        except Exception as e:
            logger.debug("Failed to find related tests: %s", e)
            return []

    def _determine_impact_level(self, num_nodes: int, num_tests: int) -> str:
        """Определить уровень влияния."""
        total = num_nodes + num_tests

        if total == 0:
            return "none"
        elif total <= 3:
            return "low"
        elif total <= 10:
            return "medium"
        else:
            return "high"

    def _generate_recommendations(
        self,
        affected_nodes: Set[str],
        affected_tests: Set[str],
        impact_level: str,
    ) -> List[str]:
        """Сгенерировать рекомендации на основе анализа влияния."""
        recommendations: List[str] = []

        if impact_level == "high":
            recommendations.append(
                "Высокий уровень влияния: рекомендуется полное тестирование"
            )
            recommendations.append("Рассмотрите возможность поэтапного развёртывания")
        elif impact_level == "medium":
            recommendations.append(
                "Средний уровень влияния: рекомендуется регрессионное тестирование"
            )
        else:
            recommendations.append(
                "Низкий уровень влияния: достаточно базового тестирования"
            )

        if affected_tests:
            recommendations.append(
                f"Затронуто тестов: {len(affected_tests)}. Рекомендуется запустить все затронутые тесты."
            )

        return recommendations
