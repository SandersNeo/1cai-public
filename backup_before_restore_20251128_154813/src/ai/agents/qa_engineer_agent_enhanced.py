# [NEXUS IDENTITY] ID: 6575367605745973363 | DATE: 2025-11-27

"""
Enhanced QA Engineer AI Agent
AI ассистент для тестировщиков с LLM интеграцией
"""

import logging
from typing import Any, Dict, List, Optional

from src.ai.agents.base_agent import AgentCapability, BaseAgent
from src.ai.llm import TaskType
from src.modules.qa.domain.models import (CoverageReport, TestFramework,
                                          TestGenerationResult)
# Import new services
from src.modules.qa.services import SmartTestGenerator, TestCoverageAnalyzer

logger = logging.getLogger(__name__)


class QAEngineerAgentEnhanced(BaseAgent):
    """
    Enhanced AI агент для QA инженеров

    Features:
    - LLM-powered Vanessa BDD generation
    - CI/CD integration
    - Smart test selection via Change Graph
    - Self-healing tests
    - Clean Architecture services integration
    """

    def __init__(
        self,
        test_generator=None,
        coverage_analyzer=None,
    ):
        super().__init__(
            agent_name="qa_engineer_agent_enhanced",
            capabilities=[
                AgentCapability.CODE_REVIEW,
                AgentCapability.TESTING,
            ]
        )
        self.logger = logging.getLogger("qa_engineer_agent_enhanced")

        # Initialize new services
        self.test_generator = test_generator or SmartTestGenerator()
        self.coverage_analyzer = coverage_analyzer or TestCoverageAnalyzer()

        # CI/CD integration (stubs)
        self.ci_client = None

        # Change Graph integration
        self.change_graph = None
        self._init_change_graph()

    def _init_change_graph(self):
        """Initialize Change Graph client"""
        try:

            # === NEW METHODS: Clean Architecture Services ===

    async def generate_tests_enhanced(
        self,
        function_code: str,
        function_name: str,
        module_type: str = "common_module"
    ) -> TestGenerationResult:
        """
        Enhanced test generation using Clean Architecture service

        Args:
            function_code: Код функции BSL
            function_name: Название функции
            module_type: Тип модуля

        Returns:
            TestGenerationResult
        """
        return await self.test_generator.generate_tests_for_function(
            function_code, function_name, module_type
        )

    async def analyze_coverage_enhanced(
        self,
        config_name: str,
        test_results: Optional[Dict[str, Any]] = None
    ) -> CoverageReport:
        """
        Enhanced coverage analysis using Clean Architecture service

        Args:
            config_name: Название конфигурации
            test_results: Результаты выполнения тестов

        Returns:
            CoverageReport
        """
        return await self.coverage_analyzer.analyze_coverage(
            config_name, test_results
        )

    # === LEGACY METHODS: Backward Compatibility ===

    async def generate_vanessa_tests(
        self,
        module_name: str,
        functions: List[str],
        use_llm: bool = True
    ) -> str:
        """
        Генерирует Vanessa BDD тесты с использованием LLM

        Args:
            module_name: Название модуля
            functions: Список функций для тестирования
            use_llm: Использовать LLM для генерации

        Returns:
            .feature файл с BDD сценариями
        """
        if use_llm and self.llm_selector:
            try:
