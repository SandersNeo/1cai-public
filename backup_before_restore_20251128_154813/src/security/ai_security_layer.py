# [NEXUS IDENTITY] ID: 4659789135641391103 | DATE: 2025-11-19

"""
AI Security Layer - Unified Security для всех AI агентов
Версия: 2.1.0

Улучшения:
- Structured logging
- Улучшена обработка ошибок
- Input validation

Based on Meta's Agents Rule of Two framework
"""

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


@dataclass
class SecurityCheck:
    """Результат проверки безопасности"""

    allowed: bool
    reason: Optional[str] = None
    confidence: float = 1.0
    details: Optional[Dict[str, Any]] = None


@dataclass
class AgentRuleOfTwoConfig:
    """
    Конфигурация Agents Rule of Two
    Агент может иметь максимум 2 из 3 свойств:
    [A] - Обработка недоверенных входов
    [B] - Доступ к чувствительным данным
    [C] - Изменение состояния/коммуникация
    """

    can_process_untrusted: bool  # [A]
    can_access_sensitive: bool  # [B]
    can_change_state: bool  # [C]

    def validate(self) -> bool:
        """Проверка соответствия Rule of Two"""
        properties_count = sum(
            [
                self.can_process_untrusted,
                self.can_access_sensitive,
                self.can_change_state,
            ]
        )
        return properties_count <= 2

    def get_config_code(self) -> str:
        """Возвращает код конфигурации [AB], [AC], или [BC]"""
        props = []
        if self.can_process_untrusted:
            props.append("A")
        if self.can_access_sensitive:
            props.append("B")
        if self.can_change_state:
            props.append("C")
        return f"[{''.join(props)}]"


