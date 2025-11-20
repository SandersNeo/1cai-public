# [NEXUS IDENTITY] ID: -8279323937878410066 | DATE: 2025-11-19

"""
Secure SQL Optimizer
Based on Agents Rule of Two: [AB] Configuration

[A] Can process untrusted inputs (any SQL)
[B] Can access sensitive data (DB schema)
[C] CANNOT execute automatically (requires human approval!)
"""

import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.security.ai_security_layer import AISecurityLayer, AgentRuleOfTwoConfig


@dataclass
class TrustedContributor:
    github_id: str
    email: str
    name: str
    approved_prs: int
    trusted_since: str
    no_security_incidents: bool = True


class SQLOptimizerSecure:
    """
    Secure SQL Optimizer - требует approval для execution
    """

    def __init__(self):
        self.security = AISecurityLayer()

        # Конфигурация Rule of Two
        self.config = AgentRuleOfTwoConfig(
            can_process_untrusted=True,  # [A] - принимает любой SQL
            can_access_sensitive=True,  # [B] - видит схему БД
            can_change_state=False,  # [C] - НЕ выполняет автоматически
        )

        self._pending_queries: Dict[str, Dict[str, Any]] = {}
        self.trusted_contributors: List[TrustedContributor] = (
            self._load_trusted_contributors()
        )

    def optimize_query(
        self, sql: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Оптимизирует SQL запрос

        Returns:
            {
                'optimized_sql': optimized query,
                'token': approval token,
                'safety': safety analysis,
                'performance_gain': estimated improvement,
                'requires_approval': bool
            }
        """
        context = context or {}

        # Input validation
        input_check = self.security.validate_input(
            user_input=sql,
            agent_id="sql_optimizer_secure",
            agent_config=self.config,
            context=context,
        )

        if not input_check.allowed:
            return {"error": input_check.reason, "blocked": True}

        # Проверка на SQL injection в входе
        if self._contains_sql_injection(sql):
            return {
                "error": "Potential SQL injection detected in input",
                "blocked": True,
                "suggestion": "Use parameterized queries",
            }

        # Оптимизация с AI
        try:
            optimized = self._optimize_with_ai(sql)
        except Exception as e:
            return {"error": f"Optimization failed: {str(e)}", "blocked": True}

        # Анализ безопасности
        safety = self._analyze_query_safety(optimized)

        # Оценка performance gain
        performance = self._estimate_performance_gain(sql, optimized)

        # Генерация token
        token = str(uuid.uuid4())

        # Сохранение для approval
        self._pending_queries[token] = {
            "original": sql,
            "optimized": optimized,
            "safety": safety,
            "performance": performance,
            "created_at": datetime.now(),
            "context": context,
        }

        return {
            "success": True,
            "original_sql": sql,
            "optimized_sql": optimized,
            "token": token,
            "safety": safety,
            "performance_gain": performance,
            "requires_approval": not safety["safe_for_auto_execute"],
            "can_execute": safety["safe_for_auto_execute"],
            "preview_url": f"/api/sql-approval/preview/{token}",
        }

    def execute_approved_query(
        self, token: str, approved_by_user: str, confirmation_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Выполняет запрос ТОЛЬКО после human approval

        Для опасных операций требует typing "CONFIRM"
        """
        # Проверка токена
        if token not in self._pending_queries:
            return {"error": "Invalid or expired token", "blocked": True}

        query_data = self._pending_queries[token]

        # Проверка expiration
        if datetime.now() - query_data["created_at"] > timedelta(minutes=30):
            del self._pending_queries[token]
            return {"error": "Token expired", "blocked": True}

        safety = query_data["safety"]

        # Для опасных операций - требуем confirmation text
        if safety["has_dangerous_ops"]:
            if confirmation_text != "CONFIRM":
                return {
                    "error": 'Dangerous operation requires typing "CONFIRM"',
                    "blocked": True,
                    "requires_confirmation": True,
                }

        # Audit logging
        self.security.audit_logger.log_ai_request(
            agent_id="sql_optimizer_secure",
            user_id=approved_by_user,
            input_hash=self.security._hash_input(query_data["original"]),
            rule_of_two_config=self.config.get_config_code(),
            approved_by_human=True,  # ✅ Human одобрил
        )

        # Выполнение
        try:
            result = self._execute_query(query_data["optimized"])

            # Удаляем из pending
            del self._pending_queries[token]

            return {
                "success": True,
                "result": result,
                "rows_affected": result.get("rows_affected"),
                "execution_time": result.get("execution_time"),
            }

        except Exception as e:
            return {"error": f"Execution failed: {str(e)}", "blocked": True}

    def _analyze_query_safety(self, sql: str) -> Dict[str, Any]:
        """Анализ безопасности SQL запроса"""
        sql_upper = sql.upper()

        # Опасные операции
        dangerous_ops = [
            "DROP",
            "DELETE",
            "UPDATE",
            "ALTER",
            "GRANT",
            "REVOKE",
            "TRUNCATE",
        ]
        has_dangerous = any(op in sql_upper for op in dangerous_ops)

        # Для SELECT - проверяем subqueries
        is_select_only = sql_upper.strip().startswith("SELECT")
        has_dangerous_subqueries = (
            self._has_dangerous_subqueries(sql) if is_select_only else False
        )

        return {
            "safe_for_auto_execute": is_select_only and not has_dangerous_subqueries,
            "has_dangerous_ops": has_dangerous,
            "is_read_only": is_select_only and not has_dangerous_subqueries,
            "operations": self._extract_operations(sql),
            "requires_dba_approval": has_dangerous and "DROP" in sql_upper,
            "warning": self._generate_safety_warning(sql, has_dangerous),
        }

    def _has_dangerous_subqueries(self, sql: str) -> bool:
        """Проверяет subqueries на опасные операции"""
        # Ищем subqueries
        subquery_pattern = r"\(SELECT.*?\)"
        subqueries = re.findall(subquery_pattern, sql, re.IGNORECASE | re.DOTALL)

        dangerous_ops = ["DELETE", "UPDATE", "DROP", "ALTER"]

        for subquery in subqueries:
            for op in dangerous_ops:
                if op in subquery.upper():
                    return True

        return False

    def _extract_operations(self, sql: str) -> List[str]:
        """Извлекает SQL операции из запроса"""
        operations = []
        sql_upper = sql.upper()

        ops = [
            "SELECT",
            "INSERT",
            "UPDATE",
            "DELETE",
            "DROP",
            "ALTER",
            "CREATE",
            "GRANT",
        ]

        for op in ops:
            if op in sql_upper:
                operations.append(op)

        return operations

    def _generate_safety_warning(self, sql: str, has_dangerous: bool) -> Optional[str]:
        """Генерирует предупреждение"""
        if not has_dangerous:
            return None

        sql_upper = sql.upper()

        if "DROP" in sql_upper:
            return "⚠️ CRITICAL: This query will DROP tables/databases!"
        elif "DELETE" in sql_upper:
            return "⚠️ WARNING: This query will DELETE data!"
        elif "UPDATE" in sql_upper:
            return "⚠️ WARNING: This query will UPDATE data!"
        elif "ALTER" in sql_upper:
            return "⚠️ WARNING: This query will ALTER schema!"

        return "⚠️ This query will modify data"

    def _contains_sql_injection(self, sql: str) -> bool:
        """Простая детекция SQL injection"""
        injection_patterns = [
            r";\s*DROP",
            r"'\s*OR\s*'1'\s*=\s*'1",
            r"--\s*$",
            r"/\*.*\*/",
            r";\s*EXEC",
            r"xp_cmdshell",
        ]

        for pattern in injection_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                return True

        return False

    def _optimize_with_ai(self, sql: str) -> str:
        """AI оптимизация SQL (placeholder)"""
        # В продакшене: вызов AI model
        # Пример простой оптимизации:
        optimized = sql

        # Replace SELECT * with explicit columns
        if "SELECT *" in sql.upper():
            optimized = sql.replace("SELECT *", "SELECT id, name, email")

        return optimized

    def _estimate_performance_gain(
        self, original: str, optimized: str
    ) -> Dict[str, Any]:
        """Оценка performance improvement (placeholder)"""
        # В продакшене: EXPLAIN ANALYZE
        return {
            "original_estimated_time": 5.2,
            "optimized_estimated_time": 0.3,
            "speedup": 17.3,
            "explanation": "Converted N+1 query to batch query",
        }

    def _execute_query(self, sql: str) -> Dict[str, Any]:
        """Выполнение SQL (placeholder)"""
        # В продакшене: реальное выполнение
        return {"rows_affected": 10, "execution_time": 0.3, "success": True}

    def _get_contribution_history(self, author: str) -> Dict[str, Any]:
        """История contributions (placeholder)"""
        # В продакшене: GitHub API или БД
        return {"approved_prs": 0, "rejected_prs": 0, "no_security_issues": True}

    def _add_to_trusted_list(self, author: str, email: str):
        """Добавление в trusted list"""
        # В продакшене: сохранение в БД
        contributor = TrustedContributor(
            github_id=author,
            email=email,
            name=author,
            approved_prs=5,
            trusted_since=datetime.now().isoformat(),
        )
        self.trusted_contributors.append(contributor)

    def _load_trusted_contributors(self) -> List[TrustedContributor]:
        """Загрузка trusted contributors"""
        # В продакшене: загрузка из БД
        return []
