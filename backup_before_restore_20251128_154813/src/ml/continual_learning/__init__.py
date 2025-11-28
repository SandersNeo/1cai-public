"""
Continual Learning Module

Implements Nested Learning paradigm from Google Research (NeurIPS 2025)
https://research.google/blog/introducing-nested-learning-a-new-ml-paradigm-for-continual-learning/

Key concepts:
- Continuum Memory System (CMS): Multi-level memory with different update frequencies
- Memory Levels: Individual levels with specific temporal scales
- Surprise-based Updates: Selective updates based on prediction errors
- Deep Optimizers: L2 regression loss instead of dot-product similarity

This module provides the foundation for catastrophic forgetting prevention
and continual learning across the 1C AI Stack.
"""

from .cms import ContinuumMemorySystem
from .memory_level import MemoryLevel, MemoryLevelConfig
from .types import MemoryKey, MemoryMetadata, SurpriseScore
from .vector_index import VectorIndex

__all__ = [
    "ContinuumMemorySystem",
    "MemoryLevel",
    "MemoryLevelConfig",
    "SurpriseScore",
    "MemoryKey",
    "MemoryMetadata",
    "VectorIndex",
]

__version__ = "0.1.0"
