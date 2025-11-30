"""
Memory Level - Single level in Continuum Memory System

Implements a single temporal scale in the Nested Learning paradigm.
Each level has its own update frequency and learning rate.
"""

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import numpy as np

from src.utils.structured_logging import StructuredLogger
from src.modules.nested_learning.domain.types import LevelStats, MemoryEntry, MemoryKey, SurpriseScore

logger = StructuredLogger(__name__).logger


@dataclass
class MemoryLevelConfig:
    """Configuration for a memory level"""

    name: str
    update_freq: int  # Update every N steps
    learning_rate: float  # Learning rate for this level
    threshold: float = 0.5  # Surprise threshold for updates
    capacity: int = 10000  # Max items to store
    frozen: bool = False  # If True, never update

    def __post_init__(self):
        """Validate configuration"""
        if self.update_freq < 1:
            raise ValueError(f"update_freq must be >= 1, got {self.update_freq}")
        if not 0.0 <= self.learning_rate <= 1.0:
            raise ValueError(
                f"learning_rate must be in [0, 1], got {self.learning_rate}")
        if not 0.0 <= self.threshold <= 1.0:
            raise ValueError(f"threshold must be in [0, 1], got {self.threshold}")
        if self.capacity < 1:
            raise ValueError(f"capacity must be >= 1, got {self.capacity}")


class MemoryLevel:
    """
    Single level in Continuum Memory System

    Implements:
    - Encoding at specific temporal scale
    - Selective updates based on surprise
    - Statistics tracking
    - Capacity management with eviction
    """

    def __init__(self, config: MemoryLevelConfig):
        """
        Initialize memory level

        Args:
            config: Level configuration
        """
        self.config = config
        self.step_count = 0
        self.update_count = 0

        # Storage
        self.memory: Dict[MemoryKey, np.ndarray] = {}
        self.metadata: Dict[MemoryKey, MemoryEntry] = {}

        # Statistics
        self.stats = LevelStats(
            name=config.name, update_freq=config.update_freq, frozen=config.frozen)

        logger.info(
            f"Created memory level: {config.name}",
            extra={
                "update_freq": config.update_freq,
                "learning_rate": config.learning_rate,
                "capacity": config.capacity,
                "frozen": config.frozen,
            },
        )

    def encode(self, data: Any, context: Dict) -> np.ndarray:
        """
        Encode data at this level's temporal scale
        """
        self.stats.total_encodes += 1

        # Placeholder: return random embedding
        # Subclasses should override with actual model
        return np.random.rand(768).astype("float32")

    def should_update(self, surprise: SurpriseScore) -> bool:
        """
        Determine if this level should update based on surprise
        """
        if self.config.frozen:
            return False

        # Check frequency
        if self.step_count % self.config.update_freq != 0:
            return False

        # Check surprise threshold
        return surprise > self.config.threshold

    def update(self, key: MemoryKey, data: Any, surprise: SurpriseScore):
        """
        Update memory at this level
        """
        if not self.should_update(surprise):
            return

        # Encode new data
        embedding = self.encode(data, {})

        # Store
        self.memory[key] = embedding
        self.metadata[key] = MemoryEntry(
            key=key, data=data, surprise=surprise, step=self.step_count, timestamp=time.time()
        )

        # Update stats
        self.update_count += 1
        self.stats.total_updates += 1
        self.stats.last_update_step = self.step_count

        # Update average surprise
        n = self.stats.total_updates
        self.stats.avg_surprise = (self.stats.avg_surprise * (n - 1) + surprise) / n

        # Evict if over capacity
        if len(self.memory) > self.config.capacity:
            self._evict_oldest()

        logger.debug(
            f"Updated level {self.config.name}",
            extra={"key": key, "surprise": surprise,
                "step": self.step_count, "memory_size": len(self.memory)},
        )

    def get(self, key: MemoryKey) -> Optional[np.ndarray]:
        """Get embedding by key"""
        self.stats.total_retrievals += 1
        return self.memory.get(key)

    def get_metadata(self, key: MemoryKey) -> Optional[MemoryEntry]:
        """Get metadata by key"""
        return self.metadata.get(key)

    def get_stats(self) -> LevelStats:
        """Get level statistics"""
        self.stats.memory_size = len(self.memory)
        return self.stats

    def step(self):
        """Increment step counter"""
        self.step_count += 1

    def _evict_oldest(self):
        """Evict oldest entry to maintain capacity"""
        if not self.metadata:
            return

        # Find oldest entry
        oldest_key = min(self.metadata.keys(), key=lambda k: self.metadata[k].timestamp)

        # Remove
        del self.memory[oldest_key]
        del self.metadata[oldest_key]

        logger.debug(f"Evicted oldest entry from {self.config.name}", extra={
                     "key": oldest_key})

    def clear(self):
        """Clear all memory"""
        self.memory.clear()
        self.metadata.clear()
        logger.info(f"Cleared level {self.config.name}")

    def __len__(self) -> int:
        """Get number of entries"""
        return len(self.memory)

    def __repr__(self) -> str:
        """String representation"""
        return (
            f"MemoryLevel(name={self.config.name}, "
            f"size={len(self)}, "
            f"step={self.step_count}, "
            f"updates={self.update_count})"
        )


