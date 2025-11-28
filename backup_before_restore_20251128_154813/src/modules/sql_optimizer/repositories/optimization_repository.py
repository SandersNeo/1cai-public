"""
Optimization Repository

Repository для хранения optimization patterns и best practices.
"""

from typing import Any, Dict


class OptimizationRepository:
    """
    Repository для базы знаний SQL optimization

    Хранит:
    - Anti-patterns
    - Optimization rules
    - Index strategies
    - Best practices
    """

    def __init__(self):
        """Initialize repository with patterns"""
        self._anti_patterns = self._load_anti_patterns()
        self._optimization_rules = self._load_optimization_rules()
        self._index_strategies = self._load_index_strategies()

    def get_anti_pattern(self, pattern_type: str) -> Dict[str, Any]:
        """Получить anti-pattern"""
        return self._anti_patterns.get(pattern_type, {})

    def get_optimization_rule(self, rule_type: str) -> Dict[str, Any]:
        """Получить optimization rule"""
        return self._optimization_rules.get(rule_type, {})

    def get_index_strategy(self, strategy_type: str) -> Dict[str, Any]:
        """Получить index strategy"""
        return self._index_strategies.get(strategy_type, {})

    def _load_anti_patterns(self) -> Dict[str, Dict]:
        """Load SQL anti-patterns"""
        return {
            "select_star": {
                "name": "SELECT *",
                "severity": "medium",
                "description": "Selecting all columns is inefficient",
                "fix": "Specify only needed columns",
            },
            "missing_where": {
                "name": "Missing WHERE",
                "severity": "high",
                "description": "Query without WHERE causes full table scan",
                "fix": "Add WHERE clause with indexed columns",
            },
            "function_in_where": {
                "name": "Function in WHERE",
                "severity": "high",
                "description": "Functions prevent index usage",
                "fix": "Move function to SELECT or use computed column",
            },
            "multiple_or": {
                "name": "Multiple OR",
                "severity": "medium",
                "description": "Multiple OR conditions are slow",
                "fix": "Use IN clause instead",
            },
            "leading_wildcard": {
                "name": "LIKE with leading %",
                "severity": "high",
                "description": "Leading wildcard prevents index usage",
                "fix": "Use full-text search or reverse index",
            },
        }

    def _load_optimization_rules(self) -> Dict[str, Dict]:
        """Load optimization rules"""
        return {
            "use_limit": {
                "name": "Use LIMIT",
                "benefit": "Reduces result set size",
                "when": "When full result set not needed",
            },
            "use_exists": {
                "name": "Use EXISTS instead of IN",
                "benefit": "Better performance for large subqueries",
                "when": "Checking existence, not retrieving data",
            },
            "avoid_distinct": {
                "name": "Avoid DISTINCT when possible",
                "benefit": "DISTINCT requires sorting",
                "when": "Use GROUP BY or proper joins instead",
            },
        }

    def _load_index_strategies(self) -> Dict[str, Dict]:
        """Load index strategies"""
        return {
            "where_columns": {
                "priority": "high",
                "type": "btree",
                "reason": "Columns in WHERE clause benefit most from indexes",
            },
            "join_columns": {
                "priority": "high",
                "type": "btree",
                "reason": "JOIN columns need indexes for performance",
            },
            "order_by_columns": {
                "priority": "medium",
                "type": "btree",
                "reason": "ORDER BY can use indexes to avoid sorting",
            },
            "group_by_columns": {
                "priority": "medium",
                "type": "btree",
                "reason": "GROUP BY benefits from indexes",
            },
        }


__all__ = ["OptimizationRepository"]
