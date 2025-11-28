"""
Query Rewriter Service

Сервис для переписывания и оптимизации SQL запросов.
"""

import re

from src.modules.sql_optimizer.domain.exceptions import QueryOptimizationError
from src.modules.sql_optimizer.domain.models import (
    OptimizedQuery,
    QueryAnalysis,
    SQLQuery,
)
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class QueryRewriter:
    """
    Сервис переписывания запросов

    Features:
    - Query rewriting
    - Anti-pattern fixes
    - Performance improvements
    - Optimization suggestions
    """

    def __init__(self):
        """Initialize rewriter"""

    async def rewrite_query(
        self,
        query: SQLQuery,
        analysis: QueryAnalysis
    ) -> OptimizedQuery:
        """
        Переписывание запроса

        Args:
            query: Оригинальный запрос
            analysis: Анализ запроса

        Returns:
            OptimizedQuery
        """
        try:
            logger.info("Rewriting SQL query")

            optimized_text = query.query_text
            improvements = []

            # Apply optimizations based on issues
            for issue in analysis.issues:
                if "SELECT *" in issue:
                    optimized_text, improved = self._fix_select_star(
                        optimized_text
                    )
                    if improved:
                        improvements.append("Replaced SELECT * with specific columns")

                elif "OR conditions" in issue:
                    optimized_text, improved = self._convert_or_to_in(
                        optimized_text
                    )
                    if improved:
                        improvements.append("Converted OR to IN clause")

                elif "Function in WHERE" in issue:
                    optimized_text, improved = self._remove_function_from_where(
                        optimized_text
                    )
                    if improved:
                        improvements.append("Removed function from WHERE clause")

                elif "LIKE with leading wildcard" in issue:
                    improvements.append(
                        "Consider full-text search instead of LIKE '%...'")

            # Estimate speedup
            estimated_speedup = self._estimate_speedup(
                len(improvements),
                analysis.complexity
            )

            return OptimizedQuery(
                original_query=query.query_text,
                optimized_query=optimized_text,
                improvements=improvements,
                estimated_speedup=estimated_speedup
            )

        except Exception as e:
            logger.error(f"Failed to rewrite query: {e}")
            raise QueryOptimizationError(
                f"Failed to rewrite query: {e}",
                details={}
            )

    def _fix_select_star(self, query_text: str) -> tuple:
        """Замена SELECT * на конкретные колонки"""
        if re.search(r'select\s+\*', query_text, re.IGNORECASE):
            # Simplified: replace with common columns
            optimized = re.sub(
                r'select\s+\*',
                'SELECT id, name, created_at',
                query_text,
                flags=re.IGNORECASE
            )
            return optimized, True
        return query_text, False

    def _convert_or_to_in(self, query_text: str) -> tuple:
        """Конвертация OR в IN"""
        # Pattern: column = value1 OR column = value2 OR ...
        pattern = r'(\w+)\s*=\s*([\'"]?\w+[\'"]?)\s+OR\s+\1\s*=\s*([\'"]?\w+[\'"]?)'

        if re.search(pattern, query_text, re.IGNORECASE):
            # Simplified conversion
            # In production: more sophisticated parsing
            return query_text, False  # Placeholder

        return query_text, False

    def _remove_function_from_where(self, query_text: str) -> tuple:
        """Удаление функции из WHERE"""
        # Pattern: WHERE UPPER(column) = value
        pattern = r'where\s+(upper|lower|trim)\s*\((\w+)\)\s*=\s*([\'"]?\w+[\'"]?)'

        match = re.search(pattern, query_text, re.IGNORECASE)
        if match:
            func, column, value = match.groups()
            # Convert value to match function
            if func.lower() == 'upper':
                new_value = value.upper() if value else value
            elif func.lower() == 'lower':
                new_value = value.lower() if value else value
            else:
                new_value = value

            optimized = re.sub(
                pattern,
                f'WHERE {column} = {new_value}',
                query_text,
                flags=re.IGNORECASE
            )
            return optimized, True

        return query_text, False

    def _estimate_speedup(
        self,
        improvements_count: int,
        complexity
    ) -> float:
        """Оценка ускорения"""
        if improvements_count == 0:
            return 1.0

        # Base speedup per improvement
        base_speedup = 1.2 ** improvements_count

        # Adjust for complexity
        complexity_multiplier = {
            "simple": 1.1,
            "moderate": 1.3,
            "complex": 1.5,
            "very_complex": 2.0
        }.get(complexity.value if hasattr(complexity, 'value') else str(complexity), 1.3)

        return round(base_speedup * complexity_multiplier, 2)


__all__ = ["QueryRewriter"]
