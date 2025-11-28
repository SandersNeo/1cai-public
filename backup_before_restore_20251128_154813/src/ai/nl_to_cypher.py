# [NEXUS IDENTITY] ID: -1205382716208989036 | DATE: 2025-11-19

"""
Natural Language to Cypher Query Generator
Версия: 2.1.0

Улучшения:
- Structured logging
- Улучшена обработка ошибок
- Input validation

Converts plain language queries to Neo4j Cypher
"""

import re
from typing import Any, Dict

from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class NLToCypherConverter:
    """Converts natural language to Cypher queries"""

    # Common patterns and their Cypher equivalents
    PATTERNS = [
        # Show/Find/List patterns
        (r"show\s+(?:me\s+)?all\s+(\w+)", r"MATCH (n:\1) RETURN n LIMIT 100"),
        (r"find\s+all\s+(\w+)", r"MATCH (n:\1) RETURN n LIMIT 100"),
        (r"list\s+(?:all\s+)?(\w+)", r"MATCH (n:\1) RETURN n LIMIT 100"),
        # Count patterns
        (r"how\s+many\s+(\w+)", r"MATCH (n:\1) RETURN count(n) AS total"),
        (r"count\s+(\w+)", r"MATCH (n:\1) RETURN count(n) AS total"),
        # Search patterns
        (
            r'search\s+(\w+)\s+(?:for|with|containing)\s+["\']([^"\']+)["\']',
            r'MATCH (n:\1) WHERE n.name CONTAINS "\2" RETURN n LIMIT 50',
        ),
        # Relationship patterns
        (
            r'(?:show|find)\s+(\w+)\s+(?:that\s+)?(?:depends on|related to)\s+["\']([^"\']+)["\']',
            r'MATCH (n:\1)-[r]->(m) WHERE m.name = "\2" RETURN n, r, m',
        ),
        # Property search
        (
            r'(\w+)\s+where\s+(\w+)\s*=\s*["\']([^"\']+)["\']',
            r'MATCH (n:\1 {\2: "\3"}) RETURN n',
        ),
    ]

    def convert(self, natural_query: str) -> Dict[str, Any]:
        """
        Convert natural language to Cypher

        Args:
            natural_query: Natural language query

        Returns:
            Dict with cypher query, confidence, and explanation
        """
        # Input validation
        if not natural_query or not isinstance(natural_query, str):
            logger.warning(
                f"Invalid natural_query: {natural_query}",
                extra={"query_type": type(natural_query).__name__},
            )
            raise ValueError("Natural query must be a non-empty string")

        # Validate query length (prevent DoS)
        max_query_length = 5000
        if len(natural_query) > max_query_length:
            logger.warning(
                f"Query too long: {len(natural_query)} characters",
                extra={
                    "query_length": len(natural_query),
                    "max_length": max_query_length,
                },
            )
            raise ValueError(
                f"Query too long. Maximum length: {max_query_length} characters"
            )

        query_lower = natural_query.lower().strip()

        logger.info(
            f"Converting NL query: {natural_query[:100]}",
            extra={"query_length": len(natural_query)},
        )

        # Try each pattern
        for pattern, cypher_template in self.PATTERNS:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                try:
