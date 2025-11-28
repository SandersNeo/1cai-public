"""
Adaptive LLM Selector

Автоматический выбор оптимальной LLM для задачи с fallback механизмом.
Поддерживает: Qwen, GigaChat, Claude, GPT-4
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from prometheus_client import Counter, Histogram

# Prometheus metrics
llm_requests_total = Counter(
    'llm_requests_total',
    'Total LLM requests',
    ['model', 'task_type', 'status']
)

llm_response_duration = Histogram(
    'llm_response_duration_seconds',
    'LLM response duration',
    ['model', 'task_type']
)


class LLMModel(str, Enum):
    """Supported LLM models"""
    QWEN_CODER = "qwen-coder"
    QWEN_PLUS = "qwen-plus"
    GIGACHAT_PRO = "gigachat-pro"
    GIGACHAT_LITE = "gigachat-lite"
    CLAUDE_3_OPUS = "claude-3-opus"
    CLAUDE_3_SONNET = "claude-3-sonnet"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4O = "gpt-4o"


class TaskType(str, Enum):
    """Task types for LLM selection"""
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    CODE_FIX = "code_fix"
    ARCHITECTURE_ANALYSIS = "architecture_analysis"
    REQUIREMENTS_ANALYSIS = "requirements_analysis"
    DOCUMENTATION = "documentation"
    TRANSLATION = "translation"
    BDD_GENERATION = "bdd_generation"
    LOG_ANALYSIS = "log_analysis"
    METRICS_ANALYSIS = "metrics_analysis"
    SECURITY_ANALYSIS = "security_analysis"
    TASK_DECOMPOSITION = "task_decomposition"
    EFFORT_ESTIMATION = "effort_estimation"
    STATUS_REPORT = "status_report"
    API_DOCUMENTATION = "api_documentation"
    INTERACTIVE_GUIDE = "interactive_guide"
    TEST_PRIORITIZATION = "test_prioritization"
    IMPACT_ANALYSIS = "impact_analysis"
    DEBT_ANALYSIS = "debt_analysis"
    BPMN_GENERATION = "bpmn_generation"
    ACCEPTANCE_CRITERIA = "acceptance_criteria"
    SAST_ANALYSIS = "sast_analysis"
    SCALING_DECISION = "scaling_decision"
    CHAOS_ANALYSIS = "chaos_analysis"


class AdaptiveLLMSelector:
    """
    Adaptive LLM Selector - выбирает оптимальную модель для задачи.

    Features:
    - Automatic model selection based on task type
    - Fallback mechanism
    - Cost optimization
    - Performance tracking
    - Context-aware selection
    """

    def __init__(self):
        self.logger = logging.getLogger("adaptive_llm_selector")

        # Model capabilities and characteristics
        self.model_profiles = {
            LLMModel.QWEN_CODER: {
                "best_for": [
                    TaskType.CODE_GENERATION,
                    TaskType.CODE_REVIEW,
                    TaskType.CODE_FIX,
                    TaskType.BDD_GENERATION
                ],
                "languages": ["python", "javascript", "java", "bsl", "1c"],
                "cost": "low",
                "speed": "fast",
                "max_tokens": 8192,
                "fallback": LLMModel.QWEN_PLUS
            },
            LLMModel.QWEN_PLUS: {
                "best_for": [
                    TaskType.ARCHITECTURE_ANALYSIS,
                    TaskType.IMPACT_ANALYSIS,
                    TaskType.DEBT_ANALYSIS
                ],
                "cost": "medium",
                "speed": "medium",
                "max_tokens": 32768,
                "fallback": LLMModel.GPT_4_TURBO
            },
            LLMModel.GIGACHAT_PRO: {
                "best_for": [
                    TaskType.DOCUMENTATION,
                    TaskType.REQUIREMENTS_ANALYSIS,
                    TaskType.STATUS_REPORT,
                    TaskType.BPMN_GENERATION
                ],
                "languages": ["ru", "en"],
                "cost": "medium",
                "speed": "medium",
                "max_tokens": 8192,
                "fallback": LLMModel.GIGACHAT_LITE
            },
            LLMModel.GIGACHAT_LITE: {
                "best_for": [
                    TaskType.TRANSLATION,
                    TaskType.ACCEPTANCE_CRITERIA
                ],
                "languages": ["ru", "en"],
                "cost": "low",
                "speed": "fast",
                "max_tokens": 4096,
                "fallback": LLMModel.QWEN_PLUS
            },
            LLMModel.CLAUDE_3_OPUS: {
                "best_for": [
                    TaskType.ARCHITECTURE_ANALYSIS,
                    TaskType.SECURITY_ANALYSIS,
                    TaskType.SAST_ANALYSIS
                ],
                "cost": "high",
                "speed": "slow",
                "max_tokens": 200000,
                "fallback": LLMModel.CLAUDE_3_SONNET
            },
            LLMModel.CLAUDE_3_SONNET: {
                "best_for": [
                    TaskType.CODE_REVIEW,
                    TaskType.LOG_ANALYSIS,
                    TaskType.METRICS_ANALYSIS
                ],
                "cost": "medium",
                "speed": "medium",
                "max_tokens": 200000,
                "fallback": LLMModel.GPT_4_TURBO
            },
            LLMModel.GPT_4_TURBO: {
                "best_for": [
                    TaskType.TASK_DECOMPOSITION,
                    TaskType.EFFORT_ESTIMATION,
                    TaskType.SCALING_DECISION,
                    TaskType.CHAOS_ANALYSIS
                ],
                "cost": "high",
                "speed": "medium",
                "max_tokens": 128000,
                "fallback": LLMModel.GPT_4O
            },
            LLMModel.GPT_4O: {
                "best_for": [
                    TaskType.API_DOCUMENTATION,
                    TaskType.INTERACTIVE_GUIDE,
                    TaskType.TEST_PRIORITIZATION
                ],
                "cost": "medium",
                "speed": "fast",
                "max_tokens": 128000,
                "fallback": LLMModel.QWEN_PLUS
            }
        }

        # Performance tracking
        self.model_performance = {}

        # Client instances (to be initialized)
        self.clients = {}

    def select_model(
        self,
        task_type: TaskType,
        context: Optional[Dict[str, Any]] = None
    ) -> LLMModel:
        """
        Select optimal model for task type.

        Args:
            task_type: Type of task
            context: Additional context (language, domain, etc.)

        Returns:
            Selected LLM model
        """
        context = context or {}

        # Check for language-specific requirements
        language = context.get("language", "").lower()
        if language in ["ru", "russian", "русский"]:
            # Prefer GigaChat for Russian
            for model, profile in self.model_profiles.items():
                if (task_type in profile.get("best_for", []) and
                    "ru" in profile.get("languages", [])):
                    self.logger.info(
                        f"Selected {model} for {task_type} (Russian language)"
                    )
                    return model

        # Check for BSL/1C specific requirements
        if language in ["bsl", "1c"]:
            # Prefer Qwen Coder for BSL
            if task_type in self.model_profiles[LLMModel.QWEN_CODER]["best_for"]:
                self.logger.info(
                    f"Selected {LLMModel.QWEN_CODER} for {task_type} (BSL)"
                )
                return LLMModel.QWEN_CODER

        # Find best model for task type
        for model, profile in self.model_profiles.items():
            if task_type in profile.get("best_for", []):
                self.logger.info(
                    f"Selected {model} for {task_type}"
                )
                return model

        # Default fallback
        default = LLMModel.QWEN_PLUS
        self.logger.warning(
            f"No specific model for {task_type}, using default {default}"
        )
        return default

    async def generate(
        self,
        task_type: TaskType,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """
        Generate response using optimal model with fallback.

        Args:
            task_type: Type of task
            prompt: Input prompt
            context: Additional context
            max_retries: Maximum retry attempts

        Returns:
            Generated response
        """
        context = context or {}

        # Select model
        model = self.select_model(task_type, context)

        # Try with selected model
        for attempt in range(max_retries + 1):
            try:
                start_time = datetime.utcnow()

                # Call model (placeholder - will be replaced with real API calls)
                response = await self._call_model(model, prompt, context)

                # Track duration
                duration = (datetime.utcnow() - start_time).total_seconds()
                llm_response_duration.labels(
                    model=model.value,
                    task_type=task_type.value
                ).observe(duration)

                # Track success
                llm_requests_total.labels(
                    model=model.value,
                    task_type=task_type.value,
                    status="success"
                ).inc()

                self.logger.info(
                    f"Successfully generated with {model} in {duration:.2f}s"
                )

                return {
                    "model": model.value,
                    "response": response,
                    "duration": duration,
                    "task_type": task_type.value
                }

            except Exception as e:
                self.logger.error(
                    f"Error with {model} (attempt {attempt + 1}): {e}"
                )

                # Track error
                llm_requests_total.labels(
                    model=model.value,
                    task_type=task_type.value,
                    status="error"
                ).inc()

                # Try fallback
                if attempt < max_retries:
                    fallback = self.model_profiles[model].get("fallback")
                    if fallback:
                        self.logger.info("Falling back to %s", fallback)
                        model = fallback
                    else:
                        raise
                else:
                    raise

        raise RuntimeError(f"Failed to generate after {max_retries} retries")

    async def _call_model(
        self,
        model: LLMModel,
        prompt: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Call specific LLM model.

        Args:
            model: Model to call
            prompt: Input prompt
            context: Context data

        Returns:
            Model response
        """
        # TODO: Implement real API calls
        # For now, return placeholder with proper format

        self.logger.debug(
            f"Calling {model} with prompt length {len(prompt)}"
        )

        # Simulate API call
        await asyncio.sleep(0.1)

        # Generate appropriate placeholder based on context
        language = context.get("language", "").lower()

        # For BSL/1C code generation, return valid BSL code
        if language in ["bsl", "1c"] or "BSL" in prompt or "1С" in prompt:
            return """// Сгенерировано AI
// Функция для работы с данными

Функция ПолучитьДанные(Параметр1, Параметр2 = Неопределено) Экспорт
    // Описание: Получает данные по заданным параметрам
    // Параметры:
    //   Параметр1 - Строка - основной параметр
    //   Параметр2 - Произвольный - дополнительный параметр (необязательный)
    // Возвращаемое значение:
    //   Произвольный - результат обработки

    Попытка
        Результат = Неопределено;

        // Ваша логика здесь
        Если ЗначениеЗаполнено(Параметр1) Тогда
            Результат = Параметр1;
        КонецЕсли;

        Возврат Результат;

    Исключение
        ЗаписьЖурналаРегистрации("Ошибка получения данных",
            УровеньЖурналаРегистрации.Ошибка,,,
            ПодробноеПредставлениеОшибки(ИнформацияОбОшибке()));
        Возврат Неопределено;
    КонецПопытки;

КонецФункции"""

        # For Python code generation
        elif language == "python" or "python" in prompt.lower():
            return """# Generated by AI
def example_function(param1, param2=None):
    \"\"\"
    Example function generated by AI.

    Args:
        param1: First parameter
        param2: Second parameter (optional)

    Returns:
        Result of processing
    \"\"\"
    try:
        result = None

        if param1:
            result = param1

        return result

    except Exception as e:
        print(f"Error: {e}")
        return None"""

        # Default placeholder for other tasks
        else:
            return f"[{model.value}] Generated response for: {prompt[:100]}..."

    def get_model_stats(self) -> Dict[str, Any]:
        """Get model usage statistics"""
        return {
            "models": list(self.model_profiles.keys()),
            "performance": self.model_performance
        }


__all__ = [
    "AdaptiveLLMSelector",
    "LLMModel",
    "TaskType"
]
