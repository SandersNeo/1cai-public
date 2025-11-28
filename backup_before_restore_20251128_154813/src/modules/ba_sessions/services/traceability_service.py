"""
Traceability Service
"""
from typing import Any, Dict, List

from src.infrastructure.logging.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class TraceabilityService:
    """Service for Traceability & Compliance"""

    async def build_traceability_matrix(
        self,
        requirement_ids: List[str],
        include_code: bool = True,
        include_tests: bool = True,
        include_incidents: bool = True,
        use_graph: bool = True,
    ) -> Dict[str, Any]:
        """Build traceability matrix"""
        try:
