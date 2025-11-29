# [NEXUS IDENTITY] ID: 4283341078064663194 | DATE: 2025-11-19

"""
Integrations & Collaboration с Unified Change Graph
---------------------------------------------------

Расширенная реализация BA-06 с использованием Unified Change Graph
для автоматической синхронизации артефактов с внешними системами.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.ai.code_analysis.graph import CodeGraphBackend, EdgeKind, Node

logger = logging.getLogger(__name__)


class IntegrationSyncWithGraph:
    """
    Расширенная синхронизация интеграций с использованием Unified Change Graph.

    Автоматически синхронизирует артефакты с Jira/Confluence:
    - Требования → Jira задачи
    - BPMN/KPI → Confluence страницы
    - Traceability matrix → Confluence таблицы
    - Автоматические ссылки на код/тесты из графа
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

    async def sync_requirements_to_jira(
        self,
        requirement_ids: List[str],
        *,
        project_key: Optional[str] = None,
        issue_type: str = "Story",
    ) -> Dict[str, Any]:
        """
        Синхронизировать требования из графа в Jira.

        Создаёт задачи в Jira на основе требований, автоматически добавляя:
        - Ссылки на код (IMPLEMENTS)
        - Ссылки на тесты (TESTED_BY)
        - Ссылки на инциденты (TRIGGERS_INCIDENT)

        Args:
            requirement_ids: Список ID требований
            project_key: Ключ проекта Jira
            issue_type: Тип задачи (Story, Task, Epic)

        Returns:
            Результат синхронизации с ссылками на созданные задачи
        """
        if not self.backend:
            logger.warning("Graph backend not available, cannot sync requirements")
            return {
                "synced": [],
                "errors": ["Graph backend not available"],
            }

        synced: List[Dict[str, Any]] = []
        errors: List[str] = []

        for req_id in requirement_ids:
            req_node_id = f"ba_requirement:{req_id}"
            req_node = await self.backend.get_node(req_node_id)

            if not req_node:
                errors.append(f"Requirement {req_id} not found in graph")
                continue

            # Найти связанные артефакты
            code_nodes = await self.backend.neighbors(
                req_node_id,
                kinds=[EdgeKind.IMPLEMENTS],
            )

            test_nodes: List[Node] = []
            for code_node in code_nodes:
                tests = await self.backend.neighbors(
                    code_node.id,
                    kinds=[EdgeKind.TESTED_BY],
                )
                test_nodes.extend(tests)

            # Построить описание задачи с ссылками
            description = self._build_jira_description(
                req_node,
                code_nodes,
                test_nodes,
            )

            # Создать задачу в Jira (здесь нужен реальный Jira client)
            # Пока возвращаем структуру для синхронизации
            synced.append(
                {
                    "requirement_id": req_id,
                    "jira_key": None,  # Будет заполнено после создания
                    "title": req_node.display_name,
                    "description": description,
                    "code_refs": [node.id for node in code_nodes],
                    "test_refs": [node.id for node in test_nodes],
                    "status": "pending_sync",
                }
            )

        return {
            "synced": synced,
            "errors": errors,
            "total": len(requirement_ids),
            "synced_count": len(synced),
        }

    async def sync_bpmn_to_confluence(
        self,
        process_model: Dict[str, Any],
        *,
        space_key: Optional[str] = None,
        parent_page_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Синхронизировать BPMN модель процесса в Confluence.

        Создаёт страницу в Confluence с:
        - BPMN диаграммой (Mermaid/PlantUML)
        - Автоматическими ссылками на код/тесты из графа
        - Ссылками на связанные требования

        Args:
            process_model: Модель процесса
            space_key: Ключ пространства Confluence
            parent_page_id: ID родительской страницы

        Returns:
            Результат синхронизации с ссылкой на созданную страницу
        """
        graph_refs = process_model.get("graph_refs", [])

        # Построить содержимое страницы
        page_content = self._build_confluence_bpmn_content(
            process_model,
            graph_refs,
        )

        # Создать страницу в Confluence (здесь нужен реальный Confluence client)
        # Пока возвращаем структуру для синхронизации
        return {
            "page_id": None,  # Будет заполнено после создания
            "page_title": process_model.get("name", "Process Model"),
            "content": page_content,
            "graph_refs": graph_refs,
            "status": "pending_sync",
        }

    async def sync_kpi_to_confluence(
        self,
        kpi_report: Dict[str, Any],
        *,
        space_key: Optional[str] = None,
        parent_page_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Синхронизировать KPI отчёт в Confluence.

        Создаёт страницу в Confluence с:
        - Таблицей KPI
        - SQL-запросами
        - Рекомендациями по визуализациям
        - Ссылками на связанные требования/код из графа

        Args:
            kpi_report: Отчёт KPI
            space_key: Ключ пространства Confluence
            parent_page_id: ID родительской страницы

        Returns:
            Результат синхронизации с ссылкой на созданную страницу
        """
        kpis = kpi_report.get("kpis", [])
        sql_queries = kpi_report.get("sql_queries", [])

        # Построить содержимое страницы
        page_content = self._build_confluence_kpi_content(
            kpis,
            sql_queries,
            kpi_report.get("visualizations", []),
        )

        return {
            "page_id": None,  # Будет заполнено после создания
            "page_title": f"KPI Report: {kpi_report.get('initiative', 'Unknown')}",
            "content": page_content,
            "status": "pending_sync",
        }

    async def sync_traceability_to_confluence(
        self,
        traceability_report: Dict[str, Any],
        *,
        space_key: Optional[str] = None,
        parent_page_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Синхронизировать Traceability matrix в Confluence.

        Создаёт страницу в Confluence с:
        - Таблицей traceability matrix
        - Risk register
        - Risk heatmap
        - Ссылками на код/тесты/инциденты из графа

        Args:
            traceability_report: Отчёт traceability
            space_key: Ключ пространства Confluence
            parent_page_id: ID родительской страницы

        Returns:
            Результат синхронизации с ссылкой на созданную страницу
        """
        matrix = traceability_report.get("traceability", {}).get("matrix", [])
        risk_register = traceability_report.get("risk_register", [])

        # Построить содержимое страницы
        page_content = self._build_confluence_traceability_content(
            matrix,
            risk_register,
            traceability_report.get("risk_heatmap", {}),
        )

        return {
            "page_id": None,  # Будет заполнено после создания
            "page_title": "Traceability & Compliance Report",
            "content": page_content,
            "status": "pending_sync",
        }

    def _build_jira_description(
        self,
        req_node: Node,
        code_nodes: List[Node],
        test_nodes: List[Node],
    ) -> str:
        """Построить описание задачи Jira с ссылками на код/тесты."""
        lines = [f"*Requirement:* {req_node.display_name}", ""]

        if code_nodes:
            lines.append("*Реализация:*")
            for code_node in code_nodes:
                lines.append(f"* {code_node.display_name} ({code_node.id})")
            lines.append("")

        if test_nodes:
            lines.append("*Тесты:*")
            for test_node in test_nodes:
                lines.append(f"* {test_node.display_name} ({test_node.id})")
            lines.append("")

        return "\n".join(lines)

    def _build_confluence_bpmn_content(
        self,
        process_model: Dict[str, Any],
        graph_refs: List[str],
    ) -> str:
        """Построить содержимое страницы Confluence для BPMN."""
        lines = [
            f"h1. {process_model.get('name', 'Process Model')}",
            "",
            f"*Generated:* {datetime.utcnow().isoformat()}",
            "",
        ]

        # BPMN диаграмма
        diagram = process_model.get("diagram", "")
        if diagram:
            lines.append("h2. Process Diagram")
            lines.append("")
            if "mermaid" in diagram.lower():
                lines.append("{code:language=mermaid}")
                lines.append(diagram)
                lines.append("{code}")
            else:
                lines.append("{code}")
                lines.append(diagram)
                lines.append("{code}")
            lines.append("")

        # Ссылки на граф
        if graph_refs:
            lines.append("h2. Related Artifacts")
            lines.append("")
            for ref in graph_refs[:10]:  # Ограничить количество
                lines.append(f"* {ref}")
            lines.append("")

        return "\n".join(lines)

    def _build_confluence_kpi_content(
        self,
        kpis: List[Dict[str, Any]],
        sql_queries: List[Dict[str, Any]],
        visualizations: List[Dict[str, Any]],
    ) -> str:
        """Построить содержимое страницы Confluence для KPI."""
        lines = ["h1. KPI Report", ""]

        # Таблица KPI
        if kpis:
            lines.append("h2. Key Performance Indicators")
            lines.append("")
            lines.append("||KPI||Value||Target||Unit||Category||")
            for kpi in kpis:
                name = kpi.get("name", "N/A")
                value = kpi.get("value", "N/A")
                target = kpi.get("target", "N/A")
                unit = kpi.get("unit", "N/A")
                category = kpi.get("category", "N/A")
                lines.append(f"|{name}|{value}|{target}|{unit}|{category}|")
            lines.append("")

        # SQL-запросы
        if sql_queries:
            lines.append("h2. SQL Queries")
            lines.append("")
            for query in sql_queries:
                lines.append(f"h3. {query.get('description', 'Query')}")
                lines.append("{code:language=sql}")
                lines.append(query.get("query", ""))
                lines.append("{code}")
                lines.append("")

        return "\n".join(lines)

    def _build_confluence_traceability_content(
        self,
        matrix: List[Dict[str, Any]],
        risk_register: List[Dict[str, Any]],
        risk_heatmap: Dict[str, Any],
    ) -> str:
        """Построить содержимое страницы Confluence для Traceability."""
        lines = ["h1. Traceability & Compliance Report", ""]

        # Traceability Matrix
        if matrix:
            lines.append("h2. Traceability Matrix")
            lines.append("")
            lines.append("||Requirement||Code||Tests||Coverage||")
            for entry in matrix[:20]:  # Ограничить количество
                req_id = entry.get("requirement_id", "N/A")
                code_count = len(entry.get("code_nodes", []))
                test_count = len(entry.get("test_nodes", []))
                coverage = entry.get("coverage", "N/A")
                lines.append(f"|{req_id}|{code_count}|{test_count}|{coverage}|")
            lines.append("")

        # Risk Register
        if risk_register:
            lines.append("h2. Risk Register")
            lines.append("")
            lines.append("||Requirement||Risk Level||Reasons||")
            for risk in risk_register[:20]:  # Ограничить количество
                req_id = risk.get("requirement_id", "N/A")
                level = risk.get("risk_level", "N/A")
                reasons = ", ".join(risk.get("risk_reasons", []))
                lines.append(f"|{req_id}|{level}|{reasons}|")
            lines.append("")

        # Risk Heatmap
        if risk_heatmap:
            lines.append("h2. Risk Heatmap")
            lines.append("")
            lines.append(f"*High:* {risk_heatmap.get('high', 0)}")
            lines.append(f"*Medium:* {risk_heatmap.get('medium', 0)}")
            lines.append(f"*Low:* {risk_heatmap.get('low', 0)}")
            lines.append("")

        return "\n".join(lines)
