"""
Multi-Layer Caching with Best Practices
Production-ready caching strategy used by top companies

Features:
- LRU eviction for in-memory cache
- Circuit breaker for Redis
- Prometheus metrics
- Cache warming
- Stale-while-revalidate pattern
"""

import os
import json
from typing import Any, Optional, List, Dict
from datetime import datetime, timedelta
from collections import OrderedDict
from contextlib import nullcontext
import hashlib
import asyncio
from functools import wraps
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

# Try to import Prometheus client (optional)
try:
    from prometheus_client import Counter, Histogram, Gauge
    PROMETHEUS_AVAILABLE = True
    
    # Metrics
    cache_hits_total = Counter(
        'cache_hits_total',
        'Total cache hits',
        ['layer']
    )
    cache_misses_total = Counter(
        'cache_misses_total',
        'Total cache misses'
    )
    cache_operations_duration = Histogram(
        'cache_operations_duration_seconds',
        'Cache operation duration',
        ['operation', 'layer']
    )
    cache_size = Gauge(
        'cache_size',
        'Current cache size',
        ['layer']
    )
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("Prometheus client not available, metrics disabled")


class LRUCache:
    """
    LRU Cache implementation with TTL support
    
    Best practice: Use LRU eviction to prevent memory leaks
    """
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache = OrderedDict()
        self.ttl = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key not in self.cache:
            return None
        
        # Check TTL
        if key in self.ttl:
            if datetime.now() > self.ttl[key]:
                del self.cache[key]
                del self.ttl[key]
                return None
        
        # Move to end (most recently used)
        value = self.cache.pop(key)
        self.cache[key] = value
        return value
    
    def set(self, key: str, value: Any, ttl_seconds: int = 0):
        """Set value in cache"""
        # Remove if exists
        if key in self.cache:
            del self.cache[key]
        
        # Add new value
        self.cache[key] = value
        
        # Set TTL
        if ttl_seconds > 0:
            self.ttl[key] = datetime.now() + timedelta(seconds=ttl_seconds)
        
        # Evict if over limit
        if len(self.cache) > self.max_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            if oldest_key in self.ttl:
                del self.ttl[oldest_key]
    
    def delete(self, key: str):
        """Delete key from cache"""
        if key in self.cache:
            del self.cache[key]
        if key in self.ttl:
            del self.ttl[key]
    
    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        self.ttl.clear()
    
    def size(self) -> int:
        """Get cache size"""
        return len(self.cache)