class AISecurityLayer:
    """Unified security layer для всех AI агентов"""

    # Паттерны prompt injection
    INJECTION_PATTERNS = [
        r"ignore\s+previous\s+instructions",
        r"disregard\s+all",
        r"forget\s+everything",
        r"new\s+instructions",
        r"system\s+prompt",
        r"you\s+are\s+now",
        r"act\s+as",
        r"pretend\s+to\s+be",
        r"override\s+your",
    ]

    # Паттерны чувствительных данных
    SENSITIVE_DATA_PATTERNS = {
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "api_key": r'(?:api[_-]?key|token)["\s:=]+([a-zA-Z0-9]{20,})',
        "password": r"password\s*[:=]\s*[^\s]+",
        "credit_card": r"\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}",
        "private_key": r"-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----",
        "bearer_token": r"Bearer\s+[a-zA-Z0-9\-._~+/]+=*",
    }

    def __init__(self):
        self.audit_logger = AuditLogger()
        self._rate_limit_cache = {}

    def validate_input(
        self,
        user_input: str,
        agent_id: str,
        agent_config: AgentRuleOfTwoConfig,
        context: Optional[Dict[str, Any]] = None,
    ) -> SecurityCheck:
        """
        Валидация входа перед обработкой AI

        Args:
            user_input: Вход от пользователя
            agent_id: ID агента
            agent_config: Конфигурация Rule of Two
            context: Дополнительный контекст

        Returns:
            SecurityCheck с результатом проверки
        """
        context = context or {}

        # Input validation
        if not user_input or not isinstance(user_input, str):
            logger.warning(
                f"Invalid user_input: {user_input}",
                extra={
                    "agent_id": agent_id,
                    "input_type": type(user_input).__name__ if user_input else None,
                },
            )
            return SecurityCheck(
                allowed=False,
                reason="Invalid input: must be a non-empty string")

        # Validate input length (prevent DoS)
        max_input_length = 100000  # 100KB max
        if len(user_input) > max_input_length:
            logger.warning(
                f"Input too long: {len(user_input)} characters",
                extra={
                    "agent_id": agent_id,
                    "input_length": len(user_input),
                    "max_length": max_input_length,
                },
            )
            return SecurityCheck(
                allowed=False,
                reason=f"Input too long. Maximum length: {max_input_length} characters",
            )

        # Проверка 0: Валидация конфигурации Rule of Two
        if not agent_config.validate():
            logger.error(
                f"Agent {agent_id} violates Rule of Two: {agent_config.get_config_code()}",
                extra={
                    "agent_id": agent_id,
                    "config_code": agent_config.get_config_code(),
                },
            )
            return SecurityCheck(
                allowed=False,
                reason="Agent configuration violates Agents Rule of Two",
                details={"config": agent_config.get_config_code()},
            )

        # Проверка 1: Prompt Injection Detection
        if agent_config.can_process_untrusted:
            injection_check = self._check_prompt_injection(user_input)
            if not injection_check.allowed:
                self.audit_logger.log_blocked_input(
                    agent_id=agent_id,
                    input_hash=self._hash_input(user_input),
                    reason="Prompt injection detected",
                    confidence=injection_check.confidence,
                )
                return injection_check

        # Проверка 2: Sensitive Data Leakage in Input
        if agent_config.can_access_sensitive:
            sensitive_check = self._check_sensitive_data_in_input(user_input)
            if not sensitive_check.allowed:
                self.audit_logger.log_security_concern(
                    agent_id=agent_id,
                    concern_type="sensitive_data_in_input",
                    details=sensitive_check.details,
                )
                # Предупреждение, но разрешаем (может быть легитимно)
                logger.warning(
                    f"Sensitive data detected in input for {agent_id}",
                    extra={
                        "agent_id": agent_id,
                        "sensitive_types": (
                            sensitive_check.details.get("types", [])
                            if sensitive_check.details
                            else []
                        ),
                    },
                )

        # Проверка 3: Rate Limiting
        user_id = context.get("user_id")
        if user_id and not self._check_rate_limit(agent_id, user_id):
            return SecurityCheck(
                allowed=False,
                reason="Rate limit exceeded",
                details={"retry_after": self._get_retry_after(user_id)},
            )

        # Все проверки пройдены
        self.audit_logger.log_ai_request(
            agent_id=agent_id,
            user_id=user_id or "anonymous",
            input_hash=self._hash_input(user_input),
            rule_of_two_config=agent_config.get_config_code(),
        )

        return SecurityCheck(allowed=True)

    def validate_output(
        self,
        ai_output: str,
        agent_id: str,
        agent_config: AgentRuleOfTwoConfig,
        context: Optional[Dict[str, Any]] = None,
    ) -> SecurityCheck:
        """
        Валидация выхода AI перед возвратом пользователю

        Args:
            ai_output: Выход от AI
            agent_id: ID агента
            agent_config: Конфигурация Rule of Two
            context: Дополнительный контекст

        Returns:
            SecurityCheck с результатом (может включать redacted output)
        """
        context = context or {}

        # Проверка 1: Sensitive Data Leakage
        if agent_config.can_access_sensitive:
            leakage_check = self._check_data_leakage(ai_output)

            if leakage_check["has_leakage"]:
                self.audit_logger.log_data_leakage_attempt(
                    agent_id=agent_id,
                    output_hash=self._hash_input(ai_output),
                    leaked_types=leakage_check["types"],
                )

                # Редактируем чувствительные данные
                redacted_output = self._redact_sensitive_data(ai_output)

                return SecurityCheck(
                    allowed=True,
                    reason="Sensitive data was redacted",
                    details={
                        "output": redacted_output,
                        "redacted": True,
                        "types": leakage_check["types"],
                    },
                )

        # Все проверки пройдены
        return SecurityCheck(
            allowed=True, details={"output": ai_output, "redacted": False}
        )

    def _check_prompt_injection(self, text: str) -> SecurityCheck:
        """Детектирует попытки prompt injection с input validation"""
        if not text or not isinstance(text, str):
            logger.warning(
                "Invalid text in _check_prompt_injection",
                extra={"text_type": type(text).__name__ if text else None},
            )
            return SecurityCheck(allowed=False, reason="Invalid input")

        try:
