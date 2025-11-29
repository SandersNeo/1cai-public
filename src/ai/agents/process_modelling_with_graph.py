# [NEXUS IDENTITY] ID: 6844130591866032192 | DATE: 2025-11-19

"""
Process & Journey Modelling с Unified Change Graph
--------------------------------------------------

Расширенная реализация BA-03 с использованием Unified Change Graph
для связи процессов с кодом, требованиями и тестами.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.ai.code_analysis.graph import CodeGraphBackend, EdgeKind, NodeKind

logger = logging.getLogger(__name__)


class ProcessModellerWithGraph:
    """
    Генератор моделей процессов с использованием Unified Change Graph.

    Автоматически связывает процессы с:
    - требованиями (BA_REQUIREMENT)
    - кодом (MODULE, FUNCTION)
    - тестами (TEST_CASE)
    - инцидентами (INCIDENT)
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

    async def generate_bpmn_with_graph(
        self,
        process_description: str,
        *,
        requirement_id: Optional[str] = None,
        format: str = "mermaid",
    ) -> Dict[str, Any]:
        """
        Сгенерировать BPMN модель процесса с использованием графа.

        Args:
            process_description: Текстовое описание процесса
            requirement_id: ID требования для связи с графом
            format: Формат вывода (mermaid, plantuml, json)

        Returns:
            BPMN модель с метаданными и связями с графом
        """
        # Базовая структура процесса
        process_model = await self._parse_process_description(process_description)

        # Если есть requirement_id, связать с графом
        graph_refs: List[str] = []
        if requirement_id and self.backend:
            graph_refs = await self._find_graph_refs_for_requirement(requirement_id)

        # Добавить связи с графом
        process_model["graph_refs"] = graph_refs
        process_model["metadata"] = {
            "requirement_id": requirement_id,
            "format": format,
            "generated_at": datetime.utcnow().isoformat(),
        }

        # Экспорт в нужный формат
        if format == "mermaid":
            process_model["diagram"] = self._to_mermaid(process_model)
        elif format == "plantuml":
            process_model["diagram"] = self._to_plantuml(process_model)
        elif format == "json":
            process_model["diagram"] = process_model  # Уже JSON

        return process_model

    async def generate_journey_map(
        self,
        journey_description: str,
        *,
        stages: Optional[List[str]] = None,
        format: str = "mermaid",
    ) -> Dict[str, Any]:
        """
        Сгенерировать Customer Journey Map.

        Args:
            journey_description: Текстовое описание customer journey
            stages: Список стадий (опционально, будет извлечён из описания)
            format: Формат вывода (mermaid, plantuml, json)

        Returns:
            Journey Map с стадиями, действиями, эмоциями и pain points
        """
        # Извлечь стадии из описания
        if not stages:
            stages = self._extract_journey_stages(journey_description)

        journey_map: Dict[str, Any] = {
            "stages": [],
            "touchpoints": [],
            "pain_points": [],
            "opportunities": [],
        }

        # Построить карту для каждой стадии
        for stage in stages:
            stage_data = {
                "name": stage,
                "actions": [],
                "emotions": [],
                "touchpoints": [],
            }
            journey_map["stages"].append(stage_data)

        # Если есть граф, найти связанные touchpoints
        if self.backend:
            touchpoints = await self._find_touchpoints_in_graph(journey_description)
            journey_map["touchpoints"] = touchpoints

        journey_map["metadata"] = {
            "format": format,
            "generated_at": datetime.utcnow().isoformat(),
        }

        # Экспорт в нужный формат
        if format == "mermaid":
            journey_map["diagram"] = self._journey_to_mermaid(journey_map)
        elif format == "plantuml":
            journey_map["diagram"] = self._journey_to_plantuml(journey_map)

        return journey_map

    async def validate_process(
        self,
        process_model: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Валидация модели процесса.

        Проверяет:
        - наличие владельцев для шагов
        - наличие входов/выходов
        - наличие измеримых результатов
        - связи с кодом/тестами (через граф)

        Args:
            process_model: Модель процесса для валидации

        Returns:
            Результат валидации с замечаниями и рекомендациями
        """
        issues: List[Dict[str, Any]] = []
        warnings: List[Dict[str, Any]] = []

        # Проверка владельцев
        steps = process_model.get("steps", [])
        for i, step in enumerate(steps):
            if not step.get("owner"):
                issues.append(
                    {
                        "type": "missing_owner",
                        "step_index": i,
                        "step_name": step.get("name", "Unknown"),
                        "severity": "high",
                        "message": f"Шаг '{step.get('name')}' не имеет владельца",
                    }
                )

        # Проверка входов/выходов
        for i, step in enumerate(steps):
            if not step.get("inputs") and not step.get("outputs"):
                warnings.append(
                    {
                        "type": "missing_io",
                        "step_index": i,
                        "step_name": step.get("name", "Unknown"),
                        "severity": "medium",
                        "message": f"Шаг '{step.get('name')}' не имеет входов/выходов",
                    }
                )

        # Проверка связей с графом
        graph_refs = process_model.get("graph_refs", [])
        if not graph_refs and self.backend:
            warnings.append(
                {
                    "type": "no_graph_refs",
                    "severity": "low",
                    "message": "Процесс не связан с кодом/требованиями в графе",
                }
            )

        # Проверка измеримых результатов
        has_kpi = any(step.get("kpi") for step in steps)
        if not has_kpi:
            warnings.append(
                {
                    "type": "no_kpi",
                    "severity": "medium",
                    "message": "Процесс не имеет измеримых результатов (KPI)",
                }
            )

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "summary": {
                "total_steps": len(steps),
                "steps_with_owners": sum(1 for s in steps if s.get("owner")),
                "steps_with_io": sum(
                    1 for s in steps if s.get("inputs") or s.get("outputs")
                ),
                "graph_refs_count": len(graph_refs),
            },
        }

    async def _parse_process_description(self, description: str) -> Dict[str, Any]:
        """Парсинг текстового описания процесса."""
        # Упрощённый парсинг (в реальности можно использовать LLM)
        lines = [line.strip() for line in description.split("\n") if line.strip()]

        steps: List[Dict[str, Any]] = []
        actors: List[str] = []
        events: List[str] = []

        for i, line in enumerate(lines):
            # Простая эвристика: строки, начинающиеся с цифр или "-"
            if line[0].isdigit() or line.startswith("-"):
                step_name = line.lstrip("0123456789.- ").strip()
                if step_name:
                    steps.append(
                        {
                            "id": f"step_{i+1}",
                            "name": step_name,
                            "order": i + 1,
                        }
                    )

        return {
            "name": lines[0] if lines else "Process",
            "description": description,
            "steps": steps,
            "actors": actors,
            "events": events,
        }

    async def _find_graph_refs_for_requirement(self, requirement_id: str) -> List[str]:
        """Найти ссылки на граф для требования."""
        if not self.backend:
            return []

        req_node_id = f"ba_requirement:{requirement_id}"
        req_node = await self.backend.get_node(req_node_id)

        if not req_node:
            return []

        refs: List[str] = [req_node_id]

        # Найти код, реализующий требование
        code_nodes = await self.backend.neighbors(
            req_node_id,
            kinds=[EdgeKind.IMPLEMENTS],
        )
        refs.extend([node.id for node in code_nodes])

        # Найти тесты
        for code_node in code_nodes:
            test_nodes = await self.backend.neighbors(
                code_node.id,
                kinds=[EdgeKind.TESTED_BY],
            )
            refs.extend([node.id for node in test_nodes])

        return list(set(refs))  # Удалить дубликаты

    async def _find_touchpoints_in_graph(
        self, journey_description: str
    ) -> List[Dict[str, Any]]:
        """Найти touchpoints в графе (API endpoints, модули)."""
        if not self.backend:
            return []

        touchpoints: List[Dict[str, Any]] = []

        # Найти API endpoints
        try:
            api_nodes = await self.backend.find_nodes(kind=NodeKind.API_ENDPOINT)
            for node in api_nodes:
                touchpoints.append(
                    {
                        "id": node.id,
                        "type": "api_endpoint",
                        "name": node.display_name,
                    }
                )
        except Exception as e:
            logger.debug("Failed to find API endpoints: %s", e)

        return touchpoints

    def _extract_journey_stages(self, description: str) -> List[str]:
        """Извлечь стадии customer journey из описания."""
        # Стандартные стадии
        default_stages = [
            "Awareness",
            "Consideration",
            "Purchase",
            "Retention",
            "Advocacy",
        ]

        # Простая эвристика: ищем упоминания стадий в тексте
        description_lower = description.lower()
        found_stages = []

        for stage in default_stages:
            if stage.lower() in description_lower:
                found_stages.append(stage)

        return found_stages if found_stages else default_stages

    def _to_mermaid(self, process_model: Dict[str, Any]) -> str:
        """Конвертировать модель процесса в Mermaid диаграмму."""
        steps = process_model.get("steps", [])
        if not steps:
            return "graph TD\n    A[Process]"

        lines = ["graph TD"]
        for i, step in enumerate(steps):
            step_id = step.get("id", f"step{i}")
            step_name = step.get("name", "Step")
            lines.append(f'    {step_id}["{step_name}"]')

        # Связи между шагами
        for i in range(len(steps) - 1):
            current_id = steps[i].get("id", f"step{i}")
            next_id = steps[i + 1].get("id", f"step{i+1}")
            lines.append(f"    {current_id} --> {next_id}")

        return "\n".join(lines)

    def _to_plantuml(self, process_model: Dict[str, Any]) -> str:
        """Конвертировать модель процесса в PlantUML диаграмму."""
        steps = process_model.get("steps", [])
        if not steps:
            return "@startuml\nProcess\n@enduml"

        lines = ["@startuml"]
        for step in steps:
            step_name = step.get("name", "Step")
            lines.append(f'"{step_name}"')

        lines.append("@enduml")
        return "\n".join(lines)

    def _journey_to_mermaid(self, journey_map: Dict[str, Any]) -> str:
        """Конвертировать Journey Map в Mermaid диаграмму."""
        stages = journey_map.get("stages", [])
        if not stages:
            return "graph LR\n    A[Journey]"

        lines = ["graph LR"]
        for stage in stages:
            stage_name = stage.get("name", "Stage")
            stage_id = stage_name.lower().replace(" ", "_")
            lines.append(f'    {stage_id}["{stage_name}"]')

        # Связи между стадиями
        for i in range(len(stages) - 1):
            current_id = stages[i].get("name", "Stage").lower().replace(" ", "_")
            next_id = stages[i + 1].get("name", "Stage").lower().replace(" ", "_")
            lines.append(f"    {current_id} --> {next_id}")

        return "\n".join(lines)

    def _journey_to_plantuml(self, journey_map: Dict[str, Any]) -> str:
        """Конвертировать Journey Map в PlantUML диаграмму."""
        stages = journey_map.get("stages", [])
        if not stages:
            return "@startuml\nJourney\n@enduml"

        lines = ["@startuml"]
        for stage in stages:
            stage_name = stage.get("name", "Stage")
            lines.append(f'"{stage_name}"')

        lines.append("@enduml")
        return "\n".join(lines)
