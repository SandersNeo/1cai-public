# [NEXUS IDENTITY] ID: 6575367605745973363 | DATE: 2025-11-27

"""
Enhanced Business Analyst AI Agent
AI ассистент для бизнес-аналитиков с LLM интеграцией
"""

import logging
from typing import Any, Dict, List, Optional

from src.ai.agents.base_agent import AgentCapability, BaseAgent
from src.ai.llm import TaskType
from src.integrations.docling_processor import get_docling_processor
from src.modules.business_analyst.domain.models import (
    BPMNDiagram, GapAnalysisResult, RequirementExtractionResult,
    TraceabilityMatrix)
# Import new services
from src.modules.business_analyst.services import (BPMNGenerator, GapAnalyzer,
                                                   RequirementsExtractor,
                                                   TraceabilityMatrixGenerator)

logger = logging.getLogger(__name__)


class BusinessAnalystAgentEnhanced(BaseAgent):
    """
    Enhanced AI агент для бизнес-аналитиков

    Features:
    - LLM-based requirements analysis
    - Acceptance criteria generation
    - BPMN diagram generation
    - Requirements traceability
    - Clean Architecture services integration
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
    ) -> RequirementExtractionResult:
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
    ) -> BPMNDiagram:
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
    ) -> GapAnalysisResult:
        """
        Perform gap analysis using Clean Architecture service

        Args:
            current_state: Текущее состояние
            desired_state: Желаемое состояние

        Returns:
            GapAnalysisResult
        """
        return await self.gap_analyzer.perform_gap_analysis(
            current_state, desired_state
        )

    async def generate_traceability_matrix(
        self,
        requirements: List[Any],
        test_cases: List[Dict[str, Any]]
    ) -> TraceabilityMatrix:
        """
        Generate traceability matrix using Clean Architecture service

        Args:
            requirements: Список требований
            test_cases: Список тест-кейсов

        Returns:
            TraceabilityMatrix
        """
        return await self.traceability_generator.generate_matrix(
            requirements, test_cases
        )

    # === LEGACY METHODS: Backward Compatibility ===

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