class RedisMemoryLevel(MemoryLevel):
    """
    Redis-backed Memory Level (Hot/Warm Memory)
    
    Persists data to Redis with TTL support.
    """
    
    def __init__(self, config: MemoryLevelConfig, redis_client):
        """
        Initialize Redis memory level
        
        Args:
            config: Level configuration
            redis_client: RedisClient instance
        """
        super().__init__(config)
        self.client = redis_client
        self.ttl = 86400 if config.name == "session" else 604800  # 1 day or 7 days
        
    def _get_redis_key(self, key: str) -> str:
        return f"cms:level:{self.config.name}:{key}"
        
    def update(self, key: MemoryKey, data: Any, surprise: SurpriseScore):
        """Update with Redis persistence"""
        if not self.should_update(surprise):
            return
            
        # Encode
        embedding = self.encode(data, {})
        
        # Prepare payload
        payload = {
            "data": data,
            "embedding": embedding.tolist(),
            "surprise": surprise,
            "step": self.step_count,
            "timestamp": time.time()
        }
        
        # Store in Redis
        redis_key = self._get_redis_key(key)
        self.client.set(redis_key, payload, ttl=self.ttl)
        
        # Update local stats (cache size is approximate)
        self.update_count += 1
        self.stats.total_updates += 1
        self.stats.last_update_step = self.step_count
        
        logger.debug(f"Persisted to Redis: {self.config.name}", extra={"key": key})

    def get(self, key: MemoryKey) -> Optional[np.ndarray]:
        """Get embedding from Redis"""
        self.stats.total_retrievals += 1
        redis_key = self._get_redis_key(key)
        payload = self.client.get(redis_key)
        
        if payload and "embedding" in payload:
            return np.array(payload["embedding"], dtype="float32")
        return None

    def get_metadata(self, key: MemoryKey) -> Optional[MemoryEntry]:
        """Get metadata from Redis"""
        redis_key = self._get_redis_key(key)
        payload = self.client.get(redis_key)
        
        if payload:
            return MemoryEntry(
                key=key,
                data=payload.get("data"),
                surprise=payload.get("surprise", 0.0),
                step=payload.get("step", 0),
                timestamp=payload.get("timestamp", 0.0)
            )
        return None

    def clear(self):
        """Clear Redis keys for this level"""
        # Note: This is expensive in Redis without scanning. 
        # For now, we just log. In prod, use SCAN.
        logger.warning(f"Clear called on Redis level {self.config.name} - Not fully implemented for safety")

    def __len__(self) -> int:
        return 0  # Cannot easily count without scan


class ChromaMemoryLevel(MemoryLevel):
    """
    ChromaDB-backed Memory Level (Cold Memory)
    
    Persists data to VectorDB for long-term recall.
    """
    
    def __init__(self, config: MemoryLevelConfig, chroma_client):
        """
        Initialize Chroma memory level
        
        Args:
            config: Level configuration
            chroma_client: ChromaClient instance
        """
        super().__init__(config)
        self.client = chroma_client
        self.collection_name = f"cms_level_{config.name}"
        self.client.get_or_create_collection(self.collection_name)
        
    def update(self, key: MemoryKey, data: Any, surprise: SurpriseScore):
        """Update with Chroma persistence"""
        if not self.should_update(surprise):
            return
            
        # Encode
        embedding = self.encode(data, {})
        
        # Prepare metadata
        metadata = {
            "surprise": surprise,
            "step": self.step_count,
            "timestamp": time.time(),
            "type": "memory_entry"
        }
        
        # Store in Chroma
        # Convert data to string if needed
        doc_text = str(data) if not isinstance(data, str) else data
        
        self.client.add_documents(
            collection_name=self.collection_name,
            documents=[doc_text],
            metadatas=[metadata],
            ids=[key],
            embeddings=[embedding.tolist()]
        )
        
        self.update_count += 1
        self.stats.total_updates += 1
        
        logger.debug(f"Persisted to Chroma: {self.config.name}", extra={"key": key})

    def get(self, key: MemoryKey) -> Optional[np.ndarray]:
        """Get embedding from Chroma"""
        self.stats.total_retrievals += 1
        results = self.client.query(
            collection_name=self.collection_name,
            where={"id": key}, # Chroma doesn't support get by ID directly in query easily without ID filter
            n_results=1
        )
        # Note: This is inefficient for single key retrieval in Chroma. 
        # Chroma is optimized for similarity search, not KV.
        # But we implement for compatibility.
        return None # Placeholder as Chroma query returns nearest neighbors

    def __len__(self) -> int:
        return self.client.count(self.collection_name)
