"""
Business Analyst AI Agent Extended
AI ассистент для бизнес-аналитиков с полным функционалом
"""

import os
import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class RequirementsExtractor:
    """NLP извлечение требований из документов"""
    
    def __init__(self):
        # TODO: Integration with GigaChat/YandexGPT
        self.gigachat_api_key = os.getenv("GIGACHAT_API_KEY", "")
        self.requirement_patterns = self._load_requirement_patterns()
    
    def _load_requirement_patterns(self) -> List[Dict]:
        """Паттерны для распознавания требований"""
        return [
            {
                "type": "functional",
                "patterns": [
                    r"система должна\s+(.*)",
                    r"необходимо\s+(.*)",
                    r"должен(?:а|о|ы)?\s+обеспечивать\s+(.*)",
                    r"требуется\s+(.*)",
                    r"пользователь\s+(?:может|должен)\s+(.*)"
                ],
                "priority_keywords": ["обязательно", "критично", "важно"]
            },
            {
                "type": "non_functional",
                "patterns": [
                    r"производительность[:\s]+(.+)",
                    r"(?:время|скорость)\s+(?:отклика|выполнения)[:\s]+(.+)",
                    r"(?:количество|число)\s+пользователей[:\s]+(.+)",
                    r"(?:доступность|uptime)[:\s]+(.+)",
                    r"безопасность[:\s]+(.+)"
                ]
            },
            {
                "type": "constraint",
                "patterns": [
                    r"ограничение[:\s]+(.+)",
                    r"не допускается\s+(.*)",
                    r"запрещено\s+(.*)",
                    r"в рамках\s+(?:бюджета|срока)\s+(.*)"
                ]
            }
        ]
    
    async def extract_requirements(
        self,
        document_text: str,
        document_type: str = "tz"
    ) -> Dict[str, Any]:
        """
        NLP извлечение требований из документа
        
        Args:
            document_text: Текст документа (ТЗ, email, протокол совещания)
            document_type: Тип документа (tz, email, meeting_notes)
        
        Returns:
            Структурированные требования с метаданными
        """
        logger.info(f"Extracting requirements from {document_type}")
        
        functional_requirements = []
        non_functional_requirements = []
        constraints = []
        
        # Split into sentences
        sentences = re.split(r'[.!?]\s+', document_text)
        
        # Extract functional requirements
        for pattern_info in self.requirement_patterns:
            req_type = pattern_info["type"]
            
            for sentence in sentences:
                for pattern in pattern_info["patterns"]:
                    match = re.search(pattern, sentence, re.IGNORECASE)
                    if match:
                        requirement_text = match.group(1) if match.lastindex else match.group(0)
                        
                        # Determine priority
                        priority = "medium"
                        if any(kw in sentence.lower() for kw in ["обязательно", "критично", "высокий приоритет"]):
                            priority = "high"
                        elif any(kw in sentence.lower() for kw in ["желательно", "опционально"]):
                            priority = "low"
                        
                        req_obj = {
                            "id": f"REQ-{len(functional_requirements) + len(non_functional_requirements) + 1:03d}",
                            "title": requirement_text[:100],
                            "description": sentence,
                            "priority": priority,
                            "extracted_from": f"Document: {document_type}",
                            "confidence": 0.85  # Simplified confidence score
                        }
                        
                        if req_type == "functional":
                            functional_requirements.append(req_obj)
                        elif req_type == "non_functional":
                            non_functional_requirements.append(req_obj)
                        elif req_type == "constraint":
                            constraints.append(req_obj)
        
        # Extract stakeholders (simplified)
        stakeholders = self._extract_stakeholders(document_text)
        
        # Extract acceptance criteria
        acceptance_criteria = self._extract_acceptance_criteria(document_text)

        if not functional_requirements and not non_functional_requirements:
            # Простая эвристика: строки вида "1. ..." трактуем как требования
            for line in document_text.splitlines():
                stripped = line.strip()
                if not stripped or not stripped[0].isdigit():
                    continue
                parts = stripped.split('.', 1)
                if len(parts) < 2:
                    continue
                req_text = parts[1].strip()
                if not req_text:
                    continue
                functional_requirements.append({
                    "id": f"SIMPLE-REQ-{len(functional_requirements) + 1:03d}",
                    "title": req_text[:100],
                    "description": req_text,
                    "priority": "medium",
                    "extracted_from": "list_item",
                    "confidence": 0.6,
                })
        
        return {
            "document_type": document_type,
            "functional_requirements": functional_requirements,
            "non_functional_requirements": non_functional_requirements,
            "constraints": constraints,
            "stakeholders": stakeholders,
            "acceptance_criteria": acceptance_criteria,
            "total_requirements": len(functional_requirements) + len(non_functional_requirements),
            "extracted_at": datetime.now().isoformat(),
            "requirements": functional_requirements + non_functional_requirements + constraints,
        }
    
    def _extract_stakeholders(self, text: str) -> List[str]:
        """Извлечение стейкхолдеров"""
        stakeholders = []
        
        # Common stakeholder titles
        titles = [
            "менеджер", "руководитель", "директор", "администратор",
            "пользователь", "бухгалтер", "кладовщик", "продавец"
        ]
        
        for title in titles:
            if title in text.lower():
                stakeholders.append(title.capitalize())
        
        return list(set(stakeholders))
    
    def _extract_acceptance_criteria(self, text: str) -> List[str]:
        """Извлечение критериев приемки"""
        criteria = []
        
        # Patterns for acceptance criteria
        patterns = [
            r"критерий приемки[:\s]+(.+)",
            r"должно быть обеспечено[:\s]+(.+)",
            r"результат(?:ом)?\s+(?:должен|является)[:\s]+(.+)"
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                criteria.append(match.group(1).strip())
        
        return criteria


class BPMNGenerator:
    """Генератор BPMN диаграмм бизнес-процессов"""
    
    async def generate_bpmn(
        self,
        process_description: str
    ) -> Dict[str, Any]:
        """
        Генерация BPMN диаграммы
        
        Args:
            process_description: Описание бизнес-процесса
        
        Returns:
            {
                "bpmn_xml": "...",  # BPMN 2.0 XML
                "diagram_mermaid": "...",  # Mermaid diagram
                "actors": [...],
                "activities": [...],
                "decision_points": [...]
            }
        """
        logger.info("Generating BPMN diagram")
        
        # Extract process elements
        actors = self._extract_actors(process_description)
        activities = self._extract_activities(process_description)
        decision_points = self._extract_decision_points(process_description)
        
        # Generate Mermaid diagram (simpler than BPMN XML)
        mermaid_diagram = self._generate_mermaid(actors, activities, decision_points)
        
        # Generate BPMN XML (simplified)
        bpmn_xml = self._generate_bpmn_xml(actors, activities, decision_points)
        
        return {
            "process_name": "Бизнес-процесс",
            "bpmn_xml": bpmn_xml,
            "diagram_mermaid": mermaid_diagram,
            "actors": actors,
            "activities": activities,
            "decision_points": decision_points,
            "generated_at": datetime.now().isoformat()
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
    
    def __init__(self):
        self.requirements_extractor = RequirementsExtractor()
        self.bpmn_generator = BPMNGenerator()
        self.gap_analyzer = GapAnalyzer()
        self.traceability_generator = TraceabilityMatrixGenerator()
        
        logger.info("Business Analyst Agent Extended initialized")
    
    async def extract_requirements(
        self,
        document_text: str,
        document_type: str = "tz"
    ) -> Dict[str, Any]:
        """NLP извлечение требований"""
        return await self.requirements_extractor.extract_requirements(
            document_text,
            document_type
        )
    
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


