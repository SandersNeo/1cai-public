"""
Continuum Memory System (CMS)

Core implementation of Nested Learning paradigm.
Multi-level memory with different update frequencies.

Based on Google Research NeurIPS 2025 paper:
"Nested Learning: The Illusion of Deep Learning Architectures"
"""

import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from src.utils.structured_logging import StructuredLogger

from .memory_level import MemoryLevel, MemoryLevelConfig
from .types import CMSStats, MemoryKey, SurpriseScore
from .vector_index import VectorIndex

logger = StructuredLogger(__name__).logger


class ContinuumMemorySystem:
    """
    Continuum Memory System - Multi-level memory with different temporal scales

    Key concepts from Nested Learning:
    - Multiple levels with different update frequencies
    - Surprise-based selective updates
    - Weighted combination of levels
    - Self-referential optimization

    Example:
        >>> cms = ContinuumMemorySystem([
        ...     ("fast", 1, 0.001),
        ...     ("slow", 100, 0.0001)
        ... ])
        >>> embedding = cms.encode_multi_level("data", {})
        >>> cms.update_level("fast", "key1", "data", surprise=0.8)
    """

    def __init__(
            self, levels: List[Tuple[str, int, float]], embedding_dim: int = 768):
        """
        Initialize CMS

        Args:
            levels: List of (name, update_freq, learning_rate) tuples
                   Example: [("fast", 1, 0.001), ("slow", 100, 0.0001)]
            embedding_dim: Dimension of embeddings
        """
        self.embedding_dim = embedding_dim
        self.levels: Dict[str, MemoryLevel] = {}

        # Create levels
        for name, update_freq, lr in levels:
            config = MemoryLevelConfig(
                name=name, update_freq=update_freq, learning_rate=lr
            )
            self.levels[name] = self._create_level(config)

        # Vector index for similarity search
        self.index = VectorIndex(dimension=embedding_dim)

        # Global step counter
        self.global_step = 0

        logger.info(
            "Created Continuum Memory System",
            extra={
                "num_levels": len(self.levels),
                "level_names": list(self.levels.keys()),
                "embedding_dim": embedding_dim,
            },
        )

    def _create_level(self, config: MemoryLevelConfig) -> MemoryLevel:
        """
        Create memory level

        Override in subclasses for custom level types

        Args:
            config: Level configuration

        Returns:
            Memory level instance
        """
        return MemoryLevel(config)

    def store(
        self,
        level_name: str,
        key: MemoryKey,
        data: Any,
        embedding: Optional[np.ndarray] = None,
    ):
        """
        Store data at specific level

        Args:
            level_name: Name of level to store at
            key: Unique key for data
            data: Data to store
            embedding: Pre-computed embedding (optional)
        """
        level = self.levels.get(level_name)
        if not level:
            raise ValueError(f"Unknown level: {level_name}")

        # Encode if embedding not provided
        if embedding is None:
            embedding = level.encode(data, {})

        # Store in level
        level.memory[key] = embedding
        level.metadata[key] = {
            "data": data,
            "step": self.global_step,
            "timestamp": time.time(),
        }

        # Add to vector index
        self.index.add(key, embedding, metadata={"level": level_name})

        logger.debug(
            f"Stored in level {level_name}",
            extra={
                "key": key,
                "level": level_name})

    def retrieve(
        self, query: Any, level_name: str, k: int = 5
    ) -> List[Tuple[MemoryKey, float, Any]]:
        """
        Retrieve similar items from specific level

        Args:
            query: Query data
            level_name: Level to search in
            k: Number of results

        Returns:
            List of (key, similarity, data) tuples
        """
        level = self.levels.get(level_name)
        if not level:
            raise ValueError(f"Unknown level: {level_name}")

        # Encode query
        query_emb = level.encode(query, {})

        # Search in index
        results = self.index.search(
            query_emb, k=k, filter_fn=lambda meta: meta.get("level") == level_name)

        # Return with data
        output = []
        for key, sim in results:
            if key in level.metadata:
                data = level.metadata[key].get("data")
                output.append((key, sim, data))

        return output

    def retrieve_similar(
        self, query: Any, levels: List[str], k: int = 5
    ) -> Dict[str, List[Tuple[MemoryKey, float, Any]]]:
        """
        Retrieve from multiple levels

        Args:
            query: Query data
            levels: List of level names
            k: Results per level

        Returns:
            Dict mapping level_name -> results
        """
        results = {}
        for level_name in levels:
            if level_name in self.levels:
                results[level_name] = self.retrieve(query, level_name, k)
        return results

    def update_level(
            self,
            level_name: str,
            key: MemoryKey,
            data: Any,
            surprise: SurpriseScore):
        """
        Update specific level with new data

        Args:
            level_name: Level to update
            key: Data key
            data: New data
            surprise: Surprise score (0-1)
        """
        level = self.levels.get(level_name)
        if not level:
            raise ValueError(f"Unknown level: {level_name}")

        # Update level (will check surprise threshold internally)
        level.update(key, data, surprise)

    def encode_multi_level(
        self, data: Any, context: Dict, weights: Optional[Dict[str, float]] = None
    ) -> np.ndarray:
        """
        Encode using weighted combination of all levels

        This is the key insight from Nested Learning:
        combine multiple temporal scales with context-aware weighting

        Args:
            data: Data to encode
            context: Context for weighting
            weights: Optional manual weights per level

        Returns:
            Combined embedding
        """
        if weights is None:
            weights = self._compute_weights(context)

        # Encode at each level
        embeddings = {}
        for level_name, level in self.levels.items():
            embeddings[level_name] = level.encode(data, context)

        # Weighted combination
        combined = np.zeros(self.embedding_dim, dtype="float32")
        total_weight = sum(weights.values())

        if total_weight == 0:
            # Equal weights if all zero
            total_weight = len(weights)
            weights = {k: 1.0 for k in weights.keys()}

        for level_name, emb in embeddings.items():
            weight = weights.get(level_name, 0.0) / total_weight
            combined += weight * emb

        return combined

    def _compute_weights(self, context: Dict) -> Dict[str, float]:
        """
        Compute level weights based on context

        Override in subclasses for custom weighting logic

        Args:
            context: Context dictionary

        Returns:
            Dict mapping level_name -> weight
        """
        # Default: equal weights
        n = len(self.levels)
        return {name: 1.0 / n for name in self.levels.keys()}

    def step(self):
        """Advance global step counter"""
        self.global_step += 1
        for level in self.levels.values():
            level.step()

    def get_stats(self) -> CMSStats:
        """
        Get statistics for all levels

        Returns:
            Statistics object
        """
        level_stats = {name: level.get_stats()
                       for name, level in self.levels.items()}

        total_memory = sum(len(level.memory) for level in self.levels.values())

        return CMSStats(
            global_step=self.global_step,
            total_levels=len(self.levels),
            total_memory_size=total_memory,
            index_size=self.index.size(),
            levels=level_stats,
        )

    def clear(self):
        """Clear all levels and index"""
        for level in self.levels.values():
            level.clear()
        self.index.clear()
        self.global_step = 0
        logger.info("Cleared CMS")

    def __repr__(self) -> str:
        """String representation"""
        return (
            f"ContinuumMemorySystem("
            f"levels={len(self.levels)}, "
            f"step={self.global_step}, "
            f"total_memory={sum(len(l) for l in self.levels.values())})"
        )
