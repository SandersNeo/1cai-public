"""
Redis Client for Nested Learning (Hot Memory)

Handles:
- Session storage (L1)
- Daily patterns (L2)
- Metrics and counters
"""

import json
import os
from typing import Any, Dict, List, Optional, Union

import redis
from src.config import settings
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class RedisClient:
    """
    Redis client wrapper for Nested Learning persistence.

    Implements:
    - Connection management
    - JSON serialization/deserialization
    - Key namespacing
    """

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, password: Optional[str] = None):
        """
        Initialize Redis client.

        Args:
            host: Redis host
            port: Redis port
            db: Redis DB index
            password: Redis password
        """
        self.host = host or settings.redis_host
        self.port = int(port or settings.redis_port)
        self.db = int(db or settings.redis_db)
        self.password = password or settings.redis_password

        self._client: Optional[redis.Redis] = None
        self.namespace = "nested_learning"

    def connect(self) -> bool:
        """
        Connect to Redis.

        Returns:
            True if connected, False otherwise
        """
        try:
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,  # Auto-decode bytes to strings
            )
            # Test connection
            self._client.ping()
            logger.info("Connected to Redis", extra={"host": self.host, "port": self.port})
            return True
        except redis.ConnectionError as e:
            logger.error("Failed to connect to Redis", extra={"error": str(e)})
            self._client = None
            return False

    def _get_key(self, key: str) -> str:
        """Get namespaced key"""
        return f"{self.namespace}:{key}"

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set key value.

        Args:
            key: Key name
            value: Value (will be JSON serialized if dict/list)
            ttl: Time to live in seconds

        Returns:
            True if successful
        """
        if not self._client:
            if not self.connect():
                return False

        full_key = self._get_key(key)

        if isinstance(value, (dict, list)):
            try:
                value = json.dumps(value)
            except Exception as e:
                logger.error("Failed to serialize value", extra={"key": key, "error": str(e)})
                return False

        try:
            return bool(self._client.set(full_key, value, ex=ttl))
        except Exception as e:
            logger.error("Redis set failed", extra={"key": key, "error": str(e)})
            return False

    def get(self, key: str) -> Any:
        """
        Get key value.

        Args:
            key: Key name

        Returns:
            Value (parsed JSON if applicable) or None
        """
        if not self._client:
            if not self.connect():
                return None

        full_key = self._get_key(key)

        try:
            value = self._client.get(full_key)
            if value is None:
                return None

            # Try to parse JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            logger.error("Redis get failed", extra={"key": key, "error": str(e)})
            return None

    def delete(self, key: str) -> bool:
        """Delete key"""
        if not self._client:
            if not self.connect():
                return False

        full_key = self._get_key(key)
        try:
            return bool(self._client.delete(full_key))
        except Exception as e:
            logger.error("Redis delete failed", extra={"key": key, "error": str(e)})
            return False

    def lpush(self, key: str, value: Any) -> bool:
        """Push to list (left)"""
        if not self._client:
            if not self.connect():
                return False

        full_key = self._get_key(key)

        if isinstance(value, (dict, list)):
            value = json.dumps(value)

        try:
            return bool(self._client.lpush(full_key, value))
        except Exception as e:
            logger.error("Redis lpush failed", extra={"key": key, "error": str(e)})
            return False

    def lrange(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """Get list range"""
        if not self._client:
            if not self.connect():
                return []

        full_key = self._get_key(key)

        try:
            items = self._client.lrange(full_key, start, end)
            parsed_items = []
            for item in items:
                try:
                    parsed_items.append(json.loads(item))
                except (json.JSONDecodeError, TypeError):
                    parsed_items.append(item)
            return parsed_items
        except Exception as e:
            logger.error("Redis lrange failed", extra={"key": key, "error": str(e)})
            return []

    def expire(self, key: str, ttl: int) -> bool:
        """Set expiration"""
        if not self._client:
            if not self.connect():
                return False

        full_key = self._get_key(key)
        try:
            return bool(self._client.expire(full_key, ttl))
        except Exception as e:
            logger.error("Redis expire failed", extra={"key": key, "error": str(e)})
            return False

    def keys(self, pattern: str) -> List[str]:
        """
        Get keys matching pattern.
        Handles namespacing automatically.

        Args:
            pattern: Key pattern (e.g. "cms:*")

        Returns:
            List of keys (without namespace prefix)
        """
        if not self._client:
            if not self.connect():
                return []

        full_pattern = self._get_key(pattern)

        try:
            full_keys = self._client.keys(full_pattern)
            # Strip namespace
            prefix_len = len(self.namespace) + 1  # +1 for colon
            return [k[prefix_len:] for k in full_keys]
        except Exception as e:
            logger.error("Redis keys failed", extra={"pattern": pattern, "error": str(e)})
            return []
