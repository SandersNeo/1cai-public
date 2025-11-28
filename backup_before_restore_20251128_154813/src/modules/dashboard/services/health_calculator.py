"""
Health Calculator Service
Calculates system health score based on actual metrics
"""
import time
from typing import Optional

import asyncpg

from src.infrastructure.logging.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class HealthCalculator:
    """Calculates system health score"""

    async def calculate_health_score(self, conn: asyncpg.Connection) -> int:
        """
        Calculate real system health score based on actual metrics

        Args:
            conn: Database connection

        Returns:
            int: Health score from 0-100
        """
        score = 100

        try:
