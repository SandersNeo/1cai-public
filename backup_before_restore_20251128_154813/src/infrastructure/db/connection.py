# [NEXUS IDENTITY] ID: -3490012960058878088 | DATE: 2025-11-19

"""
Database Connection Pool Management
Best Practices:
- Connection pooling with optimal size
- Retry logic with exponential backoff
- Health checks and monitoring
- Graceful shutdown
"""

import asyncio
import os
import time
from contextlib import asynccontextmanager
from typing import Optional

import asyncpg

from src.infrastructure.logging.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

# Global pool instance
_pool: Optional[asyncpg.Pool] = None

# Pool configuration (best practices from top companies)
DEFAULT_MIN_SIZE = int(os.getenv("DB_POOL_MIN_SIZE", "5"))
DEFAULT_MAX_SIZE = int(os.getenv("DB_POOL_MAX_SIZE", "20"))
DEFAULT_MAX_QUERIES = int(os.getenv("DB_POOL_MAX_QUERIES", "50000"))
DEFAULT_MAX_INACTIVE_CONNECTION_LIFETIME = int(
    os.getenv("DB_POOL_MAX_INACTIVE_LIFETIME", "300"))
DEFAULT_COMMAND_TIMEOUT = int(os.getenv("DB_COMMAND_TIMEOUT", "60"))
DEFAULT_CONNECT_TIMEOUT = int(os.getenv("DB_CONNECT_TIMEOUT", "30"))


async def create_pool(max_retries: int = 1,
     retry_delay: int = 1) -> Optional[asyncpg.Pool]:
    """
    Create database connection pool with retry logic and best practices

    Features:
    - Fast failure (single attempt with short timeout)
    - Optimal pool sizing
    - Connection lifetime management
    - Query timeout protection

    Args:
        max_retries: Maximum number of retry attempts (default: 1 for fast startup)
        retry_delay: Initial delay between retries in seconds (default: 1s)

    Returns:
        Optional[asyncpg.Pool]: Configured database connection pool, or None if all attempts failed
    """
    global _pool

    if _pool is None:
        database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/enterprise_1c_ai",
        )

        logger.info("Creating database pool with optimal configuration...")

        for attempt in range(max_retries):
            try:
                    f"Failed to create database pool (attempt {attempt + 1}/{max_retries})",
                    extra = {"error": str(e), "error_type": type(e).__name__},
                )
                if attempt < max_retries - 1:
                    backoff_delay = retry_delay * (2**attempt)
                    await asyncio.sleep(backoff_delay)
                else:
                    logger.warning("Database not available, continuing without DB")
                    return None

    return _pool


async def close_pool():
    """
    Close database connection pool gracefully

    Best practice: Wait for active connections to finish before closing
    """
    global _pool

    if _pool:
        logger.info("Closing database pool...")
        try: