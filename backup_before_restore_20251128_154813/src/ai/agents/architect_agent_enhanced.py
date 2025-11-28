# [NEXUS IDENTITY] ID: 6575367605745973363 | DATE: 2025-11-27

"""
Enhanced Architect AI Agent
AI ассистент для архитекторов с LLM интеграцией
"""

import logging
from typing import Any, Dict, List, Optional

from src.ai.agents.base_agent import AgentCapability, BaseAgent
from src.ai.architecture_patterns import PatternCategory, get_pattern_matcher
from src.ai.llm import TaskType
from src.integrations.docling_processor import get_docling_processor
from src.modules.architect.domain.models import (ADR, ADRStatus, AntiPattern,
                                                 ArchitectureAnalysisResult)
# Import new services
from src.modules.architect.services import (ADRGenerator, AntiPatternDetector,
                                            ArchitectureAnalyzer)

logger = logging.getLogger(__name__)


class ArchitectAgentEnhanced(BaseAgent):
    """
    Enhanced AI агент для архитекторов

    Features:
    - LLM-based architecture analysis
    - C4 diagram generation
    - Technical debt analysis
    - BSL-specific patterns
    - Clean Architecture services integration
    """

    def __init__(
        self,
        architecture_analyzer=None,
        adr_generator=None,
        anti_pattern_detector=None,
    ):
        super().__init__(
            agent_name="architect_agent_enhanced",
            capabilities=[
                AgentCapability.ARCHITECTURE_ANALYSIS,
                AgentCapability.CODE_REVIEW,
            ]
        )
        self.logger = logging.getLogger("architect_agent_enhanced")

        # Initialize new services
        self.architecture_analyzer = (
            architecture_analyzer or ArchitectureAnalyzer()
        )
        self.adr_generator = adr_generator or ADRGenerator()
        self.anti_pattern_detector = (
            anti_pattern_detector or AntiPatternDetector()
        )

        # Change Graph integration (stub)
        self.change_graph = None

        # Docling processor for document intelligence
        self.docling = get_docling_processor()

        # Pattern matcher for architecture patterns
        self.pattern_matcher = get_pattern_matcher()

    # === NEW METHODS: Clean Architecture Services ===

    async def analyze_architecture_enhanced(
        self,
        config_name: str,
        deep_analysis: bool = True
    ) -> ArchitectureAnalysisResult:
        """
        Enhanced architecture analysis using Clean Architecture service

        Args:
            config_name: Название конфигурации
            deep_analysis: Глубокий анализ (включая anti-patterns)

        Returns:
            ArchitectureAnalysisResult
        """
        return await self.architecture_analyzer.analyze_architecture(
            config_name, deep_analysis
        )

    async def generate_adr_enhanced(
        self,
        title: str,
        context: str,
        problem: str,
        decision: str,
        alternatives: List[Dict[str, List[str]]],
        consequences: Dict[str, List[str]],
        status: ADRStatus = ADRStatus.PROPOSED
    ) -> ADR:
        """
        Enhanced ADR generation using Clean Architecture service

        Args:
            title: Название решения
            context: Контекст
            problem: Проблема
            decision: Решение
            alternatives: Альтернативы
            consequences: Последствия
            status: Статус ADR

        Returns:
            ADR object
        """
        return await self.adr_generator.generate_adr(
            title, context, problem, decision,
            alternatives, consequences, status
        )

    async def detect_anti_patterns_enhanced(
        self,
        config_name: str
    ) -> List[AntiPattern]:
        """
        Enhanced anti-pattern detection using Clean Architecture service

        Args:
            config_name: Название конфигурации

        Returns:
            List of detected anti-patterns
        """
        return await self.anti_pattern_detector.detect_anti_patterns(
            config_name
        )

    # === LEGACY METHODS: Backward Compatibility ===

    async def analyze_architecture(
        self,
        system_description: str,
        codebase_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        LLM-based architecture analysis

        Args:
            system_description: Описание системы
            codebase_path: Путь к кодовой базе

        Returns:
            Анализ архитектуры
        """
        if not self.llm_selector:
            return {"status": "llm_not_available"}

        try:
