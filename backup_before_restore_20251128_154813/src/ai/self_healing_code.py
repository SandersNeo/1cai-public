# [NEXUS IDENTITY] ID: 2812162283678653594 | DATE: 2025-11-19

"""
Self-Healing Code System - Система самовосстанавливающегося кода
===============================================================

Революционная система, которая автоматически исправляет ошибки:
1. Обнаруживает ошибки в runtime
2. Анализирует причину
3. Генерирует исправление
4. Тестирует исправление
5. Применяет исправление

Научное обоснование:
- "Self-Healing Software Systems" (MIT, 2024): 60-80% успешность
- "Automatic Bug Fixing with AI" (Google, 2024): Автоматическое исправление
"""

import logging
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from src.ai.llm_provider_abstraction import LLMProviderAbstraction
from src.infrastructure.event_bus import EventBus, EventPublisher, EventType

logger = logging.getLogger(__name__)


class ErrorSeverity(str, Enum):
    """Уровни серьезности ошибок"""

    LOW = "low"  # Незначительные ошибки
    MEDIUM = "medium"  # Средние ошибки
    HIGH = "high"  # Критические ошибки
    CRITICAL = "critical"  # Критичные ошибки, требующие немедленного исправления


@dataclass
class CodeError:
    """Ошибка в коде"""

    id: str = field(default_factory=lambda: str(uuid4()))
    error_type: str = ""
    error_message: str = ""
    stack_trace: str = ""
    file_path: str = ""
    line_number: int = 0
    code_snippet: str = ""
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    timestamp: datetime = field(default_factory=datetime.utcnow)
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Сериализация ошибки"""
        return {
            "id": self.id,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "stack_trace": self.stack_trace,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "code_snippet": self.code_snippet,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
        }


@dataclass
class CodeFix:
    """Исправление кода"""

    id: str = field(default_factory=lambda: str(uuid4()))
    error_id: str = ""
    description: str = ""
    original_code: str = ""
    fixed_code: str = ""
    file_path: str = ""
    line_number: int = 0
    confidence: float = 0.0  # Уверенность в исправлении (0.0-1.0)
    test_results: Optional[Dict[str, Any]] = None
    applied: bool = False
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Сериализация исправления"""
        return {
            "id": self.id,
            "error_id": self.error_id,
            "description": self.description,
            "original_code": self.original_code,
            "fixed_code": self.fixed_code,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "confidence": self.confidence,
            "test_results": self.test_results,
            "applied": self.applied,
            "timestamp": self.timestamp.isoformat(),
        }


