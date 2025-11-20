# [NEXUS IDENTITY] ID: -2874959337580181467 | DATE: 2025-11-19

"""
Специализированный AI-ассистент для архитекторов
Реализует функции анализа требований и генерации архитектурных диаграмм
"""

import json
import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from src.config import settings

from .base_assistant import (AssistantConfig, BaseAIAssistant,
                             ChatPromptTemplate)


# Упрощенные классы для тестирования
class PromptTemplate:
    def __init__(self, **kwargs):
        pass


class StructuredOutputParser:
    def __init__(self, response_schemas):
        self.response_schemas = response_schemas

    @classmethod
    def from_response_schemas(cls, response_schemas):
        return cls(response_schemas)

    def parse(self, content):
        if isinstance(content, str):
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                pass

        parsed = {}
        for schema in self.response_schemas:
            if schema.type == "array":
                parsed[schema.name] = []
            elif schema.type == "object":
                parsed[schema.name] = {}
            elif schema.type == "string":
                parsed[schema.name] = ""
            else:
                parsed[schema.name] = None
        return parsed


class ResponseSchema:
    def __init__(self, name, description, type, required=True):
        self.name = name
        self.description = description
        self.type = type
        self.required = required


class Requirement(BaseModel):
    """Модель требования"""

    id: str
    title: str
    description: str
    type: str  # functional, non_functional, constraint
    priority: str  # high, medium, low
    acceptance_criteria: List[str]
    dependencies: List[str]
    estimated_complexity: int  # 1-10


class ArchitectureComponent(BaseModel):
    """Компонент архитектуры"""

    name: str
    type: str  # module, service, database, api, etc.
    description: str
    responsibilities: List[str]
    interfaces: List[str]
    technologies: List[str]
    dependencies: List[str]
    complexity_score: int  # 1-10


class RiskAssessment(BaseModel):
    """Оценка риска"""

    risk_id: str
    title: str
    description: str
    severity: str  # critical, high, medium, low
    probability: float  # 0-1
    impact: float  # 0-1
    mitigation_strategy: str
    owner: str


class ArchitectureProposal(BaseModel):
    """Предложение архитектуры"""

    title: str
    description: str
    components: List[ArchitectureComponent]
    risks: List[RiskAssessment]
    benefits: List[str]
    trade_offs: List[str]
    implementation_phases: List[str]
    estimated_timeline: str
    resource_requirements: List[str]


