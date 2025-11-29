# [NEXUS IDENTITY] ID: -1017500679021558599 | DATE: 2025-11-19

"""
Analytics & KPI Toolkit с Unified Change Graph
----------------------------------------------

Расширенная реализация BA-04 с использованием Unified Change Graph
для автоматического построения KPI на основе реальных метрик.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.ai.code_analysis.graph import CodeGraphBackend, EdgeKind, Node, NodeKind

logger = logging.getLogger(__name__)


class KPIGeneratorWithGraph:
    """
    Генератор KPI с использованием Unified Change Graph.

    Автоматически строит KPI на основе реальных метрик из графа:
    - Code coverage (код → тесты)
    - Test coverage (требования → тесты)
    - Incident rate (код → инциденты)
    - Deployment frequency (релизы)
    - Change failure rate (инциденты / изменения)
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

    async def generate_kpis_from_graph(
        self,
        feature_id: Optional[str] = None,
        *,
        include_technical: bool = True,
        include_business: bool = True,
    ) -> Dict[str, Any]:
        """
        Сгенерировать KPI на основе данных из Unified Change Graph.

        Args:
            feature_id: ID фичи/требования (опционально)
            include_technical: Включать технические KPI
            include_business: Включать бизнес KPI

        Returns:
            Словарь с KPI, SQL-запросами и визуализациями
        """
        if not self.backend:
            logger.warning("Graph backend not available, returning template KPIs")
            return self._generate_template_kpis()

        kpis: List[Dict[str, Any]] = []

        # Технические KPI на основе графа
        if include_technical:
            technical_kpis = await self._build_technical_kpis(feature_id)
            kpis.extend(technical_kpis)

        # Бизнес KPI (шаблоны, т.к. требуют внешних данных)
        if include_business:
            business_kpis = self._build_business_kpi_templates(feature_id)
            kpis.extend(business_kpis)

        # SQL-запросы для KPI
        sql_queries = await self._generate_sql_queries(kpis, feature_id)

        # Визуализации
        visualizations = self._generate_visualizations(kpis)

        return {
            "kpis": kpis,
            "sql_queries": sql_queries,
            "visualizations": visualizations,
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def _build_technical_kpis(
        self, feature_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Построить технические KPI на основе графа."""
        kpis: List[Dict[str, Any]] = []

        # 1. Code Coverage KPI
        if feature_id:
            req_node_id = f"ba_requirement:{feature_id}"
            req_node = await self.backend.get_node(req_node_id)
            if req_node:
                # Найти код, реализующий требование
                code_nodes = await self.backend.neighbors(
                    req_node_id,
                    kinds=[EdgeKind.IMPLEMENTS],
                )
                # Найти тесты для кода
                all_test_nodes: List[Node] = []
                for code_node in code_nodes:
                    test_nodes = await self.backend.neighbors(
                        code_node.id,
                        kinds=[EdgeKind.TESTED_BY],
                    )
                    all_test_nodes.extend(test_nodes)

                code_count = len(code_nodes)
                test_count = len(set(node.id for node in all_test_nodes))
                coverage_percent = (
                    int((test_count / code_count) * 100) if code_count > 0 else 0
                )

                kpis.append(
                    {
                        "id": "kpi_code_coverage",
                        "name": "Code Coverage",
                        "description": f"Процент кода, покрытого тестами для фичи {feature_id}",
                        "formula": "(test_count / code_count) * 100",
                        "value": coverage_percent,
                        "target": 80,
                        "unit": "%",
                        "source": "Unified Change Graph",
                        "frequency": "per_release",
                        "category": "technical",
                    }
                )

        # 2. Test Coverage KPI (общий)
        all_requirements = await self._get_all_requirements()
        all_tests = await self._get_all_tests()
        test_coverage = (
            int((len(all_tests) / len(all_requirements)) * 100)
            if len(all_requirements) > 0
            else 0
        )

        kpis.append(
            {
                "id": "kpi_test_coverage",
                "name": "Test Coverage",
                "description": "Процент требований, покрытых тестами",
                "formula": "(test_count / requirement_count) * 100",
                "value": test_coverage,
                "target": 90,
                "unit": "%",
                "source": "Unified Change Graph",
                "frequency": "weekly",
                "category": "technical",
            }
        )

        # 3. Incident Rate KPI
        all_incidents = await self._get_all_incidents()
        all_modules = await self._get_all_modules()
        incident_rate = (
            len(all_incidents) / len(all_modules) if len(all_modules) > 0 else 0
        )

        kpis.append(
            {
                "id": "kpi_incident_rate",
                "name": "Incident Rate",
                "description": "Количество инцидентов на модуль",
                "formula": "incident_count / module_count",
                "value": round(incident_rate, 2),
                "target": 0.1,
                "unit": "incidents/module",
                "source": "Unified Change Graph",
                "frequency": "monthly",
                "category": "technical",
            }
        )

        # 4. Change Failure Rate (DORA metric)
        # Инциденты, связанные с изменениями кода
        change_failure_rate = await self._calculate_change_failure_rate()
        kpis.append(
            {
                "id": "kpi_change_failure_rate",
                "name": "Change Failure Rate",
                "description": "Процент изменений, приводящих к инцидентам (DORA)",
                "formula": "(incidents_from_changes / total_changes) * 100",
                "value": change_failure_rate,
                "target": 15,
                "unit": "%",
                "source": "Unified Change Graph",
                "frequency": "monthly",
                "category": "technical",
            }
        )

        return kpis

    def _build_business_kpi_templates(
        self, feature_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Построить шаблоны бизнес KPI (требуют внешних данных)."""
        kpis: List[Dict[str, Any]] = [
            {
                "id": "kpi_revenue_impact",
                "name": "Revenue Impact",
                "description": "Влияние фичи на выручку",
                "formula": "SUM(revenue) WHERE feature_id = ?",
                "value": None,
                "target": None,
                "unit": "currency",
                "source": "Business Data (requires external DB)",
                "frequency": "monthly",
                "category": "business",
            },
            {
                "id": "kpi_user_adoption",
                "name": "User Adoption",
                "description": "Процент пользователей, использующих фичу",
                "formula": "(active_users / total_users) * 100",
                "value": None,
                "target": 50,
                "unit": "%",
                "source": "Analytics Platform (requires external DB)",
                "frequency": "weekly",
                "category": "business",
            },
            {
                "id": "kpi_time_to_value",
                "name": "Time to Value",
                "description": "Время от релиза до первого использования",
                "formula": "AVG(first_use_timestamp - release_timestamp)",
                "value": None,
                "target": "7 days",
                "unit": "days",
                "source": "Analytics Platform (requires external DB)",
                "frequency": "per_release",
                "category": "business",
            },
        ]

        return kpis

    async def _generate_sql_queries(
        self, kpis: List[Dict[str, Any]], feature_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Сгенерировать SQL-запросы для KPI."""
        queries: List[Dict[str, Any]] = []

        for kpi in kpis:
            if kpi.get("category") == "technical" and self.backend:
                # SQL для технических KPI на основе графа
                if kpi["id"] == "kpi_code_coverage":
                    queries.append(
                        {
                            "kpi_id": kpi["id"],
                            "query": """
-- Code Coverage для фичи
SELECT
    COUNT(DISTINCT code_nodes.id) as code_count,
    COUNT(DISTINCT test_nodes.id) as test_count,
    ROUND((COUNT(DISTINCT test_nodes.id)::numeric /
           NULLIF(COUNT(DISTINCT code_nodes.id), 0)) * 100, 2) as coverage_percent
FROM graph_nodes code_nodes
LEFT JOIN graph_edges code_to_test
    ON code_nodes.id = code_to_test.source_id
    AND code_to_test.kind = 'TESTED_BY'
LEFT JOIN graph_nodes test_nodes
    ON code_to_test.target_id = test_nodes.id
WHERE code_nodes.kind = 'MODULE'
    AND code_nodes.id IN (
        SELECT target_id FROM graph_edges
        WHERE source_id = 'ba_requirement:{}'
        AND kind = 'IMPLEMENTS'
    )
""".format(
                                feature_id or "?"
                            ),
                            "database": "postgresql",
                            "description": f"SQL для {kpi['name']}",
                        }
                    )
                elif kpi["id"] == "kpi_incident_rate":
                    queries.append(
                        {
                            "kpi_id": kpi["id"],
                            "query": """
-- Incident Rate
SELECT
    COUNT(DISTINCT modules.id) as module_count,
    COUNT(DISTINCT incidents.id) as incident_count,
    ROUND(COUNT(DISTINCT incidents.id)::numeric /
          NULLIF(COUNT(DISTINCT modules.id), 0), 2) as incident_rate
FROM graph_nodes modules
LEFT JOIN graph_edges module_to_incident
    ON modules.id = module_to_incident.source_id
    AND module_to_incident.kind = 'TRIGGERS_INCIDENT'
LEFT JOIN graph_nodes incidents
    ON module_to_incident.target_id = incidents.id
WHERE modules.kind = 'MODULE'
""",
                            "database": "postgresql",
                            "description": f"SQL для {kpi['name']}",
                        }
                    )

            elif kpi.get("category") == "business":
                # SQL шаблоны для бизнес KPI
                if kpi["id"] == "kpi_revenue_impact":
                    queries.append(
                        {
                            "kpi_id": kpi["id"],
                            "query": """
-- Revenue Impact (требует внешней таблицы revenue)
SELECT
    feature_id,
    SUM(revenue) as total_revenue,
    COUNT(DISTINCT user_id) as active_users,
    AVG(revenue_per_user) as avg_revenue_per_user
FROM revenue_events
WHERE feature_id = :feature_id
    AND event_date >= :start_date
    AND event_date <= :end_date
GROUP BY feature_id
""",
                            "database": "postgresql",
                            "description": f"SQL шаблон для {kpi['name']}",
                            "note": "Требует внешнюю таблицу revenue_events",
                        }
                    )

        return queries

    def _generate_visualizations(
        self, kpis: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Сгенерировать рекомендации по визуализациям."""
        visualizations: List[Dict[str, Any]] = []

        for kpi in kpis:
            viz_type = "line"  # по умолчанию
            if kpi.get("category") == "technical":
                if "coverage" in kpi["id"]:
                    viz_type = "gauge"  # Для coverage - gauge
                elif "rate" in kpi["id"]:
                    viz_type = "bar"  # Для rate - bar chart

            visualizations.append(
                {
                    "kpi_id": kpi["id"],
                    "type": viz_type,
                    "title": kpi["name"],
                    "description": kpi.get("description", ""),
                    "fields": ["timestamp", "value"],
                    "group_by": ["category"] if kpi.get("category") else None,
                    "recommended_tool": (
                        "Grafana" if kpi.get("category") == "technical" else "Power BI"
                    ),
                }
            )

        return visualizations

    async def _get_all_requirements(self) -> List[Node]:
        """Получить все требования из графа."""
        if not self.backend:
            return []
        try:
            nodes = await self.backend.find_nodes(kind=NodeKind.BA_REQUIREMENT)
            return nodes
        except Exception as e:
            logger.debug("Failed to find requirements: %s", e)
            return []

    async def _get_all_tests(self) -> List[Node]:
        """Получить все тесты из графа."""
        if not self.backend:
            return []
        try:
            # Найти TEST_CASE и TEST_SUITE отдельно
            test_cases = await self.backend.find_nodes(kind=NodeKind.TEST_CASE)
            test_suites = await self.backend.find_nodes(kind=NodeKind.TEST_SUITE)
            return test_cases + test_suites
        except Exception as e:
            logger.debug("Failed to find tests: %s", e)
            return []

    async def _get_all_incidents(self) -> List[Node]:
        """Получить все инциденты из графа."""
        if not self.backend:
            return []
        try:
            nodes = await self.backend.find_nodes(kind=NodeKind.INCIDENT)
            return nodes
        except Exception as e:
            logger.debug("Failed to find incidents: %s", e)
            return []

    async def _get_all_modules(self) -> List[Node]:
        """Получить все модули из графа."""
        if not self.backend:
            return []
        try:
            nodes = await self.backend.find_nodes(kind=NodeKind.MODULE)
            return nodes
        except Exception as e:
            logger.debug("Failed to find modules: %s", e)
            return []

    async def _calculate_change_failure_rate(self) -> float:
        """Рассчитать Change Failure Rate (DORA metric)."""
        if not self.backend:
            return 0.0
        try:
            # Найти все инциденты, связанные с изменениями кода
            incidents = await self._get_all_incidents()
            modules = await self._get_all_modules()

            # Подсчитать инциденты, связанные с модулями
            incident_count = 0
            for incident in incidents:
                # Проверить, есть ли связь с модулем
                incident_neighbors = await self.backend.neighbors(
                    incident.id,
                    kinds=[EdgeKind.TRIGGERS_INCIDENT],
                )
                # Инвертируем: ищем модули, которые связаны с инцидентом
                for neighbor in incident_neighbors:
                    if neighbor.kind == NodeKind.MODULE:
                        incident_count += 1
                        break

            total_modules = len(modules)
            if total_modules == 0:
                return 0.0

            # Change Failure Rate = (инциденты от изменений / общее количество изменений) * 100
            # Упрощённо: инциденты на модуль
            failure_rate = (incident_count / total_modules) * 100
            return round(failure_rate, 2)
        except Exception as e:
            logger.debug("Failed to calculate change failure rate: %s", e)
            return 0.0

    def _generate_template_kpis(self) -> Dict[str, Any]:
        """Сгенерировать шаблонные KPI без графа."""
        return {
            "kpis": [
                {
                    "id": "kpi_template_1",
                    "name": "Template KPI",
                    "description": "Template KPI (graph not available)",
                    "formula": "N/A",
                    "value": None,
                    "target": None,
                    "unit": "N/A",
                    "source": "Template",
                    "frequency": "N/A",
                    "category": "template",
                }
            ],
            "sql_queries": [],
            "visualizations": [],
            "generated_at": datetime.utcnow().isoformat(),
        }
