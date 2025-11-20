# [NEXUS IDENTITY] ID: -5362652906318903951 | DATE: 2025-11-19

"""
Secure DevOps AI Agent
Based on Agents Rule of Two: [BC] Configuration

[A] CANNOT process untrusted inputs (only trusted log sources)
[B] Can access sensitive data (infrastructure)
[C] Can change state (execute commands)
"""

import re
from typing import Any, Dict, List, Optional

from src.security.ai_security_layer import (AgentRuleOfTwoConfig,
                                            AISecurityLayer)


class DevOpsAISecure:
    """
    Secure DevOps AI - только trusted log sources
    """

    # Доверенные источники логов
    TRUSTED_LOG_SOURCES = [
        "internal-ci-server",
        "production-monitor",
        "kubernetes-logs",
        "prometheus",
        "grafana",
        "loki",
        # Внутренние системы
    ]

    # Паттерны для allowlist логов
    SAFE_LOG_PATTERNS = [
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",  # ISO timestamp
        r"(INFO|WARNING|ERROR|DEBUG|CRITICAL)",  # Log levels
        r"\d{3}\s+(GET|POST|PUT|DELETE)",  # HTTP requests
    ]

    def __init__(self):
        self.security = AISecurityLayer()

        # Конфигурация Rule of Two
        self.config = AgentRuleOfTwoConfig(
            can_process_untrusted=False,  # [A] - только trusted sources
            can_access_sensitive=True,  # [B] - видит инфраструктуру
            can_change_state=True,  # [C] - может выполнять команды
        )

    def analyze_ci_cd_logs(
        self, logs: List[str], source: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Анализ CI/CD логов

        КРИТИЧНО: Только от trusted sources!
        """
        context = context or {}

        # [A] ЗАЩИТА: Проверка trusted source
        if not self._is_trusted_source(source):
            self.security.audit_logger.log_security_concern(
                agent_id="devops_ai_secure",
                concern_type="untrusted_log_source",
                details={"source": source, "rejected": True},
            )

            return {
                "error": f"Untrusted log source: {source}",
                "blocked": True,
                "suggestion": f"Add {source} to TRUSTED_LOG_SOURCES if this is legitimate",
            }

        # Санитизация даже для trusted sources (defense in depth!)
        sanitized_logs = self._sanitize_logs(logs)

        # AI анализ
        analysis = self._analyze_with_ai(sanitized_logs)

        # Audit logging
        self.security.audit_logger.log_ai_request(
            agent_id="devops_ai_secure",
            user_id=context.get("user_id", "system"),
            input_hash=self.security._hash_input(str(logs[:10])),  # First 10 lines
            rule_of_two_config=self.config.get_config_code(),
            approved_by_human=False,  # Auto for trusted sources
        )

        return {
            "success": True,
            "analysis": analysis,
            "source": source,
            "logs_processed": len(sanitized_logs),
            "logs_redacted": len(logs) - len(sanitized_logs),
        }

    def optimize_ci_cd_pipeline(
        self, pipeline_config: Dict[str, Any], source: str
    ) -> Dict[str, Any]:
        """
        Оптимизация CI/CD pipeline

        [B] Видит конфигурацию
        [C] Может предлагать изменения
        """
        # [A] ЗАЩИТА: Только trusted sources
        if not self._is_trusted_source(source):
            return {"error": f"Untrusted source: {source}", "blocked": True}

        # AI анализ и оптимизация
        optimized = self._optimize_pipeline_with_ai(pipeline_config)

        return {
            "success": True,
            "original": pipeline_config,
            "optimized": optimized,
            "improvements": optimized.get("improvements", []),
        }

    def _is_trusted_source(self, source: str) -> bool:
        """Проверка trusted source"""
        # Exact match
        if source in self.TRUSTED_LOG_SOURCES:
            return True

        # Domain match (*.company.com)
        for trusted in self.TRUSTED_LOG_SOURCES:
            if trusted.startswith("*.") and source.endswith(trusted[1:]):
                return True

        return False

    def _sanitize_logs(self, logs: List[str]) -> List[str]:
        """
        Санитизация логов для защиты от prompt injection

        Использует allowlist подход - только разрешённые паттерны
        """
        sanitized = []

        for line in logs:
            # Проверка на безопасные паттерны
            if self._is_safe_log_line(line):
                # Дополнительно: удаляем injection keywords
                if not self._contains_injection_keywords(line):
                    sanitized.append(line)
                else:
                    sanitized.append("[REDACTED - suspicious content]")
            else:
                sanitized.append("[REDACTED - invalid format]")

        return sanitized

    def _is_safe_log_line(self, line: str) -> bool:
        """Проверяет соответствие безопасным паттернам"""
        # Хотя бы один safe pattern должен совпадать
        for pattern in self.SAFE_LOG_PATTERNS:
            if re.search(pattern, line):
                return True

        return False

    def _contains_injection_keywords(self, line: str) -> bool:
        """Детектирует injection keywords в логах"""
        injection_keywords = [
            "ignore previous",
            "disregard",
            "new instructions",
            "forget everything",
            "system prompt",
            "you are now",
            "act as",
            "pretend to be",
        ]

        line_lower = line.lower()
        return any(keyword in line_lower for keyword in injection_keywords)

    def _analyze_with_ai(self, logs: List[str]) -> Dict[str, Any]:
        """AI анализ логов (placeholder)"""
        # В продакшене: вызов AI model
        return {
            "summary": "Build successful, no issues detected",
            "errors_count": 0,
            "warnings_count": 2,
            "recommendations": [
                "Consider adding caching to step 3",
                "Parallel execution could save 2 minutes",
            ],
        }

    def _optimize_pipeline_with_ai(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """AI оптимизация pipeline (placeholder)"""
        return {
            **config,
            "improvements": [
                "Added caching for npm dependencies",
                "Enabled parallel test execution",
            ],
        }
