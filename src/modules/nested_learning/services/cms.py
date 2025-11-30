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

from src.modules.nested_learning.services.memory_level import MemoryLevel, MemoryLevelConfig
from src.modules.nested_learning.domain.types import CMSStats, MemoryKey, SurpriseScore, MemoryEntry
from src.modules.nested_learning.infrastructure.vector_index import VectorIndex

logger = StructuredLogger(__name__).logger


class ContinuumMemorySystem:
    """
    Continuum Memory System - Multi-level memory with different temporal scales
    """

    def __init__(self, levels: List[Tuple[str, int, float]], embedding_dim: int = 768):
        """
        Initialize CMS with Persistence

        Args:
            levels: List of (name, update_freq, learning_rate) tuples
            embedding_dim: Dimension of embeddings
        """
        self.embedding_dim = embedding_dim
        self.levels: Dict[str, MemoryLevel] = {}

        # Initialize Persistence Clients
        try:
            from src.services.storage.redis_client import RedisClient
            from src.services.storage.chroma_client import ChromaClient

            self.redis_client = RedisClient()
            self.chroma_client = ChromaClient()

            # Connect
            self.redis_connected = self.redis_client.connect()
            self.chroma_connected = self.chroma_client.connect()

        except ImportError:
            logger.warning("Persistence clients not found, falling back to in-memory")
            self.redis_connected = False
            self.chroma_connected = False

        # Create levels
        for name, update_freq, lr in levels:
            config = MemoryLevelConfig(name=name, update_freq=update_freq, learning_rate=lr)
            self.levels[name] = self._create_level(config)

        # Vector index for similarity search
        self.index = VectorIndex(dimension=embedding_dim)

        # Global step counter
        self.global_step = 0

        logger.info(
            "Created Continuum Memory System",
            extra={
                "num_levels": len(self.levels),
                "persistence": {"redis": self.redis_connected, "chroma": self.chroma_connected},
            },
        )

        # Reload from persistence if available
        self._reload_from_persistence()

    def _reload_from_persistence(self):
        """
        Reload vectors from persistent storage into in-memory index.
        Crucial for 'Strike 2' persistence to work across restarts.
        """
        from src.modules.nested_learning.services.memory_level import RedisMemoryLevel

        for name, level in self.levels.items():
            if isinstance(level, RedisMemoryLevel) and self.redis_connected:
                try:
                    # Scan for keys in this level
                    pattern = f"cms:level:{name}:*"
                    keys = self.redis_client.keys(pattern)

                    count = 0
                    for full_key in keys:
                        # full_key is like "cms:level:session:abc..."
                        # we need just "abc..."
                        key = full_key.split(":")[-1]

                        # Get embedding from level
                        emb = level.get(key)
                        if emb is not None:
                            # Add to index
                            self.index.add(key, emb, metadata={"level": name})
                            count += 1

                    if count > 0:
                        logger.info(f"Reloaded {count} items from Redis for level '{name}'")

                except Exception as e:
                    logger.error(f"Failed to reload level '{name}' from Redis: {e}")

    def _create_level(self, config: MemoryLevelConfig) -> MemoryLevel:
        """
        Create memory level with appropriate persistence backend
        """
        from src.modules.nested_learning.services.memory_level import RedisMemoryLevel, ChromaMemoryLevel

        # Determine storage type based on level name
        if config.name in ["session", "daily"] and self.redis_connected:
            return RedisMemoryLevel(config, self.redis_client)

        elif config.name in ["historical", "domain"] and self.chroma_connected:
            return ChromaMemoryLevel(config, self.chroma_client)

        else:
            # Fallback to in-memory
            return MemoryLevel(config)

    def store(self, level_name: str, key: MemoryKey, data: Any, embedding: Optional[np.ndarray] = None):
        """
        Store data at specific level
        """
        level = self.levels.get(level_name)
        if level is None:
            raise ValueError(f"Unknown level: {level_name}")

        # Encode if embedding not provided
        if embedding is None:
            embedding = level.encode(data, {})

        # Store in level
        level.memory[key] = embedding
        level.metadata[key] = MemoryEntry(
            key=key,
            data=data,
            surprise=surprise if "surprise" in locals() else 0.0,
            step=self.global_step,
            timestamp=time.time(),
        )

        # Add to vector index
        self.index.add(key, embedding, metadata={"level": level_name})

        logger.debug(f"Stored in level {level_name}", extra={"key": key, "level": level_name})

    def retrieve(self, query: Any, level_name: str, k: int = 5) -> List[Tuple[MemoryKey, float, Any]]:
        """
        Retrieve similar items from specific level
        """
        level = self.levels.get(level_name)
        if level is None:
            raise ValueError(f"Unknown level: {level_name}")

        # Encode query
        query_emb = level.encode(query, {})

        # Search in index
        results = self.index.search(query_emb, k=k, filter_fn=lambda meta: meta.get("level") == level_name)

        # Return with data
        output = []
        for key, sim in results:
            # Use get_metadata() method instead of direct dict access
            meta = level.get_metadata(key)
            if meta:
                data = meta.data if hasattr(meta, "data") else meta.get("data")
                output.append((key, sim, data))

        return output

    def retrieve_similar(
        self, query: Any, levels: List[str], k: int = 5
    ) -> Dict[str, List[Tuple[MemoryKey, float, Any]]]:
        """
        Retrieve from multiple levels
        """
        results = {}
        for level_name in levels:
            # DEBUG CHECK
            if level_name not in self.levels:
                print(f"WARNING: Requested level '{level_name}' not in CMS levels: {list(self.levels.keys())}")
                continue

            results[level_name] = self.retrieve(query, level_name, k)
        return results

    def update_level(self, level_name: str, key: MemoryKey, data: Any, surprise: SurpriseScore):
        """
        Update specific level with new data
        """
        level = self.levels.get(level_name)
        if level is None:
            raise ValueError(f"Unknown level: {level_name}")

        # Update level (will check surprise threshold internally)
        level.update(key, data, surprise)

    def encode_multi_level(self, data: Any, context: Dict, weights: Optional[Dict[str, float]] = None) -> np.ndarray:
        """
        Encode using weighted combination of all levels
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
        """
        level_stats = {name: level.get_stats() for name, level in self.levels.items()}

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
