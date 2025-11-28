"""
Health Calculator Service
Calculates system health score based on actual metrics
"""
import time

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
            # Check 1: Database response time (< 100ms = good)
            start = time.time()
            await conn.fetchval("SELECT 1")
            db_latency_ms = (time.time() - start) * 1000

            if db_latency_ms > 200:
                score -= 20  # Critical
            elif db_latency_ms > 100:
                score -= 10  # Warning

            # Check 2: Error rate (check recent activities for errors)
            error_count = (
                await conn.fetchval(
                    """
                SELECT COUNT(*)
                FROM activities
                WHERE type = 'error'
                  AND created_at > NOW() - INTERVAL '1 hour'
                """
                )
                or 0
            )

            if error_count > 10:
                score -= 20  # High error rate
            elif error_count > 5:
                score -= 10  # Moderate error rate

            # Check 3: Active users (should have some activity)
            recent_activity = (
                await conn.fetchval(
                    """
                SELECT COUNT(DISTINCT actor_id)
                FROM activities
                WHERE created_at > NOW() - INTERVAL '1 day'
                """
                )
                or 0
            )

            if recent_activity == 0:
                score -= 5  # No recent activity (might be okay)

            # Check 4: Failed transactions
            failed_transactions = (
                await conn.fetchval(
                    """
                SELECT COUNT(*)
                FROM transactions
                WHERE status = 'failed'
                  AND created_at > NOW() - INTERVAL '1 day'
                """
                )
                or 0
            )

            if failed_transactions > 5:
                score -= 15  # Many failures
            elif failed_transactions > 2:
                score -= 5  # Some failures

        except Exception as e:
            logger.error(
                "Error calculating health score",
                extra={"error": str(e), "error_type": type(e).__name__},
                exc_info=True,
            )
            score -= 30  # Significant issue if we can't calculate

        return max(0, min(100, score))  # Clamp between 0-100

    def get_health_status(self, score: int) -> str:
        """
        Get health status from score

        Args:
            score: Health score 0-100

        Returns:
            str: Status (healthy, warning, critical)
        """
        if score >= 80:
            return "healthy"
        elif score >= 60:
            return "warning"
        else:
            return "critical"

    def get_health_message(self, score: int) -> str:
        """
        Get health message from score

        Args:
            score: Health score 0-100

        Returns:
            str: Health message
        """
        if score >= 80:
            return "All systems operational"
        elif score >= 60:
            return "Minor issues detected"
        else:
            return "Critical issues require attention"
