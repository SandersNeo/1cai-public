"""
Log Patterns Repository

Repository для хранения patterns и thresholds для анализа логов.
"""

from typing import Any, Dict


class LogPatternsRepository:
    """
    Repository для базы знаний log patterns

    Хранит:
    - Performance thresholds
    - Error patterns
    - Optimization recommendations
    """

    def __init__(self):
        """Initialize repository with default patterns"""
        self._thresholds = self._load_thresholds()
        self._error_patterns = self._load_error_patterns()
        self._recommendations = self._load_recommendations()

    def get_threshold(self, metric_type: str) -> float:
        """Получить threshold для метрики"""
        return self._thresholds.get(metric_type, 1000.0)

    def get_error_pattern(self, error_type: str) -> Dict[str, Any]:
        """Получить pattern для ошибки"""
        return self._error_patterns.get(error_type, {})

    def get_recommendation(self, issue_type: str) -> str:
        """Получить рекомендацию для типа проблемы"""
        return self._recommendations.get(issue_type, "Review and optimize")

    def _load_thresholds(self) -> Dict[str, float]:
        """Load performance thresholds"""
        return {
            "slow_query_ms": 1000.0,
            "very_slow_query_ms": 5000.0,
            "slow_method_ms": 500.0,
            "lock_ms": 100.0,
            "memory_mb": 1024.0,
        }

    def _load_error_patterns(self) -> Dict[str, Dict]:
        """Load error patterns"""
        return {
            "EXCP": {"severity": "error", "category": "exception"},
            "TLOCK": {"severity": "warning", "category": "lock"},
            "TTIMEOUT": {"severity": "error", "category": "timeout"},
        }

    def _load_recommendations(self) -> Dict[str, str]:
        """Load optimization recommendations"""
        return {
            "slow_query": "Add indexes, optimize query structure",
            "slow_method": "Profile and optimize method logic",
            "lock": "Review transaction isolation, use optimistic locking",
            "exception": "Review error handling and validation",
            "memory": "Optimize memory usage, review data structures",
        }


__all__ = ["LogPatternsRepository"]
