# [NEXUS IDENTITY] ID: 8523876577921277390 | DATE: 2025-11-19

"""
Documentation & Enablement с Unified Change Graph
-------------------------------------------------

Расширенная реализация BA-07 с использованием Unified Change Graph
для автоматической генерации enablement-материалов на основе реальных артефактов.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.ai.code_analysis.graph import CodeGraphBackend, NodeKind

logger = logging.getLogger(__name__)


class EnablementGeneratorWithGraph:
    """
    Генератор enablement-материалов с использованием Unified Change Graph.

    Автоматически строит гайды, примеры и onboarding-материалы на основе:
    - реальных сценариев из графа
    - связанных требований, кода, тестов
    - существующей документации
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

    async def generate_enablement_plan(
        self,
        feature_name: str,
        *,
        audience: str = "BA+Dev+QA",
        include_examples: bool = True,
        use_graph: bool = True,
    ) -> Dict[str, Any]:
        """
        Сгенерировать план enablement-материалов с использованием графа.

        Args:
            feature_name: Название фичи
            audience: Целевая аудитория (BA+Dev+QA, Product, Executive)
            include_examples: Включать примеры из графа
            use_graph: Использовать Unified Change Graph

        Returns:
            План enablement-материалов с модулями, примерами и ссылками
        """
        modules: List[Dict[str, Any]] = [
            {
                "id": "overview",
                "title": f"Обзор: {feature_name}",
                "deliverables": ["README блок", "FAQ", "архитектурный обзор"],
                "examples": [],
            },
            {
                "id": "howto",
                "title": f"How-to сценарии для {feature_name}",
                "deliverables": ["Cookbook рецепты", "пошаговые туториалы"],
                "examples": [],
            },
            {
                "id": "observability",
                "title": f"Наблюдаемость и SLO для {feature_name}",
                "deliverables": ["метрики", "дашборд", "алерты"],
                "examples": [],
            },
        ]

        # Обогатить примерами из графа
        if use_graph and self.backend and include_examples:
            examples = await self._find_examples_in_graph(feature_name)
            for module in modules:
                module["examples"] = examples.get(module["id"], [])

        return {
            "feature_name": feature_name,
            "audience": audience,
            "modules": modules,
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def generate_guide(
        self,
        topic: str,
        *,
        format: str = "markdown",
        include_code_examples: bool = True,
    ) -> Dict[str, Any]:
        """
        Сгенерировать гайд по теме с примерами из графа.

        Args:
            topic: Тема гайда
            format: Формат вывода (markdown, confluence, html)
            include_code_examples: Включать примеры кода из графа

        Returns:
            Гайд с содержанием, примерами и ссылками
        """
        guide: Dict[str, Any] = {
            "title": f"Guide: {topic}",
            "sections": [],
            "examples": [],
            "references": [],
        }

        # Найти релевантные узлы в графе
        if self.backend and include_code_examples:
            examples = await self._find_code_examples_for_topic(topic)
            guide["examples"] = examples

            # Найти связанные требования
            requirements = await self._find_related_requirements(topic)
            guide["references"].extend(requirements)

        # Построить структуру гайда
        guide["sections"] = [
            {
                "id": "introduction",
                "title": "Введение",
                "content": f"Этот гайд описывает {topic}.",
            },
            {
                "id": "examples",
                "title": "Примеры",
                "content": "Примеры использования из реальных сценариев.",
            },
            {
                "id": "references",
                "title": "Ссылки",
                "content": "Связанные требования и документация.",
            },
        ]

        # Экспорт в нужный формат
        if format == "markdown":
            guide["content"] = self._to_markdown(guide)
        elif format == "confluence":
            guide["content"] = self._to_confluence(guide)

        return guide

    async def generate_presentation_outline(
        self,
        topic: str,
        *,
        audience: str = "stakeholders",
        duration_minutes: int = 30,
    ) -> Dict[str, Any]:
        """
        Сгенерировать outline презентации.

        Args:
            topic: Тема презентации
            audience: Аудитория (stakeholders, technical, executive)
            duration_minutes: Длительность в минутах

        Returns:
            Outline презентации с слайдами и ключевыми сообщениями
        """
        outline: Dict[str, Any] = {
            "title": f"Presentation: {topic}",
            "audience": audience,
            "duration_minutes": duration_minutes,
            "slides": [],
        }

        # Стандартная структура презентации
        slides = [
            {"id": "title", "title": f"{topic}", "content": "Title slide"},
            {"id": "agenda", "title": "Agenda", "content": "Overview of topics"},
            {
                "id": "problem",
                "title": "Problem Statement",
                "content": "Current challenges",
            },
            {"id": "solution", "title": "Solution", "content": "Proposed approach"},
            {"id": "benefits", "title": "Benefits", "content": "Expected outcomes"},
            {"id": "next_steps", "title": "Next Steps", "content": "Action items"},
        ]

        # Обогатить данными из графа
        if self.backend:
            # Найти метрики для слайда benefits
            metrics = await self._find_metrics_for_topic(topic)
            if metrics:
                slides[4]["content"] = f"Benefits: {', '.join(metrics)}"

        outline["slides"] = slides

        return outline

    async def generate_onboarding_checklist(
        self,
        role: str = "BA",
        *,
        include_practical_tasks: bool = True,
    ) -> Dict[str, Any]:
        """
        Сгенерировать onboarding чек-лист для роли.

        Args:
            role: Роль (BA, Dev, QA, Product)
            include_practical_tasks: Включать практические задачи из графа

        Returns:
            Onboarding чек-лист с задачами и ссылками
        """
        checklist: Dict[str, Any] = {
            "role": role,
            "sections": [],
            "tasks": [],
        }

        # Стандартные секции
        sections = [
            {
                "id": "reading",
                "title": "Что прочитать",
                "items": [
                    "README проекта",
                    "Архитектурная документация",
                    "Гайды по использованию",
                ],
            },
            {
                "id": "scenarios",
                "title": "Какие сценарии попробовать",
                "items": [],
            },
            {
                "id": "metrics",
                "title": "Какие метрики отслеживать",
                "items": [],
            },
        ]

        # Обогатить практическими задачами из графа
        if include_practical_tasks and self.backend:
            scenarios = await self._find_scenarios_for_role(role)
            sections[1]["items"] = scenarios

            metrics = await self._find_metrics_for_role(role)
            sections[2]["items"] = metrics

        checklist["sections"] = sections

        return checklist

    async def _find_examples_in_graph(
        self, feature_name: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Найти примеры использования в графе."""
        if not self.backend:
            return {}

        examples: Dict[str, List[Dict[str, Any]]] = {
            "overview": [],
            "howto": [],
            "observability": [],
        }

        # Найти связанные сценарии
        try:
            # Ищем требования, связанные с фичей
            requirements = await self.backend.find_nodes(kind=NodeKind.BA_REQUIREMENT)
            for req in requirements[:5]:  # Ограничить количество
                if feature_name.lower() in req.display_name.lower():
                    examples["overview"].append(
                        {
                            "type": "requirement",
                            "id": req.id,
                            "title": req.display_name,
                        }
                    )
        except Exception as e:
            logger.debug("Failed to find examples in graph: %s", e)

        return examples

    async def _find_code_examples_for_topic(self, topic: str) -> List[Dict[str, Any]]:
        """Найти примеры кода для темы."""
        if not self.backend:
            return []

        examples: List[Dict[str, Any]] = []

        try:
            # Ищем модули, связанные с темой
            modules = await self.backend.find_nodes(kind=NodeKind.MODULE)
            for module in modules[:3]:  # Ограничить количество
                if topic.lower() in module.display_name.lower():
                    examples.append(
                        {
                            "type": "code",
                            "id": module.id,
                            "title": module.display_name,
                            "description": f"Example module for {topic}",
                        }
                    )
        except Exception as e:
            logger.debug("Failed to find code examples: %s", e)

        return examples

    async def _find_related_requirements(self, topic: str) -> List[Dict[str, Any]]:
        """Найти связанные требования."""
        if not self.backend:
            return []

        requirements: List[Dict[str, Any]] = []

        try:
            req_nodes = await self.backend.find_nodes(kind=NodeKind.BA_REQUIREMENT)
            for req in req_nodes[:5]:  # Ограничить количество
                if topic.lower() in req.display_name.lower():
                    requirements.append(
                        {
                            "id": req.id,
                            "title": req.display_name,
                        }
                    )
        except Exception as e:
            logger.debug("Failed to find related requirements: %s", e)

        return requirements

    async def _find_metrics_for_topic(self, topic: str) -> List[str]:
        """Найти метрики для темы."""
        if not self.backend:
            return []

        # Упрощённо: возвращаем стандартные метрики
        return [
            "Code Coverage",
            "Test Coverage",
            "Incident Rate",
        ]

    async def _find_scenarios_for_role(self, role: str) -> List[str]:
        """Найти сценарии для роли."""
        if not self.backend:
            return []

        # Упрощённо: возвращаем стандартные сценарии
        scenarios = {
            "BA": [
                "BA→Dev→QA workflow",
                "Requirements extraction",
                "Process modelling",
            ],
            "Dev": [
                "Code generation",
                "Code review",
                "Testing",
            ],
            "QA": [
                "Test generation",
                "Coverage analysis",
                "Bug detection",
            ],
        }

        return scenarios.get(role, [])

    async def _find_metrics_for_role(self, role: str) -> List[str]:
        """Найти метрики для роли."""
        if not self.backend:
            return []

        # Упрощённо: возвращаем стандартные метрики
        metrics = {
            "BA": [
                "Requirements coverage",
                "Process completion rate",
                "Stakeholder satisfaction",
            ],
            "Dev": [
                "Code quality",
                "Deployment frequency",
                "Change failure rate",
            ],
            "QA": [
                "Test coverage",
                "Bug detection rate",
                "Test execution time",
            ],
        }

        return metrics.get(role, [])

    def _to_markdown(self, guide: Dict[str, Any]) -> str:
        """Конвертировать гайд в Markdown."""
        lines = [f"# {guide['title']}", ""]

        for section in guide.get("sections", []):
            lines.append(f"## {section.get('title', 'Section')}")
            lines.append("")
            lines.append(section.get("content", ""))
            lines.append("")

        # Примеры
        if guide.get("examples"):
            lines.append("## Примеры")
            lines.append("")
            for example in guide["examples"]:
                lines.append(f"- {example.get('title', 'Example')}")
            lines.append("")

        return "\n".join(lines)

    def _to_confluence(self, guide: Dict[str, Any]) -> str:
        """Конвертировать гайд в Confluence формат."""
        lines = [f"h1. {guide['title']}", ""]

        for section in guide.get("sections", []):
            lines.append(f"h2. {section.get('title', 'Section')}")
            lines.append("")
            lines.append(section.get("content", ""))
            lines.append("")

        return "\n".join(lines)
