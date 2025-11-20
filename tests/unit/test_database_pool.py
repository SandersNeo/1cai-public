# [NEXUS IDENTITY] ID: 1123248268577682331 | DATE: 2025-11-19

"""
Unit tests for database connection pool
Best Practices: Comprehensive testing of connection pooling
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.database import (check_pool_health, close_pool, create_pool,
                          get_db_connection, get_pool)


class AsyncAcquireContext:
    """Helper async context manager returning a mocked connection."""

    def __init__(self, conn):
        self.conn = conn

    async def __aenter__(self):
        return self.conn

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.fixture(autouse=True)
def reset_pool():
    """Ensure global pool state is reset between tests."""
    import src.database

    src.database._pool = None
    yield
    src.database._pool = None


@pytest.mark.asyncio
async def test_create_pool_success():
    """Test successful pool creation"""
    mock_conn = AsyncMock()
    mock_conn.fetchval = AsyncMock(return_value=1)
    mock_pool = MagicMock()
    mock_pool.acquire.return_value = AsyncAcquireContext(mock_conn)

    with patch(
        "src.database.asyncpg.create_pool", new_callable=AsyncMock
    ) as mock_create_pool:
        mock_create_pool.return_value = mock_pool

        pool = await create_pool()

        assert pool == mock_pool
        mock_create_pool.assert_called_once()
        mock_conn.fetchval.assert_awaited()


@pytest.mark.asyncio
async def test_create_pool_retry_logic():
    """Test retry logic on failure"""
    mock_conn = AsyncMock()
    mock_conn.fetchval = AsyncMock(return_value=1)
    mock_pool = MagicMock()
    mock_pool.acquire.return_value = AsyncAcquireContext(mock_conn)

    with patch(
        "src.database.asyncpg.create_pool", new_callable=AsyncMock
    ) as mock_create_pool:
        mock_create_pool.side_effect = [
            Exception("Connection failed"),
            Exception("Connection failed"),
            mock_pool,
        ]

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            pool = await create_pool(max_retries=3, retry_delay=0.1)

            assert pool == mock_pool
            assert mock_create_pool.call_count == 3
            assert mock_sleep.await_count == 2


@pytest.mark.asyncio
async def test_create_pool_exponential_backoff():
    """Test exponential backoff retry"""
    with patch(
        "src.database.asyncpg.create_pool", new_callable=AsyncMock
    ) as mock_create_pool:
        mock_create_pool.side_effect = Exception("Connection failed")

        sleep_calls = []

        async def mock_sleep(delay):
            sleep_calls.append(delay)

        with patch("asyncio.sleep", side_effect=mock_sleep):
            pool = await create_pool(max_retries=3, retry_delay=1)

            assert pool is None
            # Check exponential backoff: 1, 2 seconds (between attempts)
            assert sleep_calls == [1, 2]


@pytest.mark.asyncio
async def test_get_pool_before_initialization():
    """Test get_pool raises error if pool not initialized"""
    # Reset pool
    import src.database

    src.database._pool = None

    with pytest.raises(RuntimeError, match="Database pool not initialized"):
        get_pool()


@pytest.mark.asyncio
async def test_check_pool_health_healthy():
    """Test pool health check when healthy"""
    mock_pool = MagicMock()
    mock_pool.get_size.return_value = 10
    mock_pool.get_idle_size.return_value = 5

    mock_conn = AsyncMock()
    mock_conn.fetchval = AsyncMock(return_value=1)
    mock_pool.acquire.return_value = AsyncAcquireContext(mock_conn)

    with patch("src.database._pool", mock_pool):
        health = await check_pool_health()

    assert health["status"] == "healthy"
    assert health["pool_size"] == 10
    assert health["pool_idle_size"] == 5
    assert "response_time_ms" in health


@pytest.mark.asyncio
async def test_check_pool_health_unhealthy():
    """Test pool health check when unhealthy"""
    import src.database

    src.database._pool = None

    health = await check_pool_health()

    assert health["status"] == "unhealthy"
    assert "error" in health


@pytest.mark.asyncio
async def test_get_db_connection_context_manager():
    """Test database connection context manager"""
    mock_pool = MagicMock()
    mock_conn = AsyncMock()
    mock_pool.acquire.return_value = AsyncAcquireContext(mock_conn)

    with patch("src.database.get_pool", return_value=mock_pool):
        async with get_db_connection() as conn:
            assert conn == mock_conn


@pytest.mark.asyncio
async def test_close_pool_gracefully():
    """Test graceful pool closure"""
    mock_pool = MagicMock()
    mock_pool.terminate = AsyncMock()

    import src.database

    src.database._pool = mock_pool

    await close_pool()

    mock_pool.terminate.assert_called_once()
    assert src.database._pool is None
