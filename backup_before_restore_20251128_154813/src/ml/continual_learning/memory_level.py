"""
Memory Level - Single level in Continuum Memory System

Implements a single temporal scale in the Nested Learning paradigm.
Each level has its own update frequency and learning rate.

Based on:
- Nested Learning paper (NeurIPS 2025)
- Hope architecture (self-modifying recurrent)
"""

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import numpy as np

from src.utils.structured_logging import StructuredLogger

from .types import LevelStats, MemoryEntry, MemoryKey, SurpriseScore

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
                f"learning_rate must be in [0, 1], got {self.learning_rate}"
            )
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

    Example:
        >>> config = MemoryLevelConfig(
        ...     name="fast",
        ...     update_freq=1,
        ...     learning_rate=0.001
        ... )
        >>> level = MemoryLevel(config)
        >>> embedding = level.encode("some data", {})
        >>> level.update("key1", "some data", surprise=0.8)
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
            name=config.name, update_freq=config.update_freq, frozen=config.frozen
        )

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

        This is a placeholder - subclasses should override with
        actual encoding logic (e.g., using neural networks).

        Args:
            data: Input data to encode
            context: Additional context (age, type, etc.)

        Returns:
            Embedding vector
        """
        self.stats.total_encodes += 1

        # Placeholder: return random embedding
        # Subclasses should override with actual model
        return np.random.rand(768).astype("float32")

    def should_update(self, surprise: SurpriseScore) -> bool:
        """
        Determine if this level should update based on surprise

        Key insight from Nested Learning:
        - Only update when surprise exceeds threshold
        - Respect update frequency
        - Never update if frozen

        Args:
            surprise: Surprise score (0-1)

        Returns:
            True if should update
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

        Args:
            key: Memory key
            data: New data
            surprise: Surprise score (0-1)
        """
        if not self.should_update(surprise):
            return

        # Encode new data
        embedding = self.encode(data, {})

        # Store
        self.memory[key] = embedding
        self.metadata[key] = MemoryEntry(
            key=key,
            data=data,
            surprise=surprise,
            step=self.step_count,
            timestamp=time.time(),
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
            extra={
                "key": key,
                "surprise": surprise,
                "step": self.step_count,
                "memory_size": len(self.memory),
            },
        )

    def get(self, key: MemoryKey) -> Optional[np.ndarray]:
        """
        Get embedding by key

        Args:
            key: Memory key

        Returns:
            Embedding vector or None if not found
        """
        self.stats.total_retrievals += 1
        return self.memory.get(key)

    def get_metadata(self, key: MemoryKey) -> Optional[MemoryEntry]:
        """
        Get metadata by key

        Args:
            key: Memory key

        Returns:
            Memory entry or None if not found
        """
        return self.metadata.get(key)

    def get_stats(self) -> LevelStats:
        """
        Get level statistics

        Returns:
            Statistics object
        """
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

        logger.debug(
            f"Evicted oldest entry from {self.config.name}", extra={"key": oldest_key}
        )

    def clear(self):
        """Clear all memory"""
        self.memory.clear()
        self.metadata.clear()
        logger.info("Cleared level {self.config.name}")

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
