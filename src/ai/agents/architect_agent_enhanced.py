# [NEXUS IDENTITY] ID: 6575367605745973363 | DATE: 2025-11-27

"""
Enhanced Architect AI Agent
AI ассистент для архитекторов с LLM интеграцией
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from src.ai.agents.base_agent import AgentCapability, BaseAgent
from src.ai.architecture_patterns import get_pattern_matcher
from src.ai.llm import TaskType
from src.integrations.docling_processor import get_docling_processor
from src.modules.architect.domain.models import (
    ADR,
    ADRStatus,
    AntiPattern,
    ArchitectureAnalysisResult,
)

if TYPE_CHECKING:
    from src.modules.architect.services import (
        ADRGenerator,
        AntiPatternDetector,
        ArchitectureAnalyzer,
    )

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
        architecture_analyzer: Optional["ArchitectureAnalyzer"] = None,
        adr_generator: Optional["ADRGenerator"] = None,
        anti_pattern_detector: Optional["AntiPatternDetector"] = None,
    ):
        super().__init__(
            agent_name="architect_agent_enhanced",
            capabilities=[
                AgentCapability.ARCHITECTURE_ANALYSIS,
                AgentCapability.CODE_REVIEW,
            ]
        )
        self.logger = logging.getLogger("architect_agent_enhanced")

        # Initialize new services with lazy loading
        if architecture_analyzer:
            self.architecture_analyzer = architecture_analyzer
        else:
            from src.modules.architect.services import ArchitectureAnalyzer
            self.architecture_analyzer = ArchitectureAnalyzer()

        if adr_generator:
            self.adr_generator = adr_generator
        else:
            from src.modules.architect.services import ADRGenerator
            self.adr_generator = ADRGenerator()

        if anti_pattern_detector:
            self.anti_pattern_detector = anti_pattern_detector
        else:
            from src.modules.architect.services import AntiPatternDetector
            self.anti_pattern_detector = AntiPatternDetector()

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
            analysis = await self.llm_selector.generate(
                task_type=TaskType.ARCHITECTURE_ANALYSIS,
                prompt=f"""
                Проанализируй архитектуру 1С системы:

                Описание: {system_description}

                Проверь:
                1. Соответствие Clean Architecture
                2. Модульность и разделение ответственности
                3. Зависимости между компонентами
                4. Потенциальные проблемы масштабируемости
                5. Рекомендации по улучшению

                Формат: JSON с разделами analysis, issues, recommendations
                """,
                context={"domain": "1C", "language": "BSL"}
            )

            return {
                "analysis": analysis["response"],
                "model_used": analysis.get("model", "unknown"),
                "status": "completed"
            }
        except Exception as e:
            self.logger.error("Architecture analysis failed: %s", e)
            return {"status": "failed", "error": str(e)}

    async def generate_c4_diagram(
        self,
        system_description: str,
        level: str = "context"
    ) -> Dict[str, Any]:
        """
        Генерация C4 диаграммы

        Args:
            system_description: Описание системы
            level: Уровень (context, container, component, code)

        Returns:
            C4 диаграмма в PlantUML формате
        """
        if not self.llm_selector:
            return {"status": "llm_not_available"}

        try:
            diagram = await self.llm_selector.generate(
                task_type=TaskType.ARCHITECTURE_ANALYSIS,
                prompt=f"""
                Создай C4 диаграмму уровня {level} для системы 1С:

                Описание: {system_description}

                Используй PlantUML C4 синтаксис.
                Включи основные компоненты, связи и описания.
                """,
                context={"notation": "C4", "format": "PlantUML"}
            )

            return {
                "diagram": diagram["response"],
                "level": level,
                "format": "plantuml",
                "status": "generated"
            }
        except Exception as e:
            self.logger.error("C4 diagram generation failed: %s", e)
            return {"status": "failed", "error": str(e)}

    async def analyze_technical_debt(
        self,
        codebase_path: str
    ) -> Dict[str, Any]:
        """
        Анализ технического долга

        Args:
            codebase_path: Путь к кодовой базе

        Returns:
            Анализ технического долга
        """
        if not self.llm_selector:
            return {"status": "llm_not_available"}

        # TODO: Scan codebase and collect metrics

        try:
            debt_analysis = await self.llm_selector.generate(
                task_type=TaskType.DEBT_ANALYSIS,
                prompt=f"""
                Проанализируй технический долг в 1С проекте:

                Путь: {codebase_path}

                Оцени:
                1. Code smells и anti-patterns
                2. Устаревший код
                3. Дублирование
                4. Сложность модулей
                5. Приоритеты рефакторинга

                Формат: JSON с estimated_hours, priority_items, refactoring_plan
                """,
                context={"language": "BSL", "framework": "1C"}
            )

            return {
                "debt_analysis": debt_analysis["response"],
                "status": "completed"
            }
        except Exception as e:
            self.logger.error("Debt analysis failed: %s", e)
            return {"status": "failed", "error": str(e)}

    async def suggest_patterns(
        self,
        problem_description: str
    ) -> Dict[str, Any]:
        """
        Рекомендации BSL-specific паттернов с использованием pattern database

        Args:
            problem_description: Описание проблемы

        Returns:
            Рекомендуемые паттерны
        """
        try:
            # Get pattern suggestions from database
            suggested_patterns = self.pattern_matcher.suggest_patterns(
                problem_description
            )

            if not suggested_patterns:
                return {
                    "patterns": [],
                    "status": "no_patterns_found",
                    "recommendation": "Опишите проблему более детально"
                }

            # Format patterns for response
            patterns_info = []
            for pattern in suggested_patterns:
                patterns_info.append({
                    "name": pattern.name,
                    "category": pattern.category.value,
                    "description": pattern.description.strip(),
                    "use_cases": pattern.use_cases,
                    "benefits": pattern.benefits,
                    "drawbacks": pattern.drawbacks,
                    "bsl_adaptation": pattern.bsl_adaptation.strip(),
                    "examples": pattern.examples
                })

            # Enhance with LLM analysis if available
            if self.llm_selector:
                llm_analysis = await self.llm_selector.generate(
                    task_type=TaskType.ARCHITECTURE_ANALYSIS,
                    prompt=f"""
                    Проанализируй применимость паттернов для проблемы:

                    Проблема: {problem_description}

                    Предложенные паттерны:
                    {[p["name"] for p in patterns_info]}

                    Для каждого паттерна оцени:
                    1. Применимость (1-10)
                    2. Сложность внедрения (1-10)
                    3. Приоритет (высокий/средний/низкий)
                    4. Специфика для 1С/BSL

                    Формат: JSON
                    """,
                    context={"domain": "1C", "language": "BSL"}
                )

                return {
                    "patterns": patterns_info,
                    "llm_analysis": llm_analysis.get("response", ""),
                    "count": len(patterns_info),
                    "status": "completed"
                }

            return {
                "patterns": patterns_info,
                "count": len(patterns_info),
                "status": "completed"
            }

        except Exception as e:
            self.logger.error("Pattern suggestion failed: %s", e)
            return {"status": "failed", "error": str(e)}

    async def validate_architecture_patterns(
        self,
        architecture_description: str
    ) -> Dict[str, Any]:
        """
        Валидация архитектуры на anti-patterns

        Args:
            architecture_description: Описание архитектуры

        Returns:
            Результаты валидации с предупреждениями
        """
        try:
            # Validate using pattern matcher
            validation = self.pattern_matcher.validate_architecture(
                architecture_description
            )

            # Enhance with LLM if available
            if self.llm_selector and not validation["valid"]:
                recommendations = await self.llm_selector.generate(
                    task_type=TaskType.ARCHITECTURE_ANALYSIS,
                    prompt=f"""
                    Обнаружены anti-patterns в архитектуре:

                    {architecture_description}

                    Проблемы:
                    {validation["warnings"]}

                    Предложи конкретные шаги по исправлению для 1С/BSL.
                    """,
                    context={"task": "refactoring", "domain": "1C"}
                )

                validation["recommendations"] = recommendations.get("response", "")

            return validation

        except Exception as e:
            self.logger.error("Architecture validation failed: %s", e)
            return {"status": "failed", "error": str(e)}

    async def analyze_architecture_document(
        self,
        document_path: str
    ) -> Dict[str, Any]:
        """
        Analyze architecture document using Docling

        Args:
            document_path: Path to architecture document (PDF, DOCX, etc)

        Returns:
            Architecture analysis with extracted diagrams and patterns
        """
        try:
            # Process document with Docling
            doc_result = await self.docling.process_document(document_path)

            if doc_result["status"] != "success":
                return doc_result

            # Analyze architecture using LLM
            if self.llm_selector:
                analysis = await self.llm_selector.generate(
                    task_type=TaskType.ARCHITECTURE_ANALYSIS,
                    prompt=f"""
                    Проанализируй архитектурный документ:

                    {doc_result["content"][:5000]}

                    Таблицы: {len(doc_result.get("tables", []))}
                    Диаграммы: {doc_result["metadata"].get("has_images", False)}

                    Извлеки:
                    1. Архитектурные компоненты
                    2. Паттерны и принципы
                    3. Технологический стек
                    4. Зависимости между компонентами
                    5. Потенциальные проблемы

                    Формат: JSON
                    """,
                    context={"source": "document", "domain": "architecture"}
                )

                return {
                    "architecture_analysis": analysis["response"],
                    "document_metadata": doc_result["metadata"],
                    "tables": doc_result.get("tables", []),
                    "formulas": doc_result.get("formulas", []),
                    "status": "completed"
                }

            return doc_result

        except Exception as e:
            self.logger.error("Architecture document analysis failed: %s", e)
            return {"status": "failed", "error": str(e)}

    async def extract_diagrams(
        self,
        document_path: str
    ) -> Dict[str, Any]:
        """
        Extract diagrams from architecture document

        Args:
            document_path: Path to document

        Returns:
            Extracted diagrams and their descriptions
        """
        try:
            doc_result = await self.docling.process_document(document_path, "json")

            if doc_result["status"] != "success":
                return doc_result

            # Extract diagram descriptions using LLM
            if self.llm_selector and doc_result["metadata"].get("has_images"):
                descriptions = await self.llm_selector.generate(
                    task_type=TaskType.ARCHITECTURE_ANALYSIS,
                    prompt=f"""
                    Опиши архитектурные диаграммы из документа:

                    Контекст: {doc_result["content"][:3000]}

                    Для каждой диаграммы укажи:
                    1. Тип (C4, UML, BPMN, etc)
                    2. Назначение
                    3. Ключевые компоненты

                    Формат: JSON array
                    """,
                    context={"task": "diagram_extraction"}
                )

                return {
                    "diagrams": descriptions["response"],
                    "count": len(doc_result.get("structure", {}).get("images", [])),
                    "status": "completed"
                }

            return {
                "diagrams": [],
                "status": "no_diagrams_found"
            }

        except Exception as e:
            self.logger.error("Diagram extraction failed: %s", e)
            return {"status": "failed", "error": str(e)}

    async def analyze_impact(
        self,
        change_description: str
    ) -> Dict[str, Any]:
        """
        Анализ влияния изменений через Change Graph

        Args:
            change_description: Описание изменения

        Returns:
            Анализ влияния
        """
        if not self.change_graph:
            return {
                "status": "change_graph_not_available",
                "recommendation": "Configure Change Graph integration"
            }

        # TODO: Integrate with Neo4j Change Graph
        return {
            "affected_components": [],
            "risk_level": "unknown",
            "status": "pending_implementation"
        }


__all__ = ["ArchitectAgentEnhanced"]
