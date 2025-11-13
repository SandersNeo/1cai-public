"""
Multi-Layer Caching
Эффективная стратегия кеширования на нескольких уровнях
"""

import os
import json
import logging
from typing import Any, Optional, List, Dict
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)


class MultiLayerCache:
    """
    Multi-layer caching strategy
    
    Layers:
    1. In-memory (fastest, smallest)
    2. Redis (fast, medium size)
    3. Database (slower, persistent)
    """
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.memory_cache = {}  # L1: In-memory
        self.memory_cache_ttl = {}
        
        # Stats
        self.hits = {'l1': 0, 'l2': 0, 'l3': 0}
        self.misses = 0
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Получение значения из кеша
        
        Проверяет layers последовательно:
        L1 (memory) → L2 (Redis) → L3 (DB) → Source
        """
        
        # L1: Memory cache
        if key in self.memory_cache:
            # Check TTL
            if key in self.memory_cache_ttl:
                if datetime.now() > self.memory_cache_ttl[key]:
                    # Expired
                    del self.memory_cache[key]
                    del self.memory_cache_ttl[key]
                else:
                    # Valid
                    self.hits['l1'] += 1
                    logger.debug(f"Cache L1 HIT: {key}")
                    return self.memory_cache[key]
            else:
                self.hits['l1'] += 1
                return self.memory_cache[key]
        
        # L2: Redis cache
        if self.redis:
            try:
                cached_value = await self.redis.get(key)
                if cached_value:
                    self.hits['l2'] += 1
                    logger.debug(f"Cache L2 HIT (Redis): {key}")
                    
                    # Promote to L1
                    value = json.loads(cached_value)
                    self.memory_cache[key] = value
                    
                    return value
            except Exception as e:
                logger.error(f"Redis error: {e}")
        
        # Cache MISS
        self.misses += 1
        logger.debug(f"Cache MISS: {key}")
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int = 3600,
        tags: List[str] = None
    ):
        """
        Сохранение в кеш (все layers)
        
        Args:
            key: Ключ
            value: Значение
            ttl_seconds: Time to live
            tags: Теги для групповой инвалидации
        """
        
        # L1: Memory
        self.memory_cache[key] = value
        if ttl_seconds > 0:
            self.memory_cache_ttl[key] = datetime.now() + timedelta(seconds=ttl_seconds)
        
        # L2: Redis
        if self.redis:
            try:
                await self.redis.setex(
                    key,
                    ttl_seconds,
                    json.dumps(value, default=str)
                )
                
                # Add tags
                if tags:
                    for tag in tags:
                        await self.redis.sadd(f"tag:{tag}", key)
                        await self.redis.expire(f"tag:{tag}", ttl_seconds)
                
            except Exception as e:
                logger.error(f"Redis set error: {e}")
    
    async def invalidate(self, key: str):
        """Инвалидация конкретного ключа"""
        
        # L1
        if key in self.memory_cache:
            del self.memory_cache[key]
        if key in self.memory_cache_ttl:
            del self.memory_cache_ttl[key]
        
        # L2
        if self.redis:
            await self.redis.delete(key)
    
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
            
            logger.info(f"Invalidated {len(keys)} keys with tag '{tag}'")
    
    def get_stats(self) -> Dict:
        """Статистика кеша"""
        
        total_requests = sum(self.hits.values()) + self.misses
        hit_rate = sum(self.hits.values()) / total_requests if total_requests > 0 else 0
        
        return {
            'total_requests': total_requests,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': round(hit_rate, 3),
            'memory_cache_size': len(self.memory_cache)
        }
    
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