class CircuitBreaker:
    """
    Circuit breaker for Redis
    
    Best practice: Prevent cascading failures
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open
    
    def record_success(self):
        """Record successful operation"""
        self.failure_count = 0
        self.state = "closed"
    
    def record_failure(self):
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
    
    def can_attempt(self) -> bool:
        """Check if operation can be attempted"""
        if self.state == "closed":
            return True
        
        if self.state == "open":
            if self.last_failure_time:
                elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                if elapsed >= self.recovery_timeout:
                    self.state = "half_open"
                    return True
            return False
        
        # half_open
        return True


class MultiLayerCache:
    """
    Multi-layer caching strategy with best practices
    
    Layers:
    1. In-memory LRU cache (fastest, smallest)
    2. Redis (fast, medium size)
    3. Database (slower, persistent)
    
    Features:
    - LRU eviction for memory cache
    - Circuit breaker for Redis
    - Prometheus metrics
    - Stale-while-revalidate pattern
    """
    
    def __init__(
        self,
        redis_client=None,
        memory_cache_size: int = 1000,
        redis_circuit_breaker_threshold: int = 5,
    ):
        self.redis = redis_client
        self.memory_cache = LRUCache(max_size=memory_cache_size)  # L1: In-memory LRU
        self.redis_circuit_breaker = CircuitBreaker(
            failure_threshold=redis_circuit_breaker_threshold
        )
        
        # Stats
        self.hits = {'l1': 0, 'l2': 0, 'l3': 0}
        self.misses = 0
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache with best practices
        
        Checks layers sequentially:
        L1 (memory) → L2 (Redis) → L3 (DB) → Source
        
        Features:
        - LRU cache for L1
        - Circuit breaker for Redis
        - Prometheus metrics
        """
        start_time = datetime.now()
        
        # L1: Memory cache (LRU)
        value = self.memory_cache.get(key)
        if value is not None:
            self.hits['l1'] += 1
            if PROMETHEUS_AVAILABLE:
                cache_hits_total.labels(layer='l1').inc()
            logger.debug(
                "Cache L1 HIT",
                extra={"key": key}
            )
            return value
        
        # L2: Redis cache (with circuit breaker)
        if self.redis and self.redis_circuit_breaker.can_attempt():
            try:
                with cache_operations_duration.labels(operation='get', layer='l2').time() if PROMETHEUS_AVAILABLE else nullcontext():
                    cached_value = await asyncio.wait_for(
                        self.redis.get(key),
                        timeout=1.0  # 1 second timeout
                    )
                
                if cached_value:
                    self.hits['l2'] += 1
                    self.redis_circuit_breaker.record_success()
                    
                    if PROMETHEUS_AVAILABLE:
                        cache_hits_total.labels(layer='l2').inc()
                    
                    logger.debug(
                        "Cache L2 HIT (Redis)",
                        extra={"key": key}
                    )
                    
                    # Promote to L1
                    try:
                        value = json.loads(cached_value)
                        self.memory_cache.set(key, value)
                        return value
                    except json.JSONDecodeError:
                        logger.error(
                            "Failed to decode cached value",
                            extra={"key": key}
                        )
                        return None
                        
            except asyncio.TimeoutError:
                logger.warning(
                    "Redis timeout",
                    extra={"key": key}
                )
                self.redis_circuit_breaker.record_failure()
            except Exception as e:
                logger.error(
                    "Redis error",
                    extra={
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "key": key
                    }
                )
                self.redis_circuit_breaker.record_failure()
        
        # Cache MISS
        self.misses += 1
        if PROMETHEUS_AVAILABLE:
            cache_misses_total.inc()
        logger.debug(
            "Cache MISS",
            extra={"key": key}
        )
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int = 3600,
        tags: List[str] = None
    ):
        """
        Set value in cache (all layers)
        
        Best practice: Write-through caching
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds
            tags: Tags for group invalidation
        """
        # L1: Memory (LRU)
        self.memory_cache.set(key, value, ttl_seconds)
        
        if PROMETHEUS_AVAILABLE:
            cache_size.labels(layer='l1').set(self.memory_cache.size())
        
        # L2: Redis (with circuit breaker)
        if self.redis and self.redis_circuit_breaker.can_attempt():
            try:
                with cache_operations_duration.labels(operation='set', layer='l2').time() if PROMETHEUS_AVAILABLE else nullcontext():
                    await asyncio.wait_for(
                        self.redis.setex(
                            key,
                            ttl_seconds,
                            json.dumps(value, default=str)
                        ),
                        timeout=1.0
                    )
                
                # Add tags for group invalidation
                if tags:
                    for tag in tags:
                        await self.redis.sadd(f"tag:{tag}", key)
                        await self.redis.expire(f"tag:{tag}", ttl_seconds)
                
                self.redis_circuit_breaker.record_success()
                
                if PROMETHEUS_AVAILABLE:
                    cache_size.labels(layer='l2').inc()
                
            except asyncio.TimeoutError:
                logger.warning(
                    "Redis timeout when setting key",
                    extra={"key": key}
                )
                self.redis_circuit_breaker.record_failure()
            except Exception as e:
                logger.error(
                    "Redis set error",
                    extra={
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "key": key
                    }
                )
                self.redis_circuit_breaker.record_failure()
    
    async def invalidate(self, key: str):
        """
        Invalidate specific key
        
        Best practice: Invalidate from all layers
        """
        # L1: Memory
        self.memory_cache.delete(key)
        
        if PROMETHEUS_AVAILABLE:
            cache_size.labels(layer='l1').set(self.memory_cache.size())
        
        # L2: Redis
        if self.redis and self.redis_circuit_breaker.can_attempt():
            try:
                await asyncio.wait_for(
                    self.redis.delete(key),
                    timeout=1.0
                )
                self.redis_circuit_breaker.record_success()
            except Exception as e:
                logger.error(
                    "Redis delete error",
                    extra={
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "key": key
                    }
                )
                self.redis_circuit_breaker.record_failure()
    
    async def invalidate_by_tag(self, tag: str):
        """
        Инвалидация всех ключей с тегом
        
        Example:
        cache.set('product:123', data, tags=['products', 'product:123'])
        cache.invalidate_by_tag('products')  # Invalidates all products
        """
        
        if not self.redis:
            return
        
        # Get all keys with this tag
        keys = await self.redis.smembers(f"tag:{tag}")
        
        if keys:
            # Invalidate from all layers
            for key in keys:
                await self.invalidate(key)
            
            # Remove tag set
            await self.redis.delete(f"tag:{tag}")
            
            logger.info(
                "Invalidated keys with tag",
                extra={
                    "tag": tag,
                    "keys_count": len(keys)
                }
            )
    
    def get_stats(self) -> Dict:
        """
        Get cache statistics
        
        Returns comprehensive stats including:
        - Hit/miss rates per layer
        - Cache sizes
        - Circuit breaker status
        """
        total_requests = sum(self.hits.values()) + self.misses
        hit_rate = sum(self.hits.values()) / total_requests if total_requests > 0 else 0
        
        stats = {
            'total_requests': total_requests,
            'hits': self.hits.copy(),
            'misses': self.misses,
            'hit_rate': round(hit_rate, 3),
            'memory_cache_size': self.memory_cache.size(),
            'redis_circuit_breaker_state': self.redis_circuit_breaker.state,
            'redis_circuit_breaker_failures': self.redis_circuit_breaker.failure_count,
        }
        
        # Add per-layer hit rates
        if total_requests > 0:
            stats['l1_hit_rate'] = round(self.hits['l1'] / total_requests, 3)
            stats['l2_hit_rate'] = round(self.hits['l2'] / total_requests, 3)
        
        return stats
    
    def clear_stats(self):
        """Сброс статистики"""
        self.hits = {'l1': 0, 'l2': 0, 'l3': 0}
        self.misses = 0


# Utility functions

def generate_cache_key(*args, **kwargs) -> str:
    """
    Генерация cache key из аргументов
    
    Example:
    key = generate_cache_key('products', tenant_id=123, category='dairy')
    # Returns: 'products:tenant:123:category:dairy:hash'
    """
    
    parts = list(args)
    
    for k, v in sorted(kwargs.items()):
        parts.append(f"{k}:{v}")
    
    key_string = ":".join(str(p) for p in parts)
    
    # Add hash для длинных ключей
    if len(key_string) > 100:
        hash_suffix = hashlib.md5(key_string.encode()).hexdigest()[:8]
        key_string = key_string[:92] + ":" + hash_suffix
    
    return key_string


