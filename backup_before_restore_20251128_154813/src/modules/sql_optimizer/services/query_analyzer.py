"""
Query Analyzer Service

Сервис для анализа SQL запросов.
"""

import re
from typing import List

from src.modules.sql_optimizer.domain.exceptions import (InvalidQueryError,
                                                         QueryAnalysisError)
from src.modules.sql_optimizer.domain.models import (QueryAnalysis,
                                                     QueryComplexity, SQLQuery)
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class QueryAnalyzer:
    """
    Сервис анализа SQL запросов

    Features:
    - Query complexity analysis
    - Anti-pattern detection
    - Missing index detection
    - Cost estimation
    """

    def __init__(self, optimization_repository=None):
        """
        Args:
            optimization_repository: Repository для patterns
        """
        if optimization_repository is None:
            from src.modules.sql_optimizer.repositories import \
                OptimizationRepository
            optimization_repository = OptimizationRepository()

        self.optimization_repository = optimization_repository

    async def analyze_query(
        self,
        query: SQLQuery
    ) -> QueryAnalysis:
        """
        Анализ SQL запроса

        Args:
            query: SQL запрос

        Returns:
            QueryAnalysis
        """
        try:
            raise QueryAnalysisError(
                f"Failed to analyze query: {e}",
                details={}
            )

    def _analyze_complexity(self, query_text: str) -> QueryComplexity:
        """Анализ сложности запроса"""
        query_lower = query_text.lower()

        # Count complexity indicators
        join_count = len(re.findall(r'\bjoin\b', query_lower))
        subquery_count = len(re.findall(r'\(select\b', query_lower))
        union_count = len(re.findall(r'\bunion\b', query_lower))
        having_count = len(re.findall(r'\bhaving\b', query_lower))

        complexity_score = (
            join_count * 2 +
            subquery_count * 3 +
            union_count * 2 +
            having_count * 1
        )

        if complexity_score >= 10:
            return QueryComplexity.VERY_COMPLEX
        elif complexity_score >= 5:
            return QueryComplexity.COMPLEX
        elif complexity_score >= 2:
            return QueryComplexity.MODERATE
        else:
            return QueryComplexity.SIMPLE

    def _detect_issues(self, query_text: str) -> List[str]:
        """Детекция проблем в запросе"""
        issues = []
        query_lower = query_text.lower()

        # SELECT *
        if re.search(r'select\s+\*', query_lower):
            issues.append("Using SELECT * - specify columns explicitly")

        # Missing WHERE
        if 'select' in query_lower and 'where' not in query_lower:
            if 'join' not in query_lower:
                issues.append(
                    "Missing WHERE clause - potential full table scan")

        # Function in WHERE
        if re.search(
            r'where.*\b(upper|lower|substring|trim)\s*\(',
                query_lower):
            issues.append("Function in WHERE clause prevents index usage")

        # OR in WHERE
        or_count = len(re.findall(r'\bor\b', query_lower))
        if or_count > 3:
            issues.append(
                f"Multiple OR conditions ({or_count}) - consider using IN")

        # LIKE with leading wildcard
        if re.search(r"like\s+'%", query_lower):
            issues.append("LIKE with leading wildcard prevents index usage")

        return issues

    def _find_missing_indexes(self, query_text: str) -> List[str]:
        """Поиск отсутствующих индексов"""
        missing_indexes = []

        # Extract WHERE columns
        where_columns = self._extract_where_columns(query_text)
        for table, column in where_columns:
            missing_indexes.append(f"{table}.{column}")

        # Extract JOIN columns
        join_columns = self._extract_join_columns(query_text)
        for table, column in join_columns:
            if f"{table}.{column}" not in missing_indexes:
                missing_indexes.append(f"{table}.{column}")

        return missing_indexes[:5]  # Top 5

    def _extract_where_columns(self, query_text: str) -> List[tuple]:
        """Извлечение колонок из WHERE"""
        columns = []
        # Simplified extraction
        where_match = re.search(
            r'where\s+(.*?)(?:group|order|limit|$)',
            query_text,
            re.IGNORECASE | re.DOTALL)
        if where_match:
            where_clause = where_match.group(1)
            # Extract table.column patterns
            matches = re.findall(r'(\w+)\.(\w+)\s*[=<>]', where_clause)
            columns.extend(matches)
        return columns

    def _extract_join_columns(self, query_text: str) -> List[tuple]:
        """Извлечение колонок из JOIN"""
        columns = []
        # Extract JOIN ON patterns
        join_matches = re.findall(
            r'join\s+\w+\s+on\s+(\w+)\.(\w+)\s*=',
            query_text,
            re.IGNORECASE
        )
        columns.extend(join_matches)
        return columns

    def _count_full_table_scans(self, query_text: str) -> int:
        """Подсчет полных сканирований таблиц"""
        query_lower = query_text.lower()

        # Heuristic: queries without WHERE or with SELECT * are likely to scan
        scans = 0

        if 'select' in query_lower and 'where' not in query_lower:
            scans += 1

        if re.search(r'select\s+\*', query_lower):
            scans += 1

        return scans

    def _estimate_cost(
        self,
        query_text: str,
        complexity: QueryComplexity
    ) -> float:
        """Оценка стоимости запроса"""
        base_cost = {
            QueryComplexity.SIMPLE: 10.0,
            QueryComplexity.MODERATE: 50.0,
            QueryComplexity.COMPLEX: 200.0,
            QueryComplexity.VERY_COMPLEX: 1000.0
        }.get(complexity, 50.0)

        # Adjust for full table scans
        if 'where' not in query_text.lower():
            base_cost *= 5

        return round(base_cost, 2)


__all__ = ["QueryAnalyzer"]
