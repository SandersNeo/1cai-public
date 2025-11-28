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
                logger = logging.getLogger(__name__)
                logger.error("Error in try block", exc_info=True)

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