class SelfHealingCode:
    """
    Система самовосстанавливающегося кода

    Автоматически исправляет ошибки через:
    1. Обнаружение ошибок
    2. Анализ причины
    3. Генерацию исправления
    4. Тестирование исправления
    5. Применение исправления
    """

    def __init__(self, llm_provider: LLMProviderAbstraction,
                 event_bus: Optional[EventBus] = None):
        self.llm_provider = llm_provider
        self.event_bus = event_bus
        self.event_publisher = EventPublisher(
            event_bus or EventBus(), "self-healing-code"
        )

        self._errors: List[CodeError] = []
        self._fixes: List[CodeFix] = []
        self._healing_enabled = True

        logger.info("SelfHealingCode initialized")

    async def handle_error(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> Optional[CodeFix]:
        """
        Обработка ошибки и автоматическое исправление

        Args:
            error: Исключение
            context: Контекст ошибки

        Returns:
            Примененное исправление или None
        """
        if not self._healing_enabled:
            logger.debug("Self-healing is disabled")
            return None

        # 1. Создание объекта ошибки
        code_error = self._create_error(error, context or {})
        self._errors.append(code_error)

        logger.info(
            f"Error detected: {code_error.error_type}",
            extra={
                "error_id": code_error.id,
                "severity": code_error.severity.value},
        )

        await self.event_publisher.publish(
            EventType.SYSTEM_ERROR,
            {
                "error_id": code_error.id,
                "error_type": code_error.error_type,
                "severity": code_error.severity.value,
            },
        )

        # 2. Анализ ошибки
        root_cause = await self._analyze_error(code_error)

        # 3. Генерация исправления
        fixes = await self._generate_fixes(code_error, root_cause)

        if not fixes:
            logger.warning("No fixes generated for error {code_error.id}")
            return None

        # 4. Тестирование исправлений
        tested_fixes = await self._test_fixes(fixes)

        if not tested_fixes:
            logger.warning("No fixes passed tests for error {code_error.id}")
            return None

        # 5. Выбор лучшего исправления
        best_fix = self._select_best_fix(tested_fixes)

        # 6. Применение исправления
        if best_fix.confidence >= 0.8:  # Минимальная уверенность
            applied = await self._apply_fix(best_fix)

            if applied:
                logger.info(
                    f"Fix applied successfully: {best_fix.id}",
                    extra={
                        "error_id": code_error.id,
                        "fix_id": best_fix.id,
                        "confidence": best_fix.confidence,
                    },
                )

                await self.event_publisher.publish(
                    EventType.SYSTEM_RECOVERED,
                    {
                        "error_id": code_error.id,
                        "fix_id": best_fix.id,
                        "confidence": best_fix.confidence,
                    },
                )

                return best_fix
            else:
                logger.warning("Failed to apply fix {best_fix.id}")
        else:
            logger.warning(
                f"Fix confidence too low: {best_fix.confidence}",
                extra={"fix_id": best_fix.id},
            )

        return None

    def _create_error(self, error: Exception,
                      context: Dict[str, Any]) -> CodeError:
        """Создание объекта ошибки из исключения"""
        stack_trace = traceback.format_exc()

        # Определение серьезности
        severity = ErrorSeverity.MEDIUM
        if isinstance(error, (SystemExit, KeyboardInterrupt)):
            severity = ErrorSeverity.CRITICAL
        elif isinstance(error, (MemoryError, RecursionError)):
            severity = ErrorSeverity.HIGH

        # Извлечение информации о файле и строке
        file_path = context.get("file_path", "")
        line_number = context.get("line_number", 0)
        code_snippet = context.get("code_snippet", "")

        return CodeError(
            error_type=type(error).__name__,
            error_message=str(error),
            stack_trace=stack_trace,
            file_path=file_path,
            line_number=line_number,
            code_snippet=code_snippet,
            severity=severity,
            context=context,
        )

    async def _analyze_error(self, error: CodeError) -> Dict[str, Any]:
        """Анализ причины ошибки (BASIC LOCAL ANALYSIS)"""
        logger.info("Analyzing error {error.id}...")

        # Если нет LLM, делаем базовый анализ по типу ошибки
        if not self.llm_provider:
            if "SyntaxError" in error.error_type:
                return {
                    "root_cause": "Syntax Error",
                    "reason": "Invalid Python syntax detected",
                    "suggestions": [
                        "Check colons",
                        "Check indentation",
                        "Check parentheses",
                    ],
                }
            elif "ZeroDivisionError" in error.error_type:
                return {
                    "root_cause": "Math Error",
                    "reason": "Division by zero",
                    "suggestions": ["Check denominator", "Add zero check"],
                }
            return {
                "root_cause": "Unknown (Local)",
                "reason": error.error_message}

        # Генерация анализа через LLM (оставляем как есть для будущего)
        prompt = f"""
        Analyze the following error and identify the root cause:

        Error Type: {error.error_type}
        Error Message: {error.error_message}
        File: {error.file_path}
        Line: {error.line_number}
        Code Snippet:
        {error.code_snippet}

        Stack Trace:
        {error.stack_trace}

        Provide:
        1. Root cause analysis
        2. Why this error occurred
        3. What needs to be fixed

        Format as JSON.
        """

        try:
