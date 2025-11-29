# [NEXUS IDENTITY] ID: 6575367605745973363 | DATE: 2025-11-27

"""
Enhanced QA Engineer AI Agent
AI ассистент для тестировщиков с LLM интеграцией
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from src.ai.agents.base_agent import AgentCapability, BaseAgent
from src.ai.llm import TaskType
from src.modules.qa.domain.models import (
    CoverageReport,
    TestGenerationResult,
)

if TYPE_CHECKING:
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
        test_generator: Optional["SmartTestGenerator"] = None,
        coverage_analyzer: Optional["TestCoverageAnalyzer"] = None,
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
        if test_generator:
            self.test_generator = test_generator
        else:
            from src.modules.qa.services import SmartTestGenerator
            self.test_generator = SmartTestGenerator()

        if coverage_analyzer:
            self.coverage_analyzer = coverage_analyzer
        else:
            from src.modules.qa.services import TestCoverageAnalyzer
            self.coverage_analyzer = TestCoverageAnalyzer()

        # CI/CD integration (stubs)
        self.ci_client = None

        # Change Graph integration
        self.change_graph = None
        self._init_change_graph()

    def _init_change_graph(self):
        """Initialize Change Graph client"""
        try:
            from src.integrations.change_graph_client import get_change_graph_client
            self.change_graph = get_change_graph_client()
            self.logger.info("Change Graph client initialized")
        except ImportError:
            self.logger.warning("Change Graph client not available")
        except Exception as e:
            self.logger.error("Failed to initialize Change Graph: %s", e)

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
                feature_file = await self.llm_selector.generate(
                    task_type=TaskType.BDD_GENERATION,
                    prompt=f"""
                    Сгенерируй Vanessa BDD тесты для модуля 1С:

                    Модуль: {module_name}
                    Функции: {', '.join(functions)}

                    Требования:
                    1. Используй Gherkin синтаксис на русском
                    2. Добавь positive и negative сценарии
                    3. Проверь граничные случаи
                    4. Добавь проверки ошибок
                    5. Используй Vanessa Automation синтаксис

                    Формат: .feature файл
                    """,
                    context={"framework": "Vanessa", "language": "ru"}
                )

                return feature_file["response"]
            except Exception as e:
                self.logger.error("LLM test generation failed: %s", e)

        # Template-based generation (fallback)
        return self._generate_template_tests(module_name, functions)

    def _generate_template_tests(
        self,
        module_name: str,
        functions: List[str]
    ) -> str:
        """Template-based test generation (fallback)"""
        feature_file = f"""# language: ru

Функционал: Тестирование модуля {module_name}
    Как QA инженер
    Я хочу протестировать все функции модуля {module_name}
    Чтобы убедиться в их корректной работе

Контекст:
    Дано Я запускаю сценарий открытия TestClient или TestManager
    И Я закрываю все окна клиентского приложения

"""

        for func in functions:
            feature_file += f"""
Сценарий: Тестирование функции {func}
    Когда Я вызываю функцию "{func}"
    Тогда функция выполнена без ошибок
    И результат соответствует ожидаемому значению

"""

        return feature_file

    async def trigger_ci_tests(
        self,
        pipeline: str,
        test_suite: str
    ) -> Dict[str, Any]:
        """
        Запуск тестов в CI/CD pipeline

        Args:
            pipeline: Название pipeline
            test_suite: Набор тестов

        Returns:
            Результат запуска
        """
        if not self.ci_client:
            return {
                "status": "ci_not_configured",
                "recommendation": "Configure CI/CD integration"
            }

        # TODO: Integrate with GitLab CI / GitHub Actions
        return {
            "pipeline_id": "pending",
            "status": "pending_implementation"
        }

    async def select_tests_for_change(
        self,
        changed_files: List[str]
    ) -> List[str]:
        """
        Smart test selection via Change Graph

        Args:
            changed_files: Список измененных файлов

        Returns:
            Список тестов для запуска
        """
        if not self.change_graph:
            self.logger.warning("Change Graph not available")
            return []

        # TODO: Integrate with Neo4j Change Graph
        return []

    async def heal_failing_test(
        self,
        test_name: str,
        failure_reason: str
    ) -> Dict[str, Any]:
        """
        Self-healing для падающих тестов

        Args:
            test_name: Название теста
            failure_reason: Причина падения

        Returns:
            Результат исправления
        """
        if not self.llm_selector:
            return {"status": "llm_not_available"}

        try:
            fix = await self.llm_selector.generate(
                task_type=TaskType.CODE_FIX,
                prompt=f"""
                Исправь падающий Vanessa BDD тест:

                Тест: {test_name}
                Ошибка: {failure_reason}

                Предложи исправление теста.
                """,
                context={"framework": "Vanessa"}
            )

            return {
                "fixed_test": fix["response"],
                "status": "fixed"
            }
        except Exception as e:
            self.logger.error("Test healing failed: %s", e)
            return {"status": "failed", "error": str(e)}


__all__ = ["QAEngineerAgentEnhanced"]
