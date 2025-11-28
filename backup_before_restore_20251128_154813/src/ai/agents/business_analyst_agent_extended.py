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

from src.ai.clients import (GigaChatClient, LLMCallError,
                            LLMNotConfiguredError, YandexGPTClient)
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
        return [{"type": "functional",
                 "patterns": [r"система должна\s+(?P<body>.+)",
                              r"необходимо\s+(?P<body>.+)",
                              r"должен(?:а|о|ы)?\s+обеспечивать\s+(?P<body>.+)",
                              r"требуется\s+(?P<body>.+)",
                              r"пользователь\s+(?:может|должен)\s+(?P<body>.+)",
                              ],
                 },
                {"type": "non_functional",
                 "patterns": [r"производительность[:\s]+(?P<body>.+)",
                              r"(?:время|скорость)\s+(?:отклика|выполнения)[:\s]+(?P<body>.+)",
                              r"(?:количество|число)\s+пользователей[:\s]+(?P<body>.+)",
                              r"(?:доступность|uptime)[:\s]+(?P<body>.+)",
                              r"безопасность[:\s]+(?P<body>.+)",
                              ],
                 },
                {"type": "constraint",
                 "patterns": [r"ограничение[:\s]+(?P<body>.+)",
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
            "Extracting requirements (heuristics) for document type %s",
            document_type)

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
                    list_match = re.match(
                        r"^\d+[\.\)]\s+(?P<body>.+)", candidate)
                    if list_match:
                        body = list_match.group("body")
                        functional.append(
                            self._build_requirement(
                                "functional",
                                body,
                                candidate,
                                sentence_index=idx))
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
                list_match = re.match(
                    r"^\d+[\.\)]\s*(?P<body>.+)", cleaned_line)
                keyword_match = re.search(
                    r"(должн|необходимо|требуется)",
                    cleaned_line,
                    re.IGNORECASE)
                body = None
                if list_match:
                    body = list_match.group("body")
                elif keyword_match:
                    body = cleaned_line.split(
                        ":", 1)[-1].strip() or cleaned_line
                if body:
                    functional.append(
                        self._build_requirement(
                            "functional",
                            body,
                            cleaned_line,
                            sentence_index=idx))

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

        prefix = {
            "functional": "FR",
            "non_functional": "NFR",
            "constraint": "CON"}[req_type]
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
        found = {title.capitalize()
                 for title in titles if title in text.lower()}
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

    def _extract_decision_points(
            self, description: str) -> List[Dict[str, Any]]:
        decisions: List[Dict[str, Any]] = []
        patterns = [
            r"если\s+(.+?)\s+,?\s+то",
            r"в случае\s+(.+?)\s+,?\s+(?:выполняется|происходит)",
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, description, re.IGNORECASE)
            for match in matches:
                decisions.append(
                    {"condition": match.group(1), "type": "decision"})

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
        total_effort_days = sum({"low": 10, "medium": 30, "high": 90}.get(
            gap["effort"], 30) for gap in gaps)

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
        phase1 = [g for g in gaps if g["priority"] >=
                  7 and g["effort"] in ["low", "medium"]]
        if phase1:
            roadmap.append(
                {
                    "phase": "Phase 1: Quick Wins",
                    "duration_months": 1,
                    "gaps": [g["gap"] for g in phase1],
                }
            )

        # Phase 2: High priority, high effort
        phase2 = [g for g in gaps if g["priority"]
                  >= 7 and g["effort"] == "high"]
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
                tc for tc in test_cases if req_id in tc.get(
                    "requirement_ids", [])]

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
