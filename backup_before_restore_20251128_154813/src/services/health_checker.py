# [NEXUS IDENTITY] ID: 7010687647128376249 | DATE: 2025-11-19

"""
Enhanced Health Checker Service
Версия: 2.0.0

Улучшения:
- Добавлен timeout для health checks
- Улучшена обработка ошибок
- Structured logging
"""

import asyncio
import os
from datetime import datetime
from typing import Dict

from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class HealthChecker:
    """
    Comprehensive health checker for all system dependencies

    Checks:
    - PostgreSQL
    - Redis
    - Neo4j
    - Qdrant
    - Elasticsearch
    - External APIs (OpenAI, Supabase)
    """

    def __init__(self):
        self.checks = []

    async def check_all(self, timeout: float = 10.0) -> Dict:
        """
        Run all health checks in parallel with timeout

        Args:
            timeout: Maximum time to wait for all checks (seconds)
        """
        # Input validation
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            logger.warning(
                "Invalid timeout in check_all",
                extra={
    "timeout": timeout,
     "timeout_type": type(timeout).__name__},
            )
            timeout = 10.0  # Default timeout

        checks = [
            self.check_postgresql(),
            self.check_redis(),
            self.check_neo4j(),
            self.check_qdrant(),
            self.check_elasticsearch(),
            self.check_openai(),
        ]

        try:
                "PostgreSQL connection error",
                extra = {
    "error": str(e),
    "host": host,
    "port": port,
     "database": database},
            )
            return {"status": "unhealthy", "error": f"Connection failed: {str(e)}"}
        except Exception as e:
            logger.error(
                "PostgreSQL health check failed",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "host": host,
                    "port": port,
                    "database": database,
                    "user": user,
                },
                exc_info=True,
            )
            return {"status": "unhealthy", "error": str(e)}

    async def check_redis(self) -> Dict:
        """Check Redis connection"""
        try: