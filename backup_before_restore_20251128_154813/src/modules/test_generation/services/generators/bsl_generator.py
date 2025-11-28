"""
BSL Test Generator
"""
import asyncio
from datetime import datetime
from typing import Any, Dict, List

from src.ai.agents.code_review.bsl_parser import BSLParser
from src.infrastructure.logging.structured_logging import StructuredLogger
from src.services.openai_code_analyzer import get_openai_analyzer

logger = StructuredLogger(__name__).logger


class BSLTestGenerator:
    """Generator for BSL (1C:Enterprise) tests"""

    async def generate(self, code: str, include_edge_cases: bool = True,
                       timeout: float = 30.0) -> List[Dict[str, Any]]:
        """Generate tests for BSL code"""
        try:
                "Error in BSL test generation",
                extra = {"error": str(e), "code_length": len(code)},
                exc_info = True,
            )
            return []

    async def _generate_internal(self, code: str, include_edge_cases: bool) -> List[Dict[str, Any]]:
        """Internal generation logic"""
        tests = []
        parser = BSLParser()

        try: