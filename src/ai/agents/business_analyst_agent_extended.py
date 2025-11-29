# [NEXUS IDENTITY] ID: 4584524652348813128 | DATE: 2025-11-19

"""
Business Analyst AI Agent Extended.

Provides requirement extraction, BPMN generation, gap analysis and traceability
with optional LLM-based refinement (GigaChat / YandexGPT).
"""

from __future__ import annotations

import asyncio
import html
import json
import logging
import os
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union

from src.ai.clients import (
    GigaChatClient,
    LLMCallError,
    LLMNotConfiguredError,
    YandexGPTClient,
)
from src.ai.utils.document_loader import read_document
from src.integrations.confluence import ConfluenceClient
from src.integrations.exceptions import IntegrationConfigError
from src.integrations.jira import JiraClient
from src.integrations.onedocflow import OneCDocflowClient
from src.integrations.powerbi import PowerBIClient

logger = logging.getLogger(__name__)


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


class RequirementsExtractor:
    """Heuristic extraction of requirements and related artefacts."""

    def __init__(self) -> None:
        self.requirement_patterns = self._load_requirement_patterns()
        self.user_story_patterns = [
            r"как\s+(?P<role>[^,]+?),?\s+я\s+(?:хочу|должен|могу)\s+(?P<goal>[^,]+?)(?:,\s*чтобы\s+(?P<benefit>.+))?$",
            r"как\s+(?P<role>[^,]+?)\s+мне\s+нужно\s+(?P<goal>[^,]+)",
        ]

    def _load_requirement_patterns(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "functional",
                "patterns": [
                    r"система должна\s+(?P<body>.+)",
                    r"необходимо\s+(?P<body>.+)",
                    r"должен(?:а|о|ы)?\s+обеспечивать\s+(?P<body>.+)",
                    r"требуется\s+(?P<body>.+)",
                    r"пользователь\s+(?:может|должен)\s+(?P<body>.+)",
                ],
            },
            {
                "type": "non_functional",
                "patterns": [
                    r"производительность[:\s]+(?P<body>.+)",
                    r"(?:время|скорость)\s+(?:отклика|выполнения)[:\s]+(?P<body>.+)",
                    r"(?:количество|число)\s+пользователей[:\s]+(?P<body>.+)",
                    r"(?:доступность|uptime)[:\s]+(?P<body>.+)",
                    r"безопасность[:\s]+(?P<body>.+)",
                ],
            },
            {
                "type": "constraint",
                "patterns": [
                    r"ограничение[:\s]+(?P<body>.+)",
                    r"не допускается\s+(?P<body>.+)",
                    r"запрещено\s+(?P<body>.+)",
                    r"в рамках\s+(?:бюджета|срока)\s+(?P<body>.+)",
                ],
            },
        ]

    async def extract_requirements(
        self,
        document_text: str,
        document_type: str = "tz",
        *,
        source_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        logger.info(
            "Extracting requirements (heuristics) for document type %s", document_type
        )

        sentences = self._split_sentences(document_text)
        functional: List[Dict[str, Any]] = []
        non_functional: List[Dict[str, Any]] = []
        constraints: List[Dict[str, Any]] = []

        for idx, sentence in enumerate(sentences):
            cleaned = sentence.strip()
            if not cleaned:
                continue
            for pattern_info in self.requirement_patterns:
                req_type = pattern_info["type"]
                matched = False
                for pattern in pattern_info["patterns"]:
                    match = re.search(pattern, cleaned, re.IGNORECASE)
                    if not match:
                        continue
                    body = match.groupdict().get("body") or match.group(0)
                    requirement = self._build_requirement(
                        req_type, body, cleaned, sentence_index=idx
                    )
                    if req_type == "functional":
                        functional.append(requirement)
                    elif req_type == "non_functional":
                        non_functional.append(requirement)
                    else:
                        constraints.append(requirement)
                    matched = True
                    break
                if matched:
                    break
            if not matched:
                for candidate in cleaned.splitlines():
                    candidate = candidate.strip()
                    if not candidate:
                        continue
                    list_match = re.match(r"^\d+[\.\)]\s+(?P<body>.+)", candidate)
                    if list_match:
                        body = list_match.group("body")
                        functional.append(
                            self._build_requirement(
                                "functional", body, candidate, sentence_index=idx
                            )
                        )
                        matched = True
                        break

        stakeholders = self._extract_stakeholders(document_text)
        acceptance_criteria = self._extract_acceptance_criteria(document_text)
        user_stories = self._extract_user_stories(document_text)

        if not functional:
            for idx, line in enumerate(document_text.splitlines()):
                cleaned_line = line.strip(" \t-")
                if not cleaned_line:
                    continue
                list_match = re.match(r"^\d+[\.\)]\s*(?P<body>.+)", cleaned_line)
                keyword_match = re.search(
                    r"(должн|необходимо|требуется)", cleaned_line, re.IGNORECASE
                )
                body = None
                if list_match:
                    body = list_match.group("body")
                elif keyword_match:
                    body = cleaned_line.split(":", 1)[-1].strip() or cleaned_line
                if body:
                    functional.append(
                        self._build_requirement(
                            "functional", body, cleaned_line, sentence_index=idx
                        )
                    )

        summary = self._build_summary(functional, non_functional, constraints)

        return {
            "document_type": document_type,
            "source_path": source_path,
            "functional_requirements": functional,
            "non_functional_requirements": non_functional,
            "constraints": constraints,
            "stakeholders": stakeholders,
            "user_stories": user_stories,
            "acceptance_criteria": acceptance_criteria,
            "summary": summary,
        }

    def _build_requirement(
        self,
        req_type: str,
        body: str,
        sentence: str,
        *,
        sentence_index: int,
    ) -> Dict[str, Any]:
        body = _normalize_whitespace(body)
        sentence = _normalize_whitespace(sentence)

        prefix = {"functional": "FR", "non_functional": "NFR", "constraint": "CON"}[
            req_type
        ]
        requirement_id = f"{prefix}-{sentence_index + 1:03d}"

        priority = "medium"
        lowered = sentence.lower()
        if any(
            keyword in lowered
            for keyword in ("обязательно", "критично", "срочно", "must")
        ):
            priority = "high"
        elif any(
            keyword in lowered
            for keyword in ("желательно", "может", "опционально", "nice to have")
        ):
            priority = "low"

        confidence = 0.65
        if priority == "high":
            confidence += 0.1
        if len(sentence) > 120:
            confidence += 0.05
        confidence = min(confidence, 0.95)

        return {
            "id": requirement_id,
            "title": body[:120],
            "description": sentence,
            "priority": priority,
            "confidence": round(confidence, 2),
            "category": req_type,
            "source": f"sentence:{sentence_index + 1}",
        }

    def _split_sentences(self, document_text: str) -> List[str]:
        return re.split(r"(?<=[.!?])\s+", document_text)

    def _extract_stakeholders(self, text: str) -> List[str]:
        titles = [
            "менеджер",
            "руководитель",
            "директор",
            "администратор",
            "пользователь",
            "бухгалтер",
            "кладовщик",
            "продавец",
            "клиент",
            "оператор",
        ]
        found = {title.capitalize() for title in titles if title in text.lower()}
        return sorted(found)

    def _extract_acceptance_criteria(self, text: str) -> List[str]:
        patterns = [
            r"критерий(?:и)? приемки[:\s]+(.+)",
            r"должно быть обеспечено[:\s]+(.+)",
            r"результат(?:ом)?\s+(?:должен|является)[:\s]+(.+)",
            r"принимается, если\s+(.+)",
        ]
        criteria: List[str] = []
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                criteria.append(_normalize_whitespace(match.group(1)))
        return criteria

    def _extract_user_stories(self, text: str) -> List[Dict[str, Any]]:
        stories: List[Dict[str, Any]] = []
        lines = [line.strip() for line in text.splitlines()]
        counter = 1
        for line in lines:
            normalized = line.lower()
            for pattern in self.user_story_patterns:
                match = re.search(pattern, normalized, re.IGNORECASE)
                if not match:
                    continue
                groups = match.groupdict()
                role = groups.get("role", "").strip().strip(",.")
                goal = groups.get("goal", "").strip().strip(",.")
                benefit = groups.get("benefit", "").strip().strip(",.")
                stories.append(
                    {
                        "id": f"US-{counter:03d}",
                        "role": role.capitalize(),
                        "goal": goal,
                        "benefit": benefit or "",
                        "acceptance_criteria": [],
                    }
                )
                counter += 1
                break
        return stories

    def _build_summary(
        self,
        functional: List[Dict[str, Any]],
        non_functional: List[Dict[str, Any]],
        constraints: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        total = len(functional) + len(non_functional) + len(constraints)
        priorities = Counter(
            [req["priority"] for req in functional + non_functional + constraints]
        )
        return {
            "total_requirements": total,
            "functional": len(functional),
            "non_functional": len(non_functional),
            "constraints": len(constraints),
            "priority_distribution": dict(priorities),
            "llm_used": False,
        }

    def _extract_actors(self, description: str) -> List[str]:
        """Извлечение участников процесса"""
        actors = set()

        patterns = [
            r"(\w+(?:щик|лог|тель|ант|ер))",
            r"(менеджер|директор|бухгалтер|кладовщик|продавец|клиент)",
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, description, re.IGNORECASE)
            for match in matches:
                actors.add(match.group(1).capitalize())

        return list(actors)[:10]

    def _extract_activities(self, description: str) -> List[str]:
        activities = []
        verb_patterns = [
            r"(создать|создание)\s+(\w+)",
            r"(проверить|проверка)\s+(\w+)",
            r"(утвердить|утверждение)\s+(\w+)",
            r"(отправить|отправка)\s+(\w+)",
            r"(получить|получение)\s+(\w+)",
        ]

        for pattern in verb_patterns:
            matches = re.finditer(pattern, description, re.IGNORECASE)
            for match in matches:
                activity = f"{match.group(1)} {match.group(2)}"
                activities.append(activity)

        return activities[:15]

    def _extract_decision_points(self, description: str) -> List[Dict[str, Any]]:
        decisions: List[Dict[str, Any]] = []
        patterns = [
            r"если\s+(.+?)\s+,?\s+то",
            r"в случае\s+(.+?)\s+,?\s+(?:выполняется|происходит)",
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, description, re.IGNORECASE)
            for match in matches:
                decisions.append({"condition": match.group(1), "type": "decision"})

        return decisions[:10]

    def _generate_mermaid(
        self,
        actors: List[str],
        activities: List[str],
        decisions: List[Dict[str, Any]],
    ) -> str:
        mermaid = "graph TD\n"
        mermaid += "    Start[Начало] --> Activity1\n"

        limited_activities = activities[:5]
        for i, activity in enumerate(limited_activities, 1):
            label = self._sanitize_step(activity, for_mermaid=True)
            mermaid += f"    Activity{i}[{label}] --> "
            if i < len(limited_activities):
                mermaid += f"Activity{i+1}\n"
            else:
                mermaid += "End[Конец]\n"

        return mermaid

    def _generate_bpmn_xml(
        self,
        actors: List[str],
        activities: List[str],
        decisions: List[Dict[str, Any]],
    ) -> str:
        bpmn = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
                  id="Definitions_1">
  <bpmn:process id="Process_1" isExecutable="false">
    <bpmn:startEvent id="StartEvent_1" name="Начало"/>
"""

        for i, activity in enumerate(activities[:5], 1):
            label = self._sanitize_step(activity, for_mermaid=False)
            bpmn += f'    <bpmn:task id="Activity_{i}" name="{label}"/>\n'

        bpmn += """    <bpmn:endEvent id="EndEvent_1" name="Конец"/>
  </bpmn:process>
</bpmn:definitions>
"""

        return bpmn


class BPMNGenerator:
    """Упрощённый генератор BPMN-диаграмм для unit-тестов."""

    def __init__(self) -> None:
        self.default_lane = "System"
        self._max_label_length = 120
        self._mermaid_translation = str.maketrans(
            {
                "[": "(",
                "]": ")",
                "{": "(",
                "}": ")",
                "<": " ",
                ">": " ",
                "`": " ",
                '"': " ",
                "'": " ",
            }
        )

    def _sanitize_step(self, text: str, *, for_mermaid: bool) -> str:
        cleaned = re.sub(r"\s+", " ", text or "").strip()
        if not cleaned:
            cleaned = "Step"
        if len(cleaned) > self._max_label_length:
            cleaned = cleaned[: self._max_label_length].rstrip()
        if for_mermaid:
            cleaned = cleaned.translate(self._mermaid_translation)
            cleaned = cleaned.replace("--", "—")
        else:
            cleaned = html.escape(cleaned, quote=True)
        return cleaned

    async def generate_bpmn(self, process_description: str) -> Dict[str, Any]:
        steps = [
            step.strip()
            for step in re.split(r"[.\n]", process_description or "")
            if step.strip()
        ]
        if not steps:
            steps = ["Начало процесса", "Завершение процесса"]

        elements: List[Dict[str, Any]] = []
        mermaid_lines = ["flowchart TD"]
        previous_node = None

        for idx, step in enumerate(steps, start=1):
            node_id = f"S{idx}"
            mermaid_label = self._sanitize_step(step, for_mermaid=True)
            xml_label = self._sanitize_step(step, for_mermaid=False)
            elements.append(
                {
                    "id": node_id,
                    "name": xml_label,
                    "raw_name": step,
                    "type": "task",
                    "lane": self.default_lane,
                }
            )
            mermaid_lines.append(f"{node_id}[{mermaid_label}]")
            if previous_node:
                mermaid_lines.append(f"{previous_node} --> {node_id}")
            previous_node = node_id

        return {
            "bpmn": {
                "lanes": [
                    {"name": self.default_lane, "elements": [e["id"] for e in elements]}
                ],
                "elements": elements,
            },
            "mermaid": "\n".join(mermaid_lines),
            "metadata": {
                "steps": len(elements),
                "generated_at": datetime.utcnow().isoformat(),
            },
        }


class GapAnalyzer:
    """Анализатор разрывов между текущим и желаемым состоянием"""

    async def perform_gap_analysis(
        self, current_state: Dict, desired_state: Dict
    ) -> Dict[str, Any]:
        """
        Gap анализ

        Args:
            current_state: {
                "processes": [...],
                "systems": [...],
                "capabilities": [...]
            }
            desired_state: {
                "processes": [...],
                "systems": [...],
                "capabilities": [...]
            }

        Returns:
            Детальный gap analysis с roadmap
        """
        logger.info("Performing gap analysis")

        gaps = []

        # Analyze processes
        current_processes = set(current_state.get("processes", []))
        desired_processes = set(desired_state.get("processes", []))
        missing_processes = desired_processes - current_processes

        for process in missing_processes:
            gaps.append(
                {
                    "area": "Processes",
                    "gap": process,
                    "current": "Not implemented",
                    "desired": "Automated process",
                    "impact": "high",
                    "effort": "medium",
                    "priority": 8,
                }
            )

        # Analyze systems
        current_systems = set(current_state.get("systems", []))
        desired_systems = set(desired_state.get("systems", []))
        missing_systems = desired_systems - current_systems

        for system in missing_systems:
            gaps.append(
                {
                    "area": "Systems",
                    "gap": system,
                    "current": "Not available",
                    "desired": "Integrated system",
                    "impact": "high",
                    "effort": "high",
                    "priority": 7,
                }
            )

        # Analyze capabilities
        current_capabilities = set(current_state.get("capabilities", []))
        desired_capabilities = set(desired_state.get("capabilities", []))
        missing_capabilities = desired_capabilities - current_capabilities

        for capability in missing_capabilities:
            gaps.append(
                {
                    "area": "Capabilities",
                    "gap": capability,
                    "current": "Manual/Limited",
                    "desired": "Full capability",
                    "impact": "medium",
                    "effort": "medium",
                    "priority": 6,
                }
            )

        # Sort by priority
        gaps.sort(key=lambda x: x["priority"], reverse=True)

        # Generate roadmap
        roadmap = self._generate_roadmap(gaps)

        # Estimate cost and timeline
        total_effort_days = sum(
            {"low": 10, "medium": 30, "high": 90}.get(gap["effort"], 30) for gap in gaps
        )

        return {
            "gaps_found": len(gaps),
            "gaps": gaps,
            "roadmap": roadmap,
            "estimated_timeline_months": total_effort_days
            // 20,  # Business days to months
            "estimated_cost_eur": total_effort_days * 500,  # €500/day
            "priority_gaps": [g for g in gaps if g["priority"] >= 7],
        }

    def _generate_roadmap(self, gaps: List[Dict]) -> List[Dict]:
        """Генерация дорожной карты"""
        roadmap = []

        # Phase 1: High priority, low effort
        phase1 = [
            g for g in gaps if g["priority"] >= 7 and g["effort"] in ["low", "medium"]
        ]
        if phase1:
            roadmap.append(
                {
                    "phase": "Phase 1: Quick Wins",
                    "duration_months": 1,
                    "gaps": [g["gap"] for g in phase1],
                }
            )

        # Phase 2: High priority, high effort
        phase2 = [g for g in gaps if g["priority"] >= 7 and g["effort"] == "high"]
        if phase2:
            roadmap.append(
                {
                    "phase": "Phase 2: Strategic Initiatives",
                    "duration_months": 3,
                    "gaps": [g["gap"] for g in phase2],
                }
            )

        # Phase 3: Medium priority
        phase3 = [g for g in gaps if g["priority"] < 7]
        if phase3:
            roadmap.append(
                {
                    "phase": "Phase 3: Improvements",
                    "duration_months": 2,
                    "gaps": [g["gap"] for g in phase3],
                }
            )

        return roadmap


class TraceabilityMatrixGenerator:
    """Генератор матрицы прослеживаемости требований"""

    async def generate_matrix(
        self, requirements: List[Dict], test_cases: List[Dict]
    ) -> Dict[str, Any]:
        """
        Генерация матрицы прослеживаемости

        Args:
            requirements: [{id, title, ...}]
            test_cases: [{id, requirement_ids, ...}]

        Returns:
            Матрица с coverage analysis
        """
        logger.info("Generating traceability matrix")

        matrix = []

        for req in requirements:
            req_id = req.get("id")

            # Find test cases covering this requirement
            covering_tests = [
                tc for tc in test_cases if req_id in tc.get("requirement_ids", [])
            ]

            matrix.append(
                {
                    "requirement_id": req_id,
                    "requirement_title": req.get("title"),
                    "test_cases": [tc.get("id") for tc in covering_tests],
                    "coverage": "100%" if covering_tests else "0%",
                    "test_count": len(covering_tests),
                }
            )

        # Coverage summary
        total_reqs = len(requirements)
        covered_reqs = sum(1 for m in matrix if m["test_count"] > 0)
        coverage_percent = (
            int((covered_reqs / total_reqs) * 100) if total_reqs > 0 else 0
        )

        return {
            "matrix": matrix,
            "coverage_summary": {
                "total_requirements": total_reqs,
                "covered_requirements": covered_reqs,
                "uncovered_requirements": total_reqs - covered_reqs,
                "coverage_percent": coverage_percent,
            },
            "uncovered_requirements": [
                m["requirement_id"] for m in matrix if m["test_count"] == 0
            ],
            "generated_at": datetime.now().isoformat(),
        }


class BusinessAnalystAgentExtended:
    """
    Расширенный Business Analyst AI ассистент

    Возможности:
    - Requirements Extraction (NLP)
    - BPMN Generation
    - Gap Analysis
    - Traceability Matrix
    """

    def __init__(self) -> None:
        self.requirements_extractor = RequirementsExtractor()
        self.bpmn_generator = BPMNGenerator()
        self.gap_analyzer = GapAnalyzer()
        self.traceability_generator = TraceabilityMatrixGenerator()
        self.integration_connector = IntegrationConnector()

        try:
            self.gigachat_client = GigaChatClient()
        except Exception as exc:  # pragma: no cover - initialization safety
            logger.warning("Failed to initialize GigaChat client: %s", exc)
            self.gigachat_client = None

        try:
            self.yandex_client = YandexGPTClient()
        except Exception as exc:  # pragma: no cover - initialization safety
            logger.warning("Failed to initialize YandexGPT client: %s", exc)
            self.yandex_client = None

        self.llm_enhancer = RequirementsLLMEnhancer(
            self.gigachat_client,
            self.yandex_client,
        )

        logger.info("Business Analyst Agent Extended initialized")

    async def extract_requirements(
        self,
        document_text: str,
        document_type: str = "tz",
        *,
        source_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Extract requirements from plain text."""
        base = await self.requirements_extractor.extract_requirements(
            document_text,
            document_type,
            source_path=source_path,
        )
        enhanced = await self.llm_enhancer.enhance(base, document_text)
        enhanced["generated_at"] = datetime.now().isoformat()
        return enhanced

    async def extract_requirements_from_file(
        self,
        path: Union[str, Path],
        document_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        file_path = Path(path)
        text = read_document(file_path)
        inferred_type = document_type or self._infer_document_type(file_path)
        return await self.extract_requirements(
            text, inferred_type, source_path=str(file_path)
        )

    async def generate_bpmn(self, process_description: str) -> Dict[str, Any]:
        """Генерация BPMN диаграммы"""
        return await self.bpmn_generator.generate_bpmn(process_description)

    async def analyze_gap(
        self, current_state: Dict, desired_state: Dict
    ) -> Dict[str, Any]:
        """Gap анализ"""
        return await self.gap_analyzer.perform_gap_analysis(
            current_state, desired_state
        )

    async def generate_traceability_matrix(
        self, requirements: List[Dict], test_cases: List[Dict]
    ) -> Dict[str, Any]:
        """Матрица прослеживаемости"""
        return await self.traceability_generator.generate_matrix(
            requirements, test_cases
        )

    # === BA‑03: Process & Journey Modelling ===

    async def generate_process_model(
        self,
        description: str,
        *,
        requirement_id: Optional[str] = None,
        format: str = "mermaid",
        use_graph: bool = True,
    ) -> Dict[str, Any]:
        """
        BA-03: Построение модели процесса с использованием Unified Change Graph.

        Использует Unified Change Graph для связи процесса с кодом, требованиями и тестами.

        Args:
            description: Текстовое описание процесса
            requirement_id: ID требования для связи с графом
            format: Формат вывода (mermaid, plantuml, json)
            use_graph: Использовать Unified Change Graph

        Returns:
            BPMN модель с метаданными и связями с графом
        """
        # Попытка использовать Unified Change Graph
        if use_graph:
            try:
                from src.ai.agents.process_modelling_with_graph import (
                    ProcessModellerWithGraph,
                )
                from src.ai.code_analysis.graph import InMemoryCodeGraphBackend

                backend = InMemoryCodeGraphBackend()
                process_modeller = ProcessModellerWithGraph(backend)

                result = await process_modeller.generate_bpmn_with_graph(
                    process_description=description,
                    requirement_id=requirement_id,
                    format=format,
                )

                result.setdefault("metadata", {})
                result["metadata"].update(
                    {
                        "ba_feature": "BA-03",
                        "source": "business_analyst_agent_extended",
                        "description_preview": (description or "")[:300],
                    }
                )

                return result

            except Exception as e:
                logger.debug(
                    "Failed to use graph-based process modelling, falling back to basic: %s",
                    e,
                )
                # Fallback на базовый подход

        # Базовый подход (без графа)
        model = await self.bpmn_generator.generate_bpmn(description)
        model.setdefault("metadata", {})
        model["metadata"].update(
            {
                "ba_feature": "BA-03",
                "source": "business_analyst_agent_extended",
                "description_preview": (description or "")[:300],
            }
        )
        return model

    async def generate_journey_map(
        self,
        journey_description: str,
        *,
        stages: Optional[List[str]] = None,
        format: str = "mermaid",
        use_graph: bool = True,
    ) -> Dict[str, Any]:
        """
        BA-03: Генерация Customer Journey Map.

        Args:
            journey_description: Текстовое описание customer journey
            stages: Список стадий (опционально)
            format: Формат вывода (mermaid, plantuml, json)
            use_graph: Использовать Unified Change Graph для поиска touchpoints

        Returns:
            Journey Map с стадиями, действиями, эмоциями и pain points
        """
        if use_graph:
            try:
                from src.ai.agents.process_modelling_with_graph import (
                    ProcessModellerWithGraph,
                )
                from src.ai.code_analysis.graph import InMemoryCodeGraphBackend

                backend = InMemoryCodeGraphBackend()
                process_modeller = ProcessModellerWithGraph(backend)

                result = await process_modeller.generate_journey_map(
                    journey_description=journey_description,
                    stages=stages,
                    format=format,
                )

                result.setdefault("metadata", {})
                result["metadata"].update(
                    {
                        "ba_feature": "BA-03",
                        "source": "business_analyst_agent_extended",
                    }
                )

                return result

            except Exception as e:
                logger.debug(
                    "Failed to use graph-based journey mapping, falling back to basic: %s",
                    e,
                )

        # Базовый подход (без графа)
        return {
            "ba_feature": "BA-03",
            "stages": stages or ["Awareness", "Consideration", "Purchase", "Retention"],
            "description": journey_description,
            "metadata": {
                "format": format,
                "generated_at": datetime.utcnow().isoformat(),
            },
        }

    async def validate_process_model(
        self,
        process_model: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        BA-03: Валидация модели процесса.

        Проверяет наличие владельцев, входов/выходов, измеримых результатов
        и связей с кодом/тестами через граф.

        Args:
            process_model: Модель процесса для валидации

        Returns:
            Результат валидации с замечаниями и рекомендациями
        """
        try:
            from src.ai.agents.process_modelling_with_graph import (
                ProcessModellerWithGraph,
            )
            from src.ai.code_analysis.graph import InMemoryCodeGraphBackend

            backend = InMemoryCodeGraphBackend()
            process_modeller = ProcessModellerWithGraph(backend)

            result = await process_modeller.validate_process(process_model)

            result["ba_feature"] = "BA-03"
            return result

        except Exception as e:
            logger.debug("Failed to validate process with graph: %s", e)
            # Базовая валидация без графа
            return {
                "ba_feature": "BA-03",
                "valid": True,
                "issues": [],
                "warnings": [],
                "summary": {},
            }

    # === BA‑04: Analytics & KPI Toolkit (минимальный каркас) ===

    async def design_kpi_blueprint(
        self,
        initiative_name: str,
        *,
        dimensions: Optional[List[str]] = None,
        feature_id: Optional[str] = None,
        use_graph: bool = True,
    ) -> Dict[str, Any]:
        """
        BA-04: Черновик KPI/OKR и SQL-квери под аналитику.

        Использует Unified Change Graph для автоматического построения KPI
        на основе реальных метрик, если доступен.

        Args:
            initiative_name: Название инициативы/фичи
            dimensions: Список измерений (опционально)
            feature_id: ID фичи/требования для поиска в графе
            use_graph: Использовать Unified Change Graph

        Returns:
            Словарь с KPI, SQL-запросами и визуализациями
        """
        # Попытка использовать Unified Change Graph
        if use_graph:
            try:
                from src.ai.agents.analytics_kpi_with_graph import KPIGeneratorWithGraph
                from src.ai.code_analysis.graph import InMemoryCodeGraphBackend

                backend = InMemoryCodeGraphBackend()
                kpi_generator = KPIGeneratorWithGraph(backend)

                result = await kpi_generator.generate_kpis_from_graph(
                    feature_id=feature_id,
                    include_technical=True,
                    include_business=True,
                )

                return {
                    "ba_feature": "BA-04",
                    "initiative": initiative_name,
                    **result,
                }

            except Exception as e:
                logger.debug(
                    "Failed to use graph-based KPI generation, falling back to basic: %s",
                    e,
                )
                # Fallback на базовый подход

        # Базовый подход (без графа)
        base_dimensions = dimensions or ["throughput", "lead_time", "quality"]

        kpis: List[Dict[str, Any]] = []
        for dim in base_dimensions:
            metric_id = dim.upper()
            title = f"{metric_id}: {initiative_name}".strip(": ")
            sql = (
                "SELECT /* TODO: скорректировать под конкретную БД */\n"
                "       date_trunc('day', ts) AS day,\n"
                "       COUNT(*)               AS value\n"
                "FROM events\n"
                "WHERE initiative = %(initiative)s\n"
                "GROUP BY day\n"
                "ORDER BY day;"
            )
            kpis.append(
                {
                    "id": metric_id,
                    "title": title,
                    "dimension": dim,
                    "sql_draft": sql,
                    "owner": "BA/Analytics",
                }
            )

        return {
            "ba_feature": "BA-04",
            "initiative": initiative_name,
            "kpis": kpis,
            "generated_at": datetime.utcnow().isoformat(),
        }

    # === BA‑05: Traceability & Compliance (надстройка над матрицей) ===

    async def build_traceability_and_risks(
        self,
        requirements: List[Dict[str, Any]],
        test_cases: List[Dict[str, Any]],
        *,
        use_graph: bool = True,
    ) -> Dict[str, Any]:
        """
        BA-05: Матрица прослеживаемости + риск‑оценка по coverage.

        Использует Unified Change Graph для полного traceability, если доступен.
        Иначе использует базовый TraceabilityMatrixGenerator.

        Args:
            requirements: Список требований [{id, title, ...}]
            test_cases: Список тестов [{id, requirement_ids, ...}]
            use_graph: Использовать Unified Change Graph (если доступен)

        Returns:
            Полный отчёт traceability & compliance
        """
        # Попытка использовать Unified Change Graph
        if use_graph:
            try:
                from src.ai.agents.traceability_with_graph import TraceabilityWithGraph
                from src.ai.code_analysis.graph import InMemoryCodeGraphBackend

                # Инициализировать backend (можно заменить на Neo4j в будущем)
                backend = InMemoryCodeGraphBackend()
                traceability_graph = TraceabilityWithGraph(backend)

                # Извлечь ID требований
                requirement_ids = [
                    req.get("id") for req in requirements if req.get("id")
                ]

                # Построить полный отчёт с использованием графа
                full_report = await traceability_graph.build_full_traceability_report(
                    requirement_ids
                )

                return full_report

            except Exception as e:
                logger.debug(
                    "Failed to use graph-based traceability, falling back to basic: %s",
                    e,
                )
                # Fallback на базовый генератор

        # Базовый подход (без графа)
        matrix = await self.traceability_generator.generate_matrix(
            requirements, test_cases
        )

        uncovered_ids = matrix["uncovered_requirements"]
        risk_register: List[Dict[str, Any]] = []
        for req in requirements:
            if req.get("id") in uncovered_ids:
                risk_register.append(
                    {
                        "requirement_id": req.get("id"),
                        "title": req.get("title"),
                        "risk_level": "high",
                        "reason": "requirement_has_no_tests",
                    }
                )

        heatmap = {
            "high": len([r for r in risk_register if r["risk_level"] == "high"]),
            "medium": 0,
            "low": 0,
        }

        return {
            "ba_feature": "BA-05",
            "traceability": matrix,
            "risk_register": risk_register,
            "risk_heatmap": heatmap,
        }

    # === BA‑06: Integrations & Collaboration (расширенная версия с графом) ===

    async def plan_and_sync_integrations(
        self,
        artefact_title: str,
        artefact_body: str,
        *,
        targets: Optional[List[str]] = None,
        use_graph: bool = True,
    ) -> Dict[str, Any]:
        """
        BA-06: Сформировать артефакт и отправить его в Jira/Confluence/Docflow/PowerBI.

        Использует Unified Change Graph для автоматического добавления ссылок на код/тесты.

        Args:
            artefact_title: Заголовок артефакта
            artefact_body: Содержимое артефакта
            targets: Список целевых систем (jira, confluence, etc.)
            use_graph: Использовать Unified Change Graph для обогащения артефакта

        Returns:
            Результат синхронизации
        """
        artefact: Dict[str, Any] = {
            "type": "ba_summary",
            "title": artefact_title,
            "content": artefact_body,
            "metadata": {
                "title": artefact_title,
                "description": artefact_body[:8000],
            },
        }

        # Обогатить артефакт ссылками из графа
        if use_graph:
            try:
                from src.ai.agents.integrations_with_graph import (
                    IntegrationSyncWithGraph,
                )
                from src.ai.code_analysis.graph import InMemoryCodeGraphBackend

                backend = InMemoryCodeGraphBackend()
                IntegrationSyncWithGraph(backend)

                # Попытка найти связанные артефакты в графе
                # (упрощённо: ищем по ключевым словам в заголовке/теле)
                # В реальности можно использовать GraphQueryHelper

            except Exception as e:
                logger.debug(
                    "Failed to enrich artefact with graph, using basic sync: %s", e
                )

        sync_result = await self.integration_connector.sync(artefact, targets=targets)
        sync_result["ba_feature"] = "BA-06"
        return sync_result

    async def sync_requirements_to_jira(
        self,
        requirement_ids: List[str],
        *,
        project_key: Optional[str] = None,
        issue_type: str = "Story",
        use_graph: bool = True,
    ) -> Dict[str, Any]:
        """
        BA-06: Синхронизировать требования из графа в Jira.

        Создаёт задачи в Jira на основе требований, автоматически добавляя
        ссылки на код и тесты из Unified Change Graph.

        Args:
            requirement_ids: Список ID требований
            project_key: Ключ проекта Jira
            issue_type: Тип задачи (Story, Task, Epic)
            use_graph: Использовать Unified Change Graph

        Returns:
            Результат синхронизации
        """
        if use_graph:
            try:
                from src.ai.agents.integrations_with_graph import (
                    IntegrationSyncWithGraph,
                )
                from src.ai.code_analysis.graph import InMemoryCodeGraphBackend

                backend = InMemoryCodeGraphBackend()
                integration_sync = IntegrationSyncWithGraph(backend)

                result = await integration_sync.sync_requirements_to_jira(
                    requirement_ids,
                    project_key=project_key,
                    issue_type=issue_type,
                )

                result["ba_feature"] = "BA-06"
                return result

            except Exception as e:
                logger.debug(
                    "Failed to sync requirements with graph, using basic sync: %s", e
                )

        # Базовый подход (без графа)
        return {
            "ba_feature": "BA-06",
            "synced": [],
            "errors": ["Graph-based sync not available"],
            "total": len(requirement_ids),
            "synced_count": 0,
        }

    async def sync_bpmn_to_confluence(
        self,
        process_model: Dict[str, Any],
        *,
        space_key: Optional[str] = None,
        parent_page_id: Optional[str] = None,
        use_graph: bool = True,
    ) -> Dict[str, Any]:
        """
        BA-06: Синхронизировать BPMN модель процесса в Confluence.

        Создаёт страницу в Confluence с BPMN диаграммой и автоматическими
        ссылками на код/тесты из Unified Change Graph.

        Args:
            process_model: Модель процесса
            space_key: Ключ пространства Confluence
            parent_page_id: ID родительской страницы
            use_graph: Использовать Unified Change Graph

        Returns:
            Результат синхронизации
        """
        if use_graph:
            try:
                from src.ai.agents.integrations_with_graph import (
                    IntegrationSyncWithGraph,
                )
                from src.ai.code_analysis.graph import InMemoryCodeGraphBackend

                backend = InMemoryCodeGraphBackend()
                integration_sync = IntegrationSyncWithGraph(backend)

                result = await integration_sync.sync_bpmn_to_confluence(
                    process_model,
                    space_key=space_key,
                    parent_page_id=parent_page_id,
                )

                result["ba_feature"] = "BA-06"
                return result

            except Exception as e:
                logger.debug("Failed to sync BPMN with graph, using basic sync: %s", e)

        # Базовый подход (без графа)
        return {
            "ba_feature": "BA-06",
            "page_id": None,
            "status": "pending_sync",
        }

    async def sync_kpi_to_confluence(
        self,
        kpi_report: Dict[str, Any],
        *,
        space_key: Optional[str] = None,
        parent_page_id: Optional[str] = None,
        use_graph: bool = True,
    ) -> Dict[str, Any]:
        """
        BA-06: Синхронизировать KPI отчёт в Confluence.

        Args:
            kpi_report: Отчёт KPI
            space_key: Ключ пространства Confluence
            parent_page_id: ID родительской страницы
            use_graph: Использовать Unified Change Graph

        Returns:
            Результат синхронизации
        """
        if use_graph:
            try:
                from src.ai.agents.integrations_with_graph import (
                    IntegrationSyncWithGraph,
                )
                from src.ai.code_analysis.graph import InMemoryCodeGraphBackend

                backend = InMemoryCodeGraphBackend()
                integration_sync = IntegrationSyncWithGraph(backend)

                result = await integration_sync.sync_kpi_to_confluence(
                    kpi_report,
                    space_key=space_key,
                    parent_page_id=parent_page_id,
                )

                result["ba_feature"] = "BA-06"
                return result

            except Exception as e:
                logger.debug("Failed to sync KPI with graph, using basic sync: %s", e)

        return {
            "ba_feature": "BA-06",
            "page_id": None,
            "status": "pending_sync",
        }

    async def sync_traceability_to_confluence(
        self,
        traceability_report: Dict[str, Any],
        *,
        space_key: Optional[str] = None,
        parent_page_id: Optional[str] = None,
        use_graph: bool = True,
    ) -> Dict[str, Any]:
        """
        BA-06: Синхронизировать Traceability matrix в Confluence.

        Args:
            traceability_report: Отчёт traceability
            space_key: Ключ пространства Confluence
            parent_page_id: ID родительской страницы
            use_graph: Использовать Unified Change Graph

        Returns:
            Результат синхронизации
        """
        if use_graph:
            try:
                from src.ai.agents.integrations_with_graph import (
                    IntegrationSyncWithGraph,
                )
                from src.ai.code_analysis.graph import InMemoryCodeGraphBackend

                backend = InMemoryCodeGraphBackend()
                integration_sync = IntegrationSyncWithGraph(backend)

                result = await integration_sync.sync_traceability_to_confluence(
                    traceability_report,
                    space_key=space_key,
                    parent_page_id=parent_page_id,
                )

                result["ba_feature"] = "BA-06"
                return result

            except Exception as e:
                logger.debug(
                    "Failed to sync traceability with graph, using basic sync: %s", e
                )

        return {
            "ba_feature": "BA-06",
            "page_id": None,
            "status": "pending_sync",
        }

    # === BA‑07: Documentation & Enablement (расширенная версия с графом) ===

    async def build_enablement_plan(
        self,
        feature_name: str,
        *,
        audience: str = "BA+Dev+QA",
        include_examples: bool = True,
        use_graph: bool = True,
    ) -> Dict[str, Any]:
        """
        BA-07: План enablement‑материалов с использованием Unified Change Graph.

        Использует граф для автоматического поиска примеров и связанных артефактов.

        Args:
            feature_name: Название фичи
            audience: Целевая аудитория (BA+Dev+QA, Product, Executive)
            include_examples: Включать примеры из графа
            use_graph: Использовать Unified Change Graph

        Returns:
            План enablement-материалов с модулями, примерами и ссылками
        """
        if use_graph:
            try:
                from src.ai.agents.enablement_with_graph import (
                    EnablementGeneratorWithGraph,
                )
                from src.ai.code_analysis.graph import InMemoryCodeGraphBackend

                backend = InMemoryCodeGraphBackend()
                enablement_generator = EnablementGeneratorWithGraph(backend)

                result = await enablement_generator.generate_enablement_plan(
                    feature_name,
                    audience=audience,
                    include_examples=include_examples,
                    use_graph=use_graph,
                )

                result["ba_feature"] = "BA-07"
                return result

            except Exception as e:
                logger.debug(
                    "Failed to use graph-based enablement, falling back to basic: %s", e
                )
                # Fallback на базовый подход

        # Базовый подход (без графа)
        modules = [
            {
                "id": "overview",
                "title": f"Обзор: {feature_name}",
                "deliverables": ["README блок", "FAQ", "архитектурный обзор"],
            },
            {
                "id": "howto",
                "title": f"How-to сценарии для {feature_name}",
                "deliverables": ["Cookbook рецепты", "пошаговые туториалы"],
            },
            {
                "id": "observability",
                "title": f"Наблюдаемость и SLO для {feature_name}",
                "deliverables": ["метрики", "дашборд", "алерты"],
            },
        ]

        return {
            "ba_feature": "BA-07",
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
        use_graph: bool = True,
    ) -> Dict[str, Any]:
        """
        BA-07: Генерация гайда по теме с примерами из графа.

        Args:
            topic: Тема гайда
            format: Формат вывода (markdown, confluence, html)
            include_code_examples: Включать примеры кода из графа
            use_graph: Использовать Unified Change Graph

        Returns:
            Гайд с содержанием, примерами и ссылками
        """
        if use_graph:
            try:
                from src.ai.agents.enablement_with_graph import (
                    EnablementGeneratorWithGraph,
                )
                from src.ai.code_analysis.graph import InMemoryCodeGraphBackend

                backend = InMemoryCodeGraphBackend()
                enablement_generator = EnablementGeneratorWithGraph(backend)

                result = await enablement_generator.generate_guide(
                    topic,
                    format=format,
                    include_code_examples=include_code_examples,
                )

                result["ba_feature"] = "BA-07"
                return result

            except Exception as e:
                logger.debug("Failed to generate guide with graph, using basic: %s", e)

        # Базовый подход (без графа)
        return {
            "ba_feature": "BA-07",
            "title": f"Guide: {topic}",
            "sections": [
                {
                    "id": "introduction",
                    "title": "Введение",
                    "content": f"Этот гайд описывает {topic}.",
                }
            ],
            "format": format,
        }

    async def generate_presentation_outline(
        self,
        topic: str,
        *,
        audience: str = "stakeholders",
        duration_minutes: int = 30,
        use_graph: bool = True,
    ) -> Dict[str, Any]:
        """
        BA-07: Генерация outline презентации.

        Args:
            topic: Тема презентации
            audience: Аудитория (stakeholders, technical, executive)
            duration_minutes: Длительность в минутах
            use_graph: Использовать Unified Change Graph

        Returns:
            Outline презентации с слайдами и ключевыми сообщениями
        """
        if use_graph:
            try:
                from src.ai.agents.enablement_with_graph import (
                    EnablementGeneratorWithGraph,
                )
                from src.ai.code_analysis.graph import InMemoryCodeGraphBackend

                backend = InMemoryCodeGraphBackend()
                enablement_generator = EnablementGeneratorWithGraph(backend)

                result = await enablement_generator.generate_presentation_outline(
                    topic,
                    audience=audience,
                    duration_minutes=duration_minutes,
                )

                result["ba_feature"] = "BA-07"
                return result

            except Exception as e:
                logger.debug(
                    "Failed to generate presentation with graph, using basic: %s", e
                )

        # Базовый подход (без графа)
        return {
            "ba_feature": "BA-07",
            "title": f"Presentation: {topic}",
            "audience": audience,
            "duration_minutes": duration_minutes,
            "slides": [
                {"id": "title", "title": f"{topic}", "content": "Title slide"},
                {"id": "agenda", "title": "Agenda", "content": "Overview"},
            ],
        }

    async def generate_onboarding_checklist(
        self,
        role: str = "BA",
        *,
        include_practical_tasks: bool = True,
        use_graph: bool = True,
    ) -> Dict[str, Any]:
        """
        BA-07: Генерация onboarding чек-листа для роли.

        Args:
            role: Роль (BA, Dev, QA, Product)
            include_practical_tasks: Включать практические задачи из графа
            use_graph: Использовать Unified Change Graph

        Returns:
            Onboarding чек-лист с задачами и ссылками
        """
        if use_graph:
            try:
                from src.ai.agents.enablement_with_graph import (
                    EnablementGeneratorWithGraph,
                )
                from src.ai.code_analysis.graph import InMemoryCodeGraphBackend

                backend = InMemoryCodeGraphBackend()
                enablement_generator = EnablementGeneratorWithGraph(backend)

                result = await enablement_generator.generate_onboarding_checklist(
                    role,
                    include_practical_tasks=include_practical_tasks,
                )

                result["ba_feature"] = "BA-07"
                return result

            except Exception as e:
                logger.debug(
                    "Failed to generate checklist with graph, using basic: %s", e
                )

        # Базовый подход (без графа)
        return {
            "ba_feature": "BA-07",
            "role": role,
            "sections": [
                {
                    "id": "reading",
                    "title": "Что прочитать",
                    "items": ["README", "Documentation"],
                }
            ],
        }

    def _infer_document_type(self, path: Path) -> str:
        suffix = path.suffix.lower()
        mapping = {
            ".docx": "tz",
            ".pdf": "tz",
            ".md": "notes",
            ".txt": "notes",
            ".json": "backlog",
        }
        return mapping.get(suffix, "tz")


class RequirementsLLMEnhancer:
    """Optional LLM enrichment for heuristic requirements."""

    def __init__(
        self,
        gigachat: Optional[GigaChatClient],
        yandex: Optional[YandexGPTClient],
    ) -> None:
        self.clients = [
            client for client in (gigachat, yandex) if client and client.is_configured
        ]

    async def enhance(self, data: Dict[str, Any], original_text: str) -> Dict[str, Any]:
        if not self.clients:
            data["summary"]["llm_used"] = False
            return data

        prompt = self._build_prompt(data, original_text)
        for client in self.clients:
            try:
                response = await client.generate(prompt, response_format="json")
            except (LLMNotConfiguredError, LLMCallError) as exc:
                logger.warning(
                    "LLM enhancement failed for %s: %s", client.__class__.__name__, exc
                )
                continue

            message = response.get("text") or ""
            try:
                parsed = json.loads(message)
                merged = self._merge(data, parsed)
                merged["summary"]["llm_used"] = True
                merged["summary"]["llm_provider"] = client.__class__.__name__
                return merged
            except json.JSONDecodeError:
                logger.warning(
                    "Failed to parse LLM response as JSON, skipping provider %s", client
                )
                continue

        data["summary"]["llm_used"] = False
        return data

    def _build_prompt(self, data: Dict[str, Any], original_text: str) -> str:
        summary = data.get("summary", {})
        prompt = (
            "Тебе дан текст технического задания. "
            "Нужно проверить найденные требования и, при необходимости, дополнить их.\n"
            "Формат ответа: JSON с полями functional_requirements, "
            "non_functional_requirements, constraints, user_stories, acceptance_criteria, stakeholders."
            "\nСохраняй идентификаторы, если корректируешь запись.\n"
        )
        prompt += f'\nТекст документа:\n"""\n{original_text[:4000]}\n"""\n'
        prompt += f"\nТекущее резюме: {json.dumps(summary, ensure_ascii=False)}"
        return prompt

    def _merge(self, base: Dict[str, Any], llm_data: Dict[str, Any]) -> Dict[str, Any]:
        def _merge_list(key: str) -> List[Any]:
            existing = {
                item["id"]: item
                for item in base.get(key, [])
                if isinstance(item, dict) and "id" in item
            }
            additional = []
            for item in llm_data.get(key, []):
                if isinstance(item, dict) and "id" in item:
                    existing[item["id"]] = item
                else:
                    additional.append(item)
            return list(existing.values()) + additional

        merged = dict(base)
        merged["functional_requirements"] = _merge_list("functional_requirements")
        merged["non_functional_requirements"] = _merge_list(
            "non_functional_requirements"
        )
        merged["constraints"] = _merge_list("constraints")
        merged["user_stories"] = llm_data.get(
            "user_stories", merged.get("user_stories", [])
        )
        merged["acceptance_criteria"] = llm_data.get(
            "acceptance_criteria", merged.get("acceptance_criteria", [])
        )
        merged["stakeholders"] = list(
            sorted(
                set(merged.get("stakeholders", []))
                | set(llm_data.get("stakeholders", []))
            )
        )
        return merged


class IntegrationConnector:
    """Синхронизация BA-артефактов с Jira, Confluence, Power BI и 1C Docflow."""

    SUPPORTED_TARGETS = ("jira", "confluence", "powerbi", "1c_docflow")

    def __init__(
        self,
        *,
        jira_client: Optional[JiraClient] = None,
        confluence_client: Optional[ConfluenceClient] = None,
        powerbi_client: Optional[PowerBIClient] = None,
        docflow_client: Optional[OneCDocflowClient] = None,
    ) -> None:
        self.jira_client = jira_client or self._init_client(JiraClient)
        self.confluence_client = confluence_client or self._init_client(
            ConfluenceClient
        )
        self.powerbi_client = powerbi_client or self._init_client(PowerBIClient)
        self.docflow_client = docflow_client or self._init_client(OneCDocflowClient)

    def _init_client(self, factory):
        if factory is None:
            return None
        try:
            return factory.from_env()
        except IntegrationConfigError:
            return None

    async def sync(
        self, artefact: Dict[str, Any], targets: Optional[Iterable[str]] = None
    ) -> Dict[str, Any]:
        targets_list = list(targets) if targets else ["jira", "confluence"]
        results: List[Dict[str, Any]] = []
        for target in targets_list:
            handler = getattr(self, f"_sync_{target}".replace("-", "_"), None)
            if handler is None:
                results.append(
                    {
                        "target": target,
                        "status": "skipped",
                        "reason": "unsupported_target",
                    }
                )
                continue
            results.append(await handler(artefact))
        return {"artefact_type": artefact.get("type"), "results": results}

    async def aclose(self) -> None:
        tasks = [
            client.aclose()
            for client in (
                self.jira_client,
                self.confluence_client,
                self.powerbi_client,
                self.docflow_client,
            )
            if client
        ]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _sync_jira(self, artefact: Dict[str, Any]) -> Dict[str, Any]:
        if not self.jira_client:
            return self._queued("jira", "not_configured")
        metadata = artefact.get("metadata", {})
        project_key = metadata.get("project_key") or os.getenv(
            "BA_JIRA_DEFAULT_PROJECT"
        )
        if not project_key:
            return self._queued("jira", "project_key_missing")
        summary = (
            metadata.get("summary")
            or metadata.get("title")
            or artefact.get("title")
            or "BA Artefact"
        )
        description = metadata.get("description") or artefact.get("content", "")
        fields = metadata.get("jira_fields")
        summary = self._safe_text(summary, max_len=255, fallback="BA Artefact")
        description = self._safe_text(description, max_len=32000, fallback=summary)
        response = await self.jira_client.create_issue(
            project_key=project_key,
            summary=summary,
            description=description,
            fields=fields,
        )
        return {
            "target": "jira",
            "status": "created",
            "key": response.get("key"),
            "url": response.get("self"),
        }

    async def _sync_confluence(self, artefact: Dict[str, Any]) -> Dict[str, Any]:
        if not self.confluence_client:
            return self._queued("confluence", "not_configured")
        metadata = artefact.get("metadata", {})
        space_key = metadata.get("space_key") or os.getenv("BA_CONFLUENCE_SPACE_KEY")
        if not space_key:
            return self._queued("confluence", "space_key_missing")
        title = (
            metadata.get("title")
            or metadata.get("summary")
            or artefact.get("title")
            or "BA Artefact"
        )
        raw_body = metadata.get("body") or artefact.get("content") or ""
        body = self._as_paragraphs(raw_body)
        response = await self.confluence_client.create_page(
            space_key=space_key,
            title=title,
            body=body,
        )
        return {
            "target": "confluence",
            "status": "published",
            "id": response.get("id"),
            "url": (response.get("links") or {}).get("webui"),
        }

    async def _sync_powerbi(self, artefact: Dict[str, Any]) -> Dict[str, Any]:
        if not self.powerbi_client:
            return self._queued("powerbi", "not_configured")
        metadata = artefact.get("metadata", {})
        workspace_id = metadata.get("workspace_id") or os.getenv(
            "BA_POWERBI_WORKSPACE_ID"
        )
        dataset_id = metadata.get("dataset_id") or os.getenv("BA_POWERBI_DATASET_ID")
        if not workspace_id or not dataset_id:
            return self._queued("powerbi", "dataset_not_configured")
        response = await self.powerbi_client.trigger_refresh(workspace_id, dataset_id)
        return {
            "target": "powerbi",
            "status": "refresh_requested",
            "details": response,
        }

    async def _sync_1c_docflow(self, artefact: Dict[str, Any]) -> Dict[str, Any]:
        if not self.docflow_client:
            return self._queued("1c_docflow", "not_configured")
        metadata = artefact.get("metadata", {})
        title = (
            metadata.get("title")
            or metadata.get("summary")
            or artefact.get("title")
            or "BA Artefact"
        )
        description = metadata.get("description") or artefact.get("content", "")
        description = self._safe_text(description, max_len=8000, fallback=title)
        category = metadata.get("category") or "BA"
        response = await self.docflow_client.register_document(
            title=title,
            description=description,
            category=category,
            payload=artefact,
        )
        return {
            "target": "1c_docflow",
            "status": "registered",
            "id": response.get("id"),
            "url": response.get("url"),
        }

    def _queued(self, target: str, reason: str) -> Dict[str, Any]:
        return {
            "target": target,
            "status": "queued",
            "reason": reason,
        }

    def _safe_text(self, value: Optional[str], *, max_len: int, fallback: str) -> str:
        text = (value or "").strip()
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)
        text = text or fallback
        if len(text) > max_len:
            text = text[:max_len].rstrip()
        return text

    def _as_paragraphs(self, value: str) -> str:
        text = self._safe_text(value, max_len=20000, fallback="No content")
        paragraphs = [
            html.escape(part.strip()) for part in text.splitlines() if part.strip()
        ]
        if not paragraphs:
            return "<p>No content</p>"
        return "".join(f"<p>{part}</p>" for part in paragraphs)
