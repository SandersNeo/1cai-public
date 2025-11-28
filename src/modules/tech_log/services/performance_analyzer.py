"""
Performance Analyzer Service

Сервис для анализа производительности на основе tech log.
"""

from typing import Dict, List

from src.modules.tech_log.domain.exceptions import PerformanceAnalysisError
from src.modules.tech_log.domain.models import (
    IssueType,
    PerformanceAnalysisResult,
    PerformanceIssue,
    Severity,
    TechLogEvent,
)
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class PerformanceAnalyzer:
    """
    Сервис анализа производительности

    Features:
    - Slow query detection
    - Slow method detection
    - Performance metrics calculation
    - Threshold-based analysis
    """

    # Thresholds
    SLOW_QUERY_THRESHOLD_MS = 1000
    SLOW_METHOD_THRESHOLD_MS = 500
    LOCK_THRESHOLD_MS = 100

    def __init__(self):
        """Initialize analyzer"""

    async def analyze_performance(
        self,
        events: List[TechLogEvent]
    ) -> PerformanceAnalysisResult:
        """
        Анализ производительности

        Args:
            events: События tech log

        Returns:
            PerformanceAnalysisResult
        """
        try:
            logger.info(
                "Analyzing performance",
                extra={"events_count": len(events)}
            )

            # Find slow queries
            slow_queries = self._find_slow_queries(events)

            # Find slow methods
            slow_methods = self._find_slow_methods(events)

            # Analyze exceptions
            errors_by_type = self._analyze_exceptions(events)

            # Analyze locks
            locks_analysis = self._analyze_locks(events)

            # Detect performance issues
            performance_issues = self._detect_performance_issues(
                slow_queries,
                slow_methods,
                errors_by_type,
                locks_analysis
            )

            # Generate AI recommendations
            ai_recommendations = self._generate_ai_recommendations(
                performance_issues
            )

            return PerformanceAnalysisResult(
                performance_issues=performance_issues,
                top_slow_queries=slow_queries[:10],
                top_slow_methods=slow_methods[:10],
                errors_by_type=errors_by_type,
                locks_analysis=locks_analysis,
                ai_recommendations=ai_recommendations
            )

        except Exception as e:
            logger.error("Failed to analyze performance: %s", e)
            raise PerformanceAnalysisError(
                f"Failed to analyze performance: {e}",
                details={}
            )

    def _find_slow_queries(
        self,
        events: List[TechLogEvent]
    ) -> List[Dict]:
        """Поиск медленных SQL запросов"""
        slow_queries = []

        for event in events:
            if (event.event_type in ["DBMSSQL", "SDBL"] and
                event.duration_ms >= self.SLOW_QUERY_THRESHOLD_MS):

                slow_queries.append({
                    "sql": event.sql or event.context,
                    "duration_ms": event.duration_ms,
                    "timestamp": event.timestamp.isoformat(),
                    "user": event.user,
                    "context": event.context
                })

        # Sort by duration
        slow_queries.sort(key=lambda x: x["duration_ms"], reverse=True)

        return slow_queries

    def _find_slow_methods(
        self,
        events: List[TechLogEvent]
    ) -> List[Dict]:
        """Поиск медленных методов"""
        slow_methods = []

        for event in events:
            if (event.event_type == "CALL" and
                event.duration_ms >= self.SLOW_METHOD_THRESHOLD_MS):

                slow_methods.append({
                    "method": event.method or event.context,
                    "duration_ms": event.duration_ms,
                    "timestamp": event.timestamp.isoformat(),
                    "user": event.user,
                    "context": event.context
                })

        # Sort by duration
        slow_methods.sort(key=lambda x: x["duration_ms"], reverse=True)

        return slow_methods

    def _analyze_exceptions(
        self,
        events: List[TechLogEvent]
    ) -> Dict:
        """Анализ исключений"""
        errors = {}

        for event in events:
            if event.error:
                error_type = event.event_type
                if error_type not in errors:
                    errors[error_type] = {
                        "count": 0,
                        "examples": []
                    }

                errors[error_type]["count"] += 1
                if len(errors[error_type]["examples"]) < 5:
                    errors[error_type]["examples"].append({
                        "error": event.error,
                        "timestamp": event.timestamp.isoformat(),
                        "context": event.context
                    })

        return errors

    def _analyze_locks(
        self,
        events: List[TechLogEvent]
    ) -> Dict:
        """Анализ блокировок"""
        locks = {
            "total_locks": 0,
            "long_locks": 0,
            "lock_types": {}
        }

        for event in events:
            if event.event_type in ["TLOCK", "TTIMEOUT"]:
                locks["total_locks"] += 1

                if event.duration_ms >= self.LOCK_THRESHOLD_MS:
                    locks["long_locks"] += 1

                lock_type = event.event_type
                locks["lock_types"][lock_type] = \
                    locks["lock_types"].get(lock_type, 0) + 1

        return locks

    def _detect_performance_issues(
        self,
        slow_queries: List[Dict],
        slow_methods: List[Dict],
        errors: Dict,
        locks: Dict
    ) -> List[PerformanceIssue]:
        """Детекция проблем производительности"""
        issues = []

        # Slow queries issues
        if len(slow_queries) > 10:
            issues.append(
                PerformanceIssue(
                    issue_type=IssueType.SLOW_QUERY,
                    severity=Severity.WARNING,
                    description=f"Found {len(slow_queries)} slow queries",
                    location="Database",
                    metric_value=float(len(slow_queries)),
                    threshold=10.0,
                    occurrences=len(slow_queries),
                    recommendation="Review and optimize slow queries",
                    auto_fix_available=False
                )
            )

        # Slow methods issues
        if len(slow_methods) > 10:
            issues.append(
                PerformanceIssue(
                    issue_type=IssueType.SLOW_METHOD,
                    severity=Severity.WARNING,
                    description=f"Found {len(slow_methods)} slow methods",
                    location="Application",
                    metric_value=float(len(slow_methods)),
                    threshold=10.0,
                    occurrences=len(slow_methods),
                    recommendation="Optimize slow methods",
                    auto_fix_available=False
                )
            )

        # Lock issues
        if locks["long_locks"] > 5:
            issues.append(
                PerformanceIssue(
                    issue_type=IssueType.LOCK,
                    severity=Severity.WARNING,
                    description=f"Found {locks['long_locks']} long locks",
                    location="Database",
                    metric_value=float(locks["long_locks"]),
                    threshold=5.0,
                    occurrences=locks["long_locks"],
                    recommendation="Review locking strategy",
                    auto_fix_available=False
                )
            )

        return issues

    def _generate_ai_recommendations(
        self,
        issues: List[PerformanceIssue]
    ) -> List[str]:
        """Генерация AI рекомендаций"""
        recommendations = []

        for issue in issues:
            if issue.issue_type == IssueType.SLOW_QUERY:
                recommendations.append(
                    "Consider adding indexes to frequently queried tables"
                )
                recommendations.append(
                    "Review query execution plans"
                )
            elif issue.issue_type == IssueType.SLOW_METHOD:
                recommendations.append(
                    "Profile slow methods to identify bottlenecks"
                )
            elif issue.issue_type == IssueType.LOCK:
                recommendations.append(
                    "Review transaction isolation levels"
                )
                recommendations.append(
                    "Consider optimistic locking where appropriate"
                )

        return list(set(recommendations))  # Remove duplicates


__all__ = ["PerformanceAnalyzer"]
