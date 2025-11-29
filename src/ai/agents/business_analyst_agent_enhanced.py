"""
Enhanced Business Analyst AI Agent
AI ассистент для бизнес-аналитиков с LLM интеграцией
"""

import logging
from typing import Any, Dict, List, Optional

from src.ai.agents.base_agent import AgentCapability, BaseAgent
from src.ai.llm import TaskType
from src.services.docling_processor import get_docling_processor

class BusinessAnalystAgentEnhanced(BaseAgent):
    """
    Enhanced AI агент для бизнес-аналитиков
    """

    def __init__(
        self,
        requirements_extractor=None,
        bpmn_generator=None,
        gap_analyzer=None,
        traceability_generator=None,
    ):
        super().__init__(
            agent_name="business_analyst_agent_enhanced",
            capabilities=[
                AgentCapability.REQUIREMENTS_ANALYSIS,
                AgentCapability.DOCUMENTATION,
            ]
        )
        self.logger = logging.getLogger("business_analyst_agent_enhanced")

        # Initialize new services
        from src.modules.business_analyst.services import (
            BPMNGenerator,
            GapAnalyzer,
            RequirementsExtractor,
            TraceabilityMatrixGenerator,
        )
        self.requirements_extractor = (
            requirements_extractor or RequirementsExtractor()
        )
        self.bpmn_generator = bpmn_generator or BPMNGenerator()
        self.gap_analyzer = gap_analyzer or GapAnalyzer()
        self.traceability_generator = (
            traceability_generator or TraceabilityMatrixGenerator()
        )

        # Enterprise Wiki integration (stub)
        self.wiki = None

        # Change Graph integration (stub)
        self.change_graph = None

        # Docling processor for document intelligence
        self.docling = get_docling_processor()

    # === NEW METHODS: Clean Architecture Services ===

    async def extract_requirements_enhanced(
        self,
        document_text: str,
        document_type: str = "tz",
        source_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Enhanced requirements extraction using Clean Architecture service

        Args:
            document_text: Текст документа
            document_type: Тип документа (tz, srs, etc.)
            source_path: Путь к файлу (опционально)

        Returns:
            RequirementExtractionResult
        """
        return await self.requirements_extractor.extract_requirements(
            document_text, document_type, source_path
        )

    async def generate_bpmn_diagram(
        self,
        process_description: str
    ) -> Any:
        """
        Generate BPMN diagram using Clean Architecture service

        Args:
            process_description: Описание бизнес-процесса

        Returns:
            BPMNDiagram
        """
        return await self.bpmn_generator.generate_bpmn(process_description)

    async def perform_gap_analysis(
        self,
        current_state: Dict[str, Any],
        desired_state: Dict[str, Any]
    ) -> Any:
        """
        Perform gap analysis using Clean Architecture service
        """
        return await self.gap_analyzer.analyze_gap(current_state, desired_state)

    async def analyze_requirements(
        self,
        requirements_text: str
    ) -> Dict[str, Any]:
        """
        LLM-based requirements analysis

        Args:
            requirements_text: Текст требований

        Returns:
            Анализ требований
        """
        if not self.llm_selector:
            return {"status": "llm_not_available"}

        try:
            analysis = await self.llm_selector.generate(
                task_type=TaskType.REQUIREMENTS_ANALYSIS,
                prompt=f"""
                Проанализируй требования для 1С системы:

                Требования: {requirements_text}

                Извлеки:
                1. Функциональные требования
                2. Нефункциональные требования
                3. Бизнес-правила
                4. Acceptance criteria
                5. Зависимости

                Формат: JSON
                """,
                context={"domain": "1C", "language": "ru"}
            )

            return {
                "analysis": analysis["response"],
                "status": "completed"
            }
        except Exception as e:
            self.logger.error("Requirements analysis failed: %s", e)
            return {"status": "failed", "error": str(e)}

    async def generate_acceptance_criteria(
        self,
        user_story: str
    ) -> List[Dict[str, str]]:
        """
        Генерация acceptance criteria в BDD формате

        Args:
            user_story: User story

        Returns:
            Список acceptance criteria (Given-When-Then)
        """
        if not self.llm_selector:
            return []

        try:
            criteria = await self.llm_selector.generate(
                task_type=TaskType.ACCEPTANCE_CRITERIA,
                prompt=f"""
                Создай SMART acceptance criteria для user story:

                User Story: {user_story}

                Формат: Given-When-Then (Gherkin)
                Язык: русский
                Включи positive и negative сценарии
                """,
                context={"framework": "BDD", "language": "ru"}
            )

            # TODO: Parse response into structured format
            return [{"criteria": criteria["response"]}]
        except Exception as e:
            self.logger.error("Criteria generation failed: %s", e)
            return []

    async def generate_bpmn(
        self,
        process_description: str
    ) -> Dict[str, Any]:
        """
        Генерация BPMN диаграммы

        Args:
            process_description: Описание бизнес-процесса

        Returns:
            BPMN диаграмма
        """
        if not self.llm_selector:
            return {"status": "llm_not_available"}

        try:
            bpmn = await self.llm_selector.generate(
                task_type=TaskType.BPMN_GENERATION,
                prompt=f"""
                Создай BPMN 2.0 диаграмму для бизнес-процесса:

                Описание: {process_description}

                Используй BPMN XML формат.
                Включи: start/end events, tasks, gateways, flows
                """,
                context={"notation": "BPMN 2.0"}
            )

            return {
                "bpmn_xml": bpmn["response"],
                "status": "generated"
            }
        except Exception as e:
            self.logger.error("BPMN generation failed: %s", e)
            return {"status": "failed", "error": str(e)}

    async def parse_requirements_document(
        self,
        document_path: str
    ) -> Dict[str, Any]:
        """
        Parse requirements document using Docling

        Args:
            document_path: Path to requirements document (PDF, DOCX, etc)

        Returns:
            Parsed requirements with structure
        """
        try:
            # Process document with Docling
            doc_result = await self.docling.process_document(document_path)

            if doc_result["status"] != "success":
                return doc_result

            # Extract requirements using LLM
            if self.llm_selector:
                analysis = await self.llm_selector.generate(
                    task_type=TaskType.REQUIREMENTS_ANALYSIS,
                    prompt=f"""
                    Извлеки требования из документа:

                    {doc_result["content"][:5000]}

                    Таблицы: {len(doc_result.get("tables", []))}

                    Извлеки:
                    1. Функциональные требования
                    2. Нефункциональные требования
                    3. Бизнес-правила
                    4. Ограничения

                    Формат: JSON
                    """,
                    context={"source": "document", "format": "structured"}
                )

                return {
                    "requirements": analysis["response"],
                    "document_metadata": doc_result["metadata"],
                    "tables": doc_result.get("tables", []),
                    "status": "completed"
                }

            return doc_result

        except Exception as e:
            self.logger.error("Document parsing failed: %s", e)
            return {"status": "failed", "error": str(e)}

    async def transcribe_meeting(
        self,
        audio_path: str
    ) -> Dict[str, Any]:
        """
        Transcribe meeting audio and extract requirements

        Args:
            audio_path: Path to audio file (WAV, MP3)

        Returns:
            Transcription and extracted requirements
        """
        try:
            # Transcribe audio
            transcript = await self.docling.transcribe_audio(audio_path)

            if transcript["status"] != "success":
                return transcript
            
            # Extract requirements from transcript
            if self.llm_selector:
                requirements = await self.llm_selector.generate(
                    task_type=TaskType.REQUIREMENTS_ANALYSIS,
                    prompt=f"""
                    Извлеки требования из транскрипции встречи:

                    {transcript["text"][:5000]}

                    Найди:
                    1. Упомянутые требования
                    2. Решения и договоренности
                    3. Action items
                    4. Вопросы и риски

                    Формат: JSON
                    """,
                    context={"source": "meeting",
                        "language": transcript.get("language", "ru")}
                )

                return {
                    "transcript": transcript["text"],
                    "requirements": requirements["response"],
                    "duration": transcript.get("duration", 0),
                    "status": "completed"
                }

            return transcript

        except Exception as e:
            self.logger.error("Meeting transcription failed: %s", e)
            return {"status": "failed", "error": str(e)}

    async def trace_requirements(
        self,
        requirement_id: str
    ) -> Dict[str, Any]:
        """
        Трассировка требований к коду

        Args:
            requirement_id: ID требования

        Returns:
            Трассировка
        """
        if not self.change_graph:
            return {
                "status": "change_graph_not_available",
                "recommendation": "Configure Change Graph integration"
            }

        # TODO: Integrate with Neo4j Change Graph
        return {
            "requirement_id": requirement_id,
            "implementations": [],
            "tests": [],
            "status": "pending_implementation"
        }


__all__ = ["BusinessAnalystAgentEnhanced"]