class ArchitectAssistant(BaseAIAssistant):
    """
    Специализированный ассистент для архитекторов систем 1С
    """

    def __init__(self):
        # Получаем конфигурацию для архитектора
        config_data = settings.assistant_configs["architect"]
        config = AssistantConfig(**config_data)

        super().__init__(config, settings.supabase_url, settings.supabase_key)

        # Специализированные промпты
        self.requirement_analysis_prompt = self._create_requirement_analysis_prompt()
        self.diagram_generation_prompt = self._create_diagram_generation_prompt()
        self.risk_assessment_prompt = self._create_risk_assessment_prompt()

        # Парсеры для структурированного вывода
        self.requirement_parser = self._create_requirement_parser()
        self.architecture_parser = self._create_architecture_parser()
        self.risk_parser = self._create_risk_parser()

    def _get_openai_api_key(self) -> str:
        """Получение API ключа OpenAI"""
        return settings.openai_api_key

    def _create_requirement_analysis_prompt(self) -> ChatPromptTemplate:
        """Создание промпта для анализа требований"""
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """Ты - опытный архитектор систем 1С. Проанализируй предоставленные бизнес-требования и структурируй их.

Твоя задача:
1. Выделить функциональные и нефункциональные требования
2. Определить приоритеты
3. Выявить зависимости между требованиями
4. Оценить сложность реализации
5. Сформулировать критерии приемки

Формат ответа: структурированный JSON с полями:
- id: уникальный идентификатор
- title: краткое название
- description: подробное описание
- type: functional/non_functional/constraint
- priority: high/medium/low
- acceptance_criteria: массив критериев
- dependencies: массив зависимостей
- estimated_complexity: число от 1 до 10""",
                ),
                (
                    "human",
                    """Бизнес-требования для анализа:
{requirements}

Контекст проекта:
{context}

Проанализируй требования и верни структурированный ответ в JSON формате.""",
                ),
            ]
        )

        return prompt

    def _create_diagram_generation_prompt(self) -> ChatPromptTemplate:
        """Создание промпта для генерации диаграмм"""
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """Ты - архитектор систем, эксперт в создании архитектурных диаграмм для систем 1С.

Твоя задача:
1. На основе анализа требований предложить архитектурное решение
2. Создать диаграмму в формате Mermaid
3. Обосновать выбор компонентов и их взаимосвязей
4. Выявить потенциальные риски

Поддерживаемые форматы диаграмм:
- flowchart (блок-схемы)
- graph (графы)
- sequence (диаграммы последовательности)
- class (диаграммы классов)

Для диаграмм Mermaid используй:
- Четкие подписи узлов
- Понятные связи между компонентами
- Цветовое кодирование по типам компонентов
- Группировку связанных элементов""",
                ),
                (
                    "human",
                    """Архитектурное предложение для визуализации:
{architecture_proposal}

Дополнительные требования к диаграмме:
{digram_requirements}

Создай диаграмму Mermaid и объясни архитектурное решение.""",
                ),
            ]
        )

        return prompt

    def _create_risk_assessment_prompt(self) -> ChatPromptTemplate:
        """Создание промпта для оценки рисков"""
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """Ты - эксперт по управлению рисками в IT проектах. Проанализируй архитектурное решение и выяви потенциальные риски.

Критерии оценки рисков:
- Техническая сложность реализации
- Интеграционные сложности
- Производительность и масштабируемость
- Безопасность и соответствие требованиям
- Зависимость от внешних систем
- Команда и компетенции
- Временные рамки

Для каждого риска укажи:
- severity: critical/high/medium/low
- probability: вероятность от 0 до 1
- impact: влияние от 0 до 1
- mitigation_strategy: стратегия минимизации""",
                ),
                (
                    "human",
                    """Архитектурное решение для анализа рисков:
{architecture}

Контекст проекта:
{project_context}

Выяви риски и предложи стратегии их минимизации.""",
                ),
            ]
        )

        return prompt

    def _create_requirement_parser(self) -> StructuredOutputParser:
        """Создание парсера для требований"""
        response_schemas = [
            ResponseSchema(
                name="requirements",
                description="Список проанализированных требований",
                type="array",
                required=True,
            )
        ]

        return StructuredOutputParser.from_response_schemas(response_schemas)

    def _create_architecture_parser(self) -> StructuredOutputParser:
        """Создание парсера для архитектурного решения"""
        response_schemas = [
            ResponseSchema(
                name="architecture",
                description="Архитектурное решение",
                type="object",
                required=True,
            ),
            ResponseSchema(
                name="mermaid_diagram",
                description="Диаграмма в формате Mermaid",
                type="string",
                required=True,
            ),
        ]

        return StructuredOutputParser.from_response_schemas(response_schemas)

    def _create_risk_parser(self) -> StructuredOutputParser:
        """Создание парсера для рисков"""
        response_schemas = [
            ResponseSchema(
                name="risks",
                description="Список выявленных рисков",
                type="array",
                required=True,
            ),
            ResponseSchema(
                name="overall_assessment",
                description="Общая оценка рисков проекта",
                type="string",
                required=True,
            ),
        ]

        return StructuredOutputParser.from_response_schemas(response_schemas)

    async def analyze_requirements(
        self, requirements_text: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Анализ бизнес-требований и структурирование

        Args:
            requirements_text: Текст с бизнес-требованиями
            context: Дополнительный контекст проекта

        Returns:
            Dict с проанализированными требованиями
        """
        try:
            # Подготавливаем контекст
            project_context = context or {}

            # Форматируем промпт
            prompt_value = self.requirement_analysis_prompt.format_prompt(
                requirements=requirements_text,
                context=json.dumps(project_context, ensure_ascii=False, indent=2),
            )

            # Получаем ответ от LLM
            response = await self.llm.ainvoke(prompt_value.to_messages())

            # Парсим ответ
            parsed_response = self.requirement_parser.parse(response.content)

            raw_requirements = parsed_response.get("requirements") or []
            if not raw_requirements and requirements_text:
                raw_requirements = self._heuristic_requirements(requirements_text)

            requirements = []
            for req_data in raw_requirements:
                requirement = Requirement(
                    id=req_data.get("id", "") or f"REQ-{len(requirements) + 1:03d}",
                    title=req_data.get("title", "")
                    or req_data.get("description", "")[:80],
                    description=req_data.get("description", req_data.get("title", "")),
                    type=req_data.get("type", "functional"),
                    priority=req_data.get("priority", "medium"),
                    acceptance_criteria=req_data.get("acceptance_criteria", []),
                    dependencies=req_data.get("dependencies", []),
                    estimated_complexity=req_data.get("estimated_complexity", 5),
                )
                requirements.append(requirement)

            return {
                "requirements": [req.dict() for req in requirements],
                "analysis_summary": {
                    "total_count": len(requirements),
                    "high_priority_count": len(
                        [r for r in requirements if r.priority == "high"]
                    ),
                    "functional_count": len(
                        [r for r in requirements if r.type == "functional"]
                    ),
                    "average_complexity": (
                        sum(r.estimated_complexity for r in requirements)
                        / len(requirements)
                        if requirements
                        else 0
                    ),
                    "critical_dependencies": list(
                        set(dep for req in requirements for dep in req.dependencies)
                    ),
                },
                "raw_response": response.content,
            }

        except Exception as e:
            self.logger.error(
                "Ошибка при анализе требований",
                extra={"error": str(e), "error_type": type(e).__name__},
                exc_info=True,
            )
            return {
                "error": str(e),
                "requirements": [],
                "analysis_summary": {"total_count": 0, "error": "Анализ не удался"},
            }

    def _heuristic_requirements(self, requirements_text: str) -> List[Dict[str, Any]]:
        """
        Простейший парсер требований на случай, если LLM не вернул структурированный JSON.
        Разделяет функциональные и нефункциональные блоки и выделяет нумерованные пункты.
        """
        requirements: List[Dict[str, Any]] = []
        current_type = "functional"

        lines = requirements_text.splitlines()
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            lowered = stripped.lower()
            if "нефункциональ" in lowered:
                current_type = "non_functional"
                continue
            if "функциональ" in lowered:
                current_type = "functional"
                continue

            match = re.match(r"^\d+[\.\)]\s*(.+)$", stripped)
            if not match:
                continue

            body = match.group(1).strip()
            req_id = f"REQ-{len(requirements) + 1:03d}"
            priority = "high" if current_type == "functional" else "medium"

            requirements.append(
                {
                    "id": req_id,
                    "title": body[:80],
                    "description": body,
                    "type": current_type,
                    "priority": priority,
                    "acceptance_criteria": [],
                    "dependencies": [],
                    "estimated_complexity": 5,
                }
            )

        return requirements

    async def generate_diagram(
        self,
        architecture_proposal: Dict[str, Any],
        diagram_type: str = "flowchart",
        diagram_requirements: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Генерация архитектурной диаграммы в формате Mermaid

        Args:
            architecture_proposal: Предложение архитектуры
            diagram_type: Тип диаграммы (flowchart, graph, sequence, class)
            diagram_requirements: Дополнительные требования к диаграмме

        Returns:
            Dict с кодом диаграммы и объяснением
        """
        try:
            # Подготавливаем данные для промпта
            diagram_reqs = diagram_requirements or {}

            prompt_value = self.diagram_generation_prompt.format_prompt(
                architecture_proposal=json.dumps(
                    architecture_proposal, ensure_ascii=False, indent=2
                ),
                digram_requirements=json.dumps(
                    diagram_reqs, ensure_ascii=False, indent=2
                ),
            )

            # Получаем ответ от LLM
            response = await self.llm.ainvoke(prompt_value.to_messages())

            # Парсим ответ для получения архитектуры и диаграммы
            parsed_response = self.architecture_parser.parse(response.content)

            # Извлекаем компоненты из архитектуры
            architecture = parsed_response.get("architecture", {})
            mermaid_code = parsed_response.get("mermaid_diagram", "")

            # Валидируем Mermaid код
            validated_diagram = self._validate_mermaid_code(mermaid_code, diagram_type)

            return {
                "mermaid_code": validated_diagram,
                "architecture": architecture,
                "explanation": response.content,
                "diagram_type": diagram_type,
                "components_count": len(architecture.get("components", [])),
                "rendered_diagram_url": self._generate_diagram_preview(
                    validated_diagram
                ),
            }

        except Exception as e:
            self.logger.error(
                "Ошибка при генерации диаграммы",
                extra={"error": str(e), "error_type": type(e).__name__},
                exc_info=True,
            )
            return {
                "error": str(e),
                "mermaid_code": "",
                "architecture": {},
                "explanation": "Не удалось сгенерировать диаграмму",
            }

    def _validate_mermaid_code(self, code: str, diagram_type: str) -> str:
        """Валидация и корректировка Mermaid кода"""
        if not code:
            return ""

        # Проверяем базовую структуру
        if diagram_type == "flowchart":
            if not re.search(r"flowchart\s+[TBRL]?", code):
                code = "flowchart TD\n" + code

        elif diagram_type == "graph":
            if not re.search(r"graph\s+[TBRL]?", code):
                code = "graph TD\n" + code

        elif diagram_type == "sequence":
            if not re.search(r"sequenceDiagram", code):
                code = "sequenceDiagram\n" + code

        elif diagram_type == "class":
            if not re.search(r"classDiagram", code):
                code = "classDiagram\n" + code

        # Убираем лишние переносы и форматируем
        code = re.sub(r"\n\s*\n", "\n", code)
        code = code.strip()

        return code

    def _generate_diagram_preview(self, mermaid_code: str) -> Optional[str]:
        """Генерация URL для предпросмотра диаграммы"""
        if not mermaid_code:
            return None

        # В реальном приложении здесь был бы вызов Mermaid.js для генерации SVG
        # Или использование сервиса типа Mermaid Live Editor

        # Возвращаем Base64 encoded код для использования в frontend
        import base64

        encoded_code = base64.b64encode(mermaid_code.encode()).decode()

        return f"data:text/plain;base64,{encoded_code}"

    async def assess_risks(
        self,
        architecture: Dict[str, Any],
        project_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Оценка рисков архитектурного решения

        Args:
            architecture: Архитектурное решение для анализа
            project_context: Контекст проекта

        Returns:
            Dict с оценкой рисков
        """
        try:
            context = project_context or {}

            prompt_value = self.risk_assessment_prompt.format_prompt(
                architecture=json.dumps(architecture, ensure_ascii=False, indent=2),
                project_context=json.dumps(context, ensure_ascii=False, indent=2),
            )

            response = await self.llm.ainvoke(prompt_value.to_messages())

            # Парсим ответ
            parsed_response = self.risk_parser.parse(response.content)

            risks = []
            for risk_data in parsed_response.get("risks", []):
                risk = RiskAssessment(
                    risk_id=risk_data.get("risk_id", ""),
                    title=risk_data.get("title", ""),
                    description=risk_data.get("description", ""),
                    severity=risk_data.get("severity", "medium"),
                    probability=risk_data.get("probability", 0.5),
                    impact=risk_data.get("impact", 0.5),
                    mitigation_strategy=risk_data.get("mitigation_strategy", ""),
                    owner=risk_data.get("owner", ""),
                )
                risks.append(risk)

            # Вычисляем общий риск-скор
            total_score = sum(r.probability * r.impact for r in risks) if risks else 0
            max_score = len(risks) if risks else 1
            risk_percentage = (total_score / max_score * 100) if max_score > 0 else 0

            # Определяем уровень общего риска
            if risk_percentage >= 70:
                overall_risk = "high"
            elif risk_percentage >= 40:
                overall_risk = "medium"
            else:
                overall_risk = "low"

            return {
                "risks": [risk.dict() for risk in risks],
                "overall_assessment": {
                    "risk_level": overall_risk,
                    "risk_percentage": round(risk_percentage, 2),
                    "total_risks": len(risks),
                    "critical_risks": len(
                        [r for r in risks if r.severity == "critical"]
                    ),
                    "high_risks": len([r for r in risks if r.severity == "high"]),
                },
                "recommendations": parsed_response.get("overall_assessment", ""),
                "raw_response": response.content,
            }

        except Exception as e:
            self.logger.error(
                "Ошибка при оценке рисков",
                extra={"error": str(e), "error_type": type(e).__name__},
                exc_info=True,
            )
            return {
                "error": str(e),
                "risks": [],
                "overall_assessment": {
                    "risk_level": "unknown",
                    "error": "Оценка не удалась",
                },
            }

    async def create_comprehensive_analysis(
        self, requirements_text: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Комплексный анализ: требования + архитектура + риски

        Args:
            requirements_text: Текст с требованиями
            context: Контекст проекта

        Returns:
            Dict с полным анализом
        """
        self.logger.info("Начинаем комплексный анализ требований")

        try:
            # Шаг 1: Анализ требований
            requirements_analysis = await self.analyze_requirements(
                requirements_text, context
            )

            if "error" in requirements_analysis:
                return requirements_analysis

            # Шаг 2: Создание архитектурного предложения
            architecture_proposal = await self._create_architecture_proposal(
                requirements_analysis["requirements"], context
            )

            # Шаг 3: Генерация диаграммы
            diagram = await self.generate_diagram(architecture_proposal)

            # Шаг 4: Оценка рисков
            risk_assessment = await self.assess_risks(architecture_proposal, context)

            return {
                "requirements_analysis": requirements_analysis,
                "architecture_proposal": architecture_proposal,
                "diagram": diagram,
                "risk_assessment": risk_assessment,
                "summary": {
                    "total_requirements": len(requirements_analysis["requirements"]),
                    "architecture_components": len(
                        architecture_proposal.get("components", [])
                    ),
                    "identified_risks": len(risk_assessment["risks"]),
                    "overall_risk_level": risk_assessment["overall_assessment"][
                        "risk_level"
                    ],
                    "recommendation": self._generate_recommendation(
                        requirements_analysis, architecture_proposal, risk_assessment
                    ),
                },
            }

        except Exception as e:
            self.logger.error(
                "Ошибка при комплексном анализе",
                extra={"error": str(e), "error_type": type(e).__name__},
                exc_info=True,
            )
            return {"error": "Комплексный анализ не удался"}

    async def _create_architecture_proposal(
        self, requirements: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Создание архитектурного предложения на основе требований"""

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """Создай архитектурное предложение на основе проанализированных требований.

Для каждого компонента укажи:
- name: название компонента
- type: тип (module/service/database/api/ui)
- description: описание функций
- responsibilities: список ответственности
- interfaces: интерфейсы
- technologies: технологии
- dependencies: зависимости
- complexity_score: сложность (1-10)

Также укажи общую информацию:
- title: название решения
- description: описание
- benefits: преимущества
- trade_offs: компромиссы
- implementation_phases: этапы внедрения
- estimated_timeline: временные рамки
- resource_requirements: требования к ресурсам""",
                ),
                (
                    "human",
                    """Требования для архитектуры:
{requirements}

Контекст проекта:
{context}

Создай архитектурное решение.""",
                ),
            ]
        )

        prompt_value = prompt.format_prompt(
            requirements=json.dumps(requirements, ensure_ascii=False, indent=2),
            context=json.dumps(context, ensure_ascii=False, indent=2),
        )

        response = await self.llm.ainvoke(prompt_value.to_messages())

        # Простой парсинг JSON из ответа
        try:
            # Ищем JSON в ответе
            json_match = re.search(r"\{.*\}", response.content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                raise ValueError("JSON не найден в ответе")
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.warning(
                "Не удалось распарсить архитектуру как JSON",
                extra={"error": str(e), "error_type": type(e).__name__},
            )
            return {
                "title": "Архитектурное решение",
                "description": response.content,
                "components": [],
                "benefits": [],
                "trade_offs": [],
            }

    def _generate_recommendation(
        self,
        requirements: Dict[str, Any],
        architecture: Dict[str, Any],
        risks: Dict[str, Any],
    ) -> str:
        """Генерация итоговой рекомендации"""

        risk_level = risks.get("overall_assessment", {}).get("risk_level", "medium")
        component_count = len(architecture.get("components", []))
        requirement_count = len(requirements.get("requirements", []))

        if risk_level == "low" and component_count <= 10:
            return "Рекомендуется немедленное начало разработки. Архитектурное решение зрелое и риски минимальны."
        elif risk_level == "medium":
            return "Рекомендуется поэтапная реализация с дополнительным анализом рисков на каждом этапе."
        else:
            return "Требуется дополнительный анализ и переработка архитектурного решения. Риски слишком высоки."
