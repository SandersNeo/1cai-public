"""
Owner Dashboard Service
Business logic for simple owner-level business metrics
"""
from typing import Any, Dict

import asyncpg

from src.infrastructure.logging.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class OwnerService:
    """Owner dashboard business logic"""

    async def get_dashboard(self, conn: asyncpg.Connection) -> Dict[str, Any]:
        """
        Get owner dashboard data (simple business metrics)

        Args:
            conn: Database connection

        Returns:
            Owner dashboard data dictionary
        """
        try:
