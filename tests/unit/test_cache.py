# [NEXUS IDENTITY] ID: 3493476252035207872 | DATE: 2025-11-19

"""
Unit tests for multi-layer cache
Best Practices: Test LRU, circuit breaker, and cache operations
"""

import asyncio
from unittest.mock import AsyncMock

import pytest

from src.cache.multi_layer_cache import (CircuitBreaker, LRUCache,
                                         MultiLayerCache)


@pytest.mark.asyncio
async def test_lru_cache_get_set():
    """Test LRU cache get and set operations"""
    cache = LRUCache(max_size=3)

    cache.set("key1", "value1")
    cache.set("key2", "value2")

    assert cache.get("key1") == "value1"
    assert cache.get("key2") == "value2"
    assert cache.get("key3") is None


@pytest.mark.asyncio
async def test_lru_cache_eviction():
    """Test LRU eviction when cache is full"""
    cache = LRUCache(max_size=2)

    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")  # Should evict key1

    assert cache.get("key1") is None  # Evicted
    assert cache.get("key2") == "value2"
    assert cache.get("key3") == "value3"


@pytest.mark.asyncio
async def test_lru_cache_ttl():
    """Test LRU cache TTL expiration"""

    cache = LRUCache(max_size=10)

    cache.set("key1", "value1", ttl_seconds=1)

    assert cache.get("key1") == "value1"

    # Wait for expiration
    await asyncio.sleep(1.1)

    assert cache.get("key1") is None


@pytest.mark.asyncio
async def test_circuit_breaker_closed_state():
    """Test circuit breaker in closed state"""
    cb = CircuitBreaker(failure_threshold=3)

    assert cb.can_attempt() is True
    cb.record_success()
    assert cb.state == "closed"


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_threshold():
    """Test circuit breaker opens after failure threshold"""
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)

    cb.record_failure()
    cb.record_failure()
    assert cb.can_attempt() is True  # Still closed

    cb.record_failure()
    assert cb.state == "open"
    assert cb.can_attempt() is False  # Now open


@pytest.mark.asyncio
async def test_circuit_breaker_recovery():
    """Test circuit breaker recovery after timeout"""

    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)

    # Open circuit breaker
    cb.record_failure()
    cb.record_failure()
    assert cb.state == "open"
    assert cb.can_attempt() is False

    # Wait for recovery timeout
    await asyncio.sleep(1.1)

    assert cb.can_attempt() is True
    assert cb.state == "half_open"


@pytest.mark.asyncio
async def test_multilayer_cache_l1_hit():
    """Test multi-layer cache L1 hit"""
    cache = MultiLayerCache(redis_client=None)

    await cache.set("key1", "value1")

    value = await cache.get("key1")

    assert value == "value1"
    assert cache.hits["l1"] == 1
    assert cache.misses == 0


@pytest.mark.asyncio
async def test_multilayer_cache_l2_hit():
    """Test multi-layer cache L2 hit"""
    mock_redis = AsyncMock()
    mock_redis.get.return_value = '{"key": "value"}'

    cache = MultiLayerCache(redis_client=mock_redis)

    value = await cache.get("key1")

    assert value == {"key": "value"}
    assert cache.hits["l2"] == 1
    # Should promote to L1
    assert cache.memory_cache.get("key1") == {"key": "value"}


@pytest.mark.asyncio
async def test_multilayer_cache_miss():
    """Test multi-layer cache miss"""
    cache = MultiLayerCache(redis_client=None)

    value = await cache.get("nonexistent")

    assert value is None
    assert cache.misses == 1


@pytest.mark.asyncio
async def test_multilayer_cache_circuit_breaker():
    """Test cache with Redis circuit breaker"""
    mock_redis = AsyncMock()
    mock_redis.get.side_effect = Exception("Redis error")

    cache = MultiLayerCache(redis_client=mock_redis, redis_circuit_breaker_threshold=2)

    # First failure
    await cache.get("key1")
    assert cache.redis_circuit_breaker.failure_count == 1

    # Second failure - should open circuit
    await cache.get("key1")
    assert cache.redis_circuit_breaker.state == "open"
    assert cache.redis_circuit_breaker.can_attempt() is False


@pytest.mark.asyncio
async def test_multilayer_cache_stats():
    """Test cache statistics"""
    cache = MultiLayerCache(redis_client=None)

    await cache.set("key1", "value1")
    await cache.get("key1")
    await cache.get("nonexistent")

    stats = cache.get_stats()

    assert stats["total_requests"] == 2
    assert stats["hits"]["l1"] == 1
    assert stats["misses"] == 1
    assert stats["hit_rate"] == 0.5
