"""SQL Optimizer Service."""

import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import sqlparse

from ..domain.sql import (Index, IndexRecommendation, OptimizationResult,
                          PerformancePrediction, QueryAnalysis, QueryType,
                          SQLQuery)


class SQLOptimizerService:
    """Service for SQL query optimization."""

    def __init__(self):
        """Initialize SQL optimizer."""
        self.slow_query_threshold_ms = 1000

    def analyze_query(self, query_text: str) -> QueryAnalysis:
        """
        Analyze SQL query.

        Args:
            query_text: SQL query text

        Returns:
            Query analysis with issues and suggestions
        """
        # Parse query
        parsed = sqlparse.parse(query_text)[
            0] if sqlparse.parse(query_text) else None

        if not parsed:
            return QueryAnalysis(
                query=self._create_query_stub(query_text),
                has_index=False,
                uses_full_scan=True,
                estimated_cost=1000.0,
                issues=["Failed to parse query"],
                warnings=[],
                suggestions=["Check query syntax"]
            )

        # Detect issues
        issues = []
        warnings = []
        suggestions = []

        # Check for SELECT *
        if 'SELECT *' in query_text.upper():
            warnings.append("Using SELECT * - specify columns explicitly")
            suggestions.append("Replace SELECT * with specific column names")

        # Check for missing WHERE clause
        if 'SELECT' in query_text.upper() and 'WHERE' not in query_text.upper():
            warnings.append("No WHERE clause - may scan entire table")
            suggestions.append("Add WHERE clause to filter data")

        # Check for OR conditions (may prevent index usage)
        if ' OR ' in query_text.upper():
            warnings.append("OR conditions may prevent index usage")
            suggestions.append("Consider using UNION or IN clause instead")

        # Check for functions in WHERE clause
        if re.search(r'WHERE.*\w+\(', query_text, re.IGNORECASE):
            issues.append("Functions in WHERE clause prevent index usage")
            suggestions.append(
                "Avoid using functions on indexed columns in WHERE clause")

        # Check for LIKE with leading wildcard
        if re.search(r"LIKE\s+['\"]%", query_text, re.IGNORECASE):
            issues.append("LIKE with leading wildcard prevents index usage")
            suggestions.append("Avoid leading wildcards in LIKE patterns")

        return QueryAnalysis(
            query=self._create_query_stub(query_text),
            has_index=len(issues) == 0,  # Simplified
            uses_full_scan=len(warnings) > 0,
            estimated_cost=len(issues) * 100.0 + len(warnings) * 50.0,
            issues=issues,
            warnings=warnings,
            suggestions=suggestions
        )

    def optimize_query(self, query_text: str) -> OptimizationResult:
        """
        Optimize SQL query.

        Args:
            query_text: Original SQL query

        Returns:
            Optimization result with improved query
        """
        original_query = self._create_query_stub(query_text)
        optimized = query_text
        changes = []
        recommendations = []

        # Replace SELECT *
        if 'SELECT *' in query_text.upper():
            # Can't auto-replace without knowing schema
            recommendations.append("Replace SELECT * with specific columns")

        # Add LIMIT if missing (for SELECT queries)
        if 'SELECT' in query_text.upper() and 'LIMIT' not in query_text.upper():
            optimized += ' LIMIT 1000'
            changes.append("Added LIMIT 1000 to prevent large result sets")

        # Format query
        try:
            logger = logging.getLogger(__name__)
            logger.error("Error in try block", exc_info=True)

        # Calculate improvement
        original_issues = len(self.analyze_query(query_text).issues)
        optimized_issues = len(self.analyze_query(optimized).issues)
        improvement = max(
            0, (original_issues - optimized_issues) / max(1, original_issues) * 100)

        return OptimizationResult(
            original_query=original_query,
            optimized_query=optimized,
            expected_improvement_percent=improvement,
            estimated_time_ms=int(1000 * (1 - improvement / 100)),
            changes=changes,
            recommendations=recommendations,
            is_valid=True
        )

    def suggest_indexes(
        self,
        table_name: str,
        query_patterns: Optional[List[str]] = None
    ) -> List[IndexRecommendation]:
        """
        Suggest indexes for table.

        Args:
            table_name: Table name
            query_patterns: Common query patterns (optional)

        Returns:
            List of index recommendations
        """
        recommendations = []

        if not query_patterns:
            # Generic recommendation
            recommendations.append(IndexRecommendation(
                table_name=table_name,
                recommended_columns=["id"],
                reason="Primary key index",
                expected_improvement_percent=50.0,
                estimated_size_mb=10.0,
                priority="high"
            ))
            return recommendations

        # Analyze query patterns
        for pattern in query_patterns:
            # Extract WHERE columns
            where_match = re.search(r'WHERE\s+(\w+)', pattern, re.IGNORECASE)
            if where_match:
                column = where_match.group(1)
                recommendations.append(IndexRecommendation(
                    table_name=table_name,
                    recommended_columns=[column],
                    reason=f"Frequently used in WHERE clause",
                    expected_improvement_percent=40.0,
                    estimated_size_mb=5.0,
                    priority="medium"
                ))

        return recommendations

    def predict_performance(self, query_text: str) -> PerformancePrediction:
        """
        Predict query performance.

        Args:
            query_text: SQL query

        Returns:
            Performance prediction
        """
        analysis = self.analyze_query(query_text)

        # Estimate based on issues
        base_time = 100  # ms
        issue_penalty = len(analysis.issues) * 500
        warning_penalty = len(analysis.warnings) * 200

        estimated_time = base_time + issue_penalty + warning_penalty

        # Estimate rows (simplified)
        has_limit = 'LIMIT' in query_text.upper()
        estimated_rows = 1000 if has_limit else 10000

        # Calculate confidence
        confidence = 0.7 if analysis.issues else 0.9

        factors = []
        if analysis.issues:
            factors.extend(analysis.issues)
        if analysis.warnings:
            factors.extend(analysis.warnings)
        if not factors:
            factors.append("Query appears optimized")

        return PerformancePrediction(
            query_text=query_text,
            estimated_time_ms=estimated_time,
            estimated_rows=estimated_rows,
            estimated_cost=analysis.estimated_cost,
            confidence=confidence,
            factors=factors
        )

    def _create_query_stub(self, query_text: str) -> SQLQuery:
        """Create SQLQuery stub for analysis."""
        query_type = self._detect_query_type(query_text)

        return SQLQuery(
            query_id=f"query_{datetime.now().timestamp()}",
            text=query_text,
            query_type=query_type,
            execution_time_ms=0,
            rows_affected=0
        )

    def _detect_query_type(self, query_text: str) -> QueryType:
        """Detect SQL query type."""
        query_upper = query_text.upper().strip()

        if query_upper.startswith('SELECT'):
            return QueryType.SELECT
        elif query_upper.startswith('INSERT'):
            return QueryType.INSERT
        elif query_upper.startswith('UPDATE'):
            return QueryType.UPDATE
        elif query_upper.startswith('DELETE'):
            return QueryType.DELETE
        else:
            return QueryType.OTHER
