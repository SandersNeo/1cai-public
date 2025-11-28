"""
Analytics Service
"""
from typing import Any, Dict, Optional

from src.infrastructure.logging.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class AnalyticsService:
    """Service for Analytics & KPI"""

    async def generate_kpis(
        self,
        initiative_name: str,
        feature_id: Optional[str] = None,
        include_technical: bool = True,
        include_business: bool = True,
        use_graph: bool = True,
    ) -> Dict[str, Any]:
        """Generate KPIs"""
        try:
