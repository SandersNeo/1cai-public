"""
TypeScript Code Analyzer
"""
import re
from typing import Any, Dict

from src.infrastructure.logging.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class TypeScriptAnalyzer:
    """Analyzer for TypeScript code"""

    def analyze(self, code: str) -> Dict[str, Any]:
        """Analyze TypeScript code"""
        # Input validation
        if not isinstance(code, str) or not code.strip():
            logger.warning(
                "Invalid code in analyze_typescript_code",
                extra={"code_type": type(code).__name__ if code else None},
            )
            return self._empty_result()

        # Limit code length (prevent DoS)
        max_code_length = 100000  # 100KB max
        if len(code) > max_code_length:
            logger.warning(
                "Code too long in analyze_typescript_code",
                extra={
                    "code_length": len(code),
                    "max_length": max_code_length,
                },
            )
            code = code[:max_code_length]

        try:
