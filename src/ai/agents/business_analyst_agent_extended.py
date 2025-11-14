"""
Business Analyst AI Agent Extended.

Provides requirement extraction, BPMN generation, gap analysis and traceability
with optional LLM-based refinement (GigaChat / YandexGPT).
"""

from __future__ import annotations

import json
import logging
import os
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from src.ai.clients import GigaChatClient, LLMCallError, LLMNotConfiguredError, YandexGPTClient
from src.ai.utils.document_loader import read_document

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
        logger.info("Extracting requirements (heuristics) for document type %s", document_type)

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
                    requirement = self._build_requirement(req_type, body, cleaned, sentence_index=idx)
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

        stakeholders = self._extract_stakeholders(document_text)
        acceptance_criteria = self._extract_acceptance_criteria(document_text)
        user_stories = self._extract_user_stories(document_text)

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

        prefix = {"functional": "FR", "non_functional": "NFR", "constraint": "CON"}[req_type]
        requirement_id = f"{prefix}-{sentence_index + 1:03d}"

        priority = "medium"
        lowered = sentence.lower()
        if any(keyword in lowered for keyword in ("обязательно", "критично", "срочно", "must")):
            priority = "high"
        elif any(keyword in lowered for keyword in ("желательно", "может", "опционально", "nice to have")):
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
        
        # Common actor patterns
        patterns = [
            r"(\w+(?:щик|лог|тель|ант|ер))",  # Roles ending in common suffixes
            r"(менеджер|директор|бухгалтер|кладовщик|продавец|клиент)"
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, description, re.IGNORECASE)
            for match in matches:
                actors.add(match.group(1).capitalize())
        
        return list(actors)[:10]  # Limit to 10
    
    def _extract_activities(self, description: str) -> List[str]:
        """Извлечение действий"""
        activities = []
        
        # Verb patterns (simplified)
        verb_patterns = [
            r"(создать|создание)\s+(\w+)",
            r"(проверить|проверка)\s+(\w+)",
            r"(утвердить|утверждение)\s+(\w+)",
            r"(отправить|отправка)\s+(\w+)",
            r"(получить|получение)\s+(\w+)"
        ]
        
        for pattern in verb_patterns:
            matches = re.finditer(pattern, description, re.IGNORECASE)
            for match in matches:
                activity = f"{match.group(1)} {match.group(2)}"
                activities.append(activity)
        
        return activities[:15]  # Limit to 15
    
    def _extract_decision_points(self, description: str) -> List[Dict]:
        """Извлечение точек принятия решения"""
        decision_points = []
        
        # Decision patterns
        patterns = [
            r"если\s+(.+?)\s+,?\s+то",
            r"в случае\s+(.+?)\s+,?\s+(?:выполняется|происходит)"
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, description, re.IGNORECASE)
            for match in matches:
                decision_points.append({
                    "condition": match.group(1),
                    "type": "decision"
                })
        
        return decision_points[:10]
    
    def _generate_mermaid(
        self,
        actors: List[str],
        activities: List[str],
        decisions: List[Dict]
    ) -> str:
        """Генерация Mermaid диаграммы"""
        mermaid = "graph TD\n"
        mermaid += "    Start[Начало] --> Activity1\n"
        
        for i, activity in enumerate(activities[:5], 1):
            mermaid += f"    Activity{i}[{activity}] --> "
            if i < len(activities[:5]):
                mermaid += f"Activity{i+1}\n"
            else:
                mermaid += "End[Конец]\n"
        
        return mermaid
    
    def _generate_bpmn_xml(
        self,
        actors: List[str],
        activities: List[str],
        decisions: List[Dict]
    ) -> str:
        """Генерация BPMN 2.0 XML (упрощенная версия)"""
        bpmn = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
                  id="Definitions_1">
  <bpmn:process id="Process_1" isExecutable="false">
    <bpmn:startEvent id="StartEvent_1" name="Начало"/>
"""
        
        # Add activities
        for i, activity in enumerate(activities[:5], 1):
            bpmn += f'    <bpmn:task id="Activity_{i}" name="{activity}"/>\n'
        
        bpmn += """    <bpmn:endEvent id="EndEvent_1" name="Конец"/>
  </bpmn:process>
</bpmn:definitions>
"""
        
        return bpmn


class GapAnalyzer:
    """Анализатор разрывов между текущим и желаемым состоянием"""
    
    async def perform_gap_analysis(
        self,
        current_state: Dict,
        desired_state: Dict
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
            gaps.append({
                "area": "Processes",
                "gap": process,
                "current": "Not implemented",
                "desired": "Automated process",
                "impact": "high",
                "effort": "medium",
                "priority": 8
            })
        
        # Analyze systems
        current_systems = set(current_state.get("systems", []))
        desired_systems = set(desired_state.get("systems", []))
        missing_systems = desired_systems - current_systems
        
        for system in missing_systems:
            gaps.append({
                "area": "Systems",
                "gap": system,
                "current": "Not available",
                "desired": "Integrated system",
                "impact": "high",
                "effort": "high",
                "priority": 7
            })
        
        # Analyze capabilities
        current_capabilities = set(current_state.get("capabilities", []))
        desired_capabilities = set(desired_state.get("capabilities", []))
        missing_capabilities = desired_capabilities - current_capabilities
        
        for capability in missing_capabilities:
            gaps.append({
                "area": "Capabilities",
                "gap": capability,
                "current": "Manual/Limited",
                "desired": "Full capability",
                "impact": "medium",
                "effort": "medium",
                "priority": 6
            })
        
        # Sort by priority
        gaps.sort(key=lambda x: x["priority"], reverse=True)
        
        # Generate roadmap
        roadmap = self._generate_roadmap(gaps)
        
        # Estimate cost and timeline
        total_effort_days = sum(
            {"low": 10, "medium": 30, "high": 90}.get(gap["effort"], 30)
            for gap in gaps
        )
        
        return {
            "gaps_found": len(gaps),
            "gaps": gaps,
            "roadmap": roadmap,
            "estimated_timeline_months": total_effort_days // 20,  # Business days to months
            "estimated_cost_eur": total_effort_days * 500,  # €500/day
            "priority_gaps": [g for g in gaps if g["priority"] >= 7]
        }
    
    def _generate_roadmap(self, gaps: List[Dict]) -> List[Dict]:
        """Генерация дорожной карты"""
        roadmap = []
        
        # Phase 1: High priority, low effort
        phase1 = [g for g in gaps if g["priority"] >= 7 and g["effort"] in ["low", "medium"]]
        if phase1:
            roadmap.append({
                "phase": "Phase 1: Quick Wins",
                "duration_months": 1,
                "gaps": [g["gap"] for g in phase1]
            })
        
        # Phase 2: High priority, high effort
        phase2 = [g for g in gaps if g["priority"] >= 7 and g["effort"] == "high"]
        if phase2:
            roadmap.append({
                "phase": "Phase 2: Strategic Initiatives",
                "duration_months": 3,
                "gaps": [g["gap"] for g in phase2]
            })
        
        # Phase 3: Medium priority
        phase3 = [g for g in gaps if g["priority"] < 7]
        if phase3:
            roadmap.append({
                "phase": "Phase 3: Improvements",
                "duration_months": 2,
                "gaps": [g["gap"] for g in phase3]
            })
        
        return roadmap


class TraceabilityMatrixGenerator:
    """Генератор матрицы прослеживаемости требований"""
    
    async def generate_matrix(
        self,
        requirements: List[Dict],
        test_cases: List[Dict]
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
                tc for tc in test_cases
                if req_id in tc.get("requirement_ids", [])
            ]
            
            matrix.append({
                "requirement_id": req_id,
                "requirement_title": req.get("title"),
                "test_cases": [tc.get("id") for tc in covering_tests],
                "coverage": "100%" if covering_tests else "0%",
                "test_count": len(covering_tests)
            })
        
        # Coverage summary
        total_reqs = len(requirements)
        covered_reqs = sum(1 for m in matrix if m["test_count"] > 0)
        coverage_percent = int((covered_reqs / total_reqs) * 100) if total_reqs > 0 else 0
        
        return {
            "matrix": matrix,
            "coverage_summary": {
                "total_requirements": total_reqs,
                "covered_requirements": covered_reqs,
                "uncovered_requirements": total_reqs - covered_reqs,
                "coverage_percent": coverage_percent
            },
            "uncovered_requirements": [
                m["requirement_id"] for m in matrix if m["test_count"] == 0
            ],
            "generated_at": datetime.now().isoformat()
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
        return await self.extract_requirements(text, inferred_type, source_path=str(file_path))
    
    async def generate_bpmn(
        self,
        process_description: str
    ) -> Dict[str, Any]:
        """Генерация BPMN диаграммы"""
        return await self.bpmn_generator.generate_bpmn(process_description)
    
    async def analyze_gap(
        self,
        current_state: Dict,
        desired_state: Dict
    ) -> Dict[str, Any]:
        """Gap анализ"""
        return await self.gap_analyzer.perform_gap_analysis(
            current_state,
            desired_state
        )
    
    async def generate_traceability_matrix(
        self,
        requirements: List[Dict],
        test_cases: List[Dict]
    ) -> Dict[str, Any]:
        """Матрица прослеживаемости"""
        return await self.traceability_generator.generate_matrix(
            requirements,
            test_cases
        )

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
        self.clients = [client for client in (gigachat, yandex) if client and client.is_configured]

    async def enhance(self, data: Dict[str, Any], original_text: str) -> Dict[str, Any]:
        if not self.clients:
            data["summary"]["llm_used"] = False
            return data

        prompt = self._build_prompt(data, original_text)
        for client in self.clients:
            try:
                response = await client.generate(prompt, response_format="json")
            except (LLMNotConfiguredError, LLMCallError) as exc:
                logger.warning("LLM enhancement failed for %s: %s", client.__class__.__name__, exc)
                continue

            message = response.get("text") or ""
            try:
                parsed = json.loads(message)
                merged = self._merge(data, parsed)
                merged["summary"]["llm_used"] = True
                merged["summary"]["llm_provider"] = client.__class__.__name__
                return merged
            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM response as JSON, skipping provider %s", client)
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
        prompt += f"\nТекст документа:\n\"\"\"\n{original_text[:4000]}\n\"\"\"\n"
        prompt += f"\nТекущее резюме: {json.dumps(summary, ensure_ascii=False)}"
        return prompt

    def _merge(self, base: Dict[str, Any], llm_data: Dict[str, Any]) -> Dict[str, Any]:
        def _merge_list(key: str) -> List[Any]:
            existing = {item["id"]: item for item in base.get(key, []) if isinstance(item, dict) and "id" in item}
            additional = []
            for item in llm_data.get(key, []):
                if isinstance(item, dict) and "id" in item:
                    existing[item["id"]] = item
                else:
                    additional.append(item)
            return list(existing.values()) + additional

        merged = dict(base)
        merged["functional_requirements"] = _merge_list("functional_requirements")
        merged["non_functional_requirements"] = _merge_list("non_functional_requirements")
        merged["constraints"] = _merge_list("constraints")
        merged["user_stories"] = llm_data.get("user_stories", merged.get("user_stories", []))
        merged["acceptance_criteria"] = llm_data.get(
            "acceptance_criteria", merged.get("acceptance_criteria", [])
        )
        merged["stakeholders"] = list(
            sorted(
                set(merged.get("stakeholders", [])) | set(llm_data.get("stakeholders", []))
            )
        )
        return merged


