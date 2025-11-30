"""
Type definitions for Nested Learning module
"""

import time
from dataclasses import dataclass
from typing import Any, Dict

# Type aliases
SurpriseScore = float  # 0.0 to 1.0
MemoryKey = str  # Unique identifier for memory entry
MemoryMetadata = Dict[str, Any]  # Metadata for memory entry


@dataclass
class MemoryEntry:
    """Single entry in memory level"""

    key: MemoryKey
    data: Any
    surprise: SurpriseScore
    step: int
    timestamp: float

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

    def age_seconds(self) -> float:
        """Get age of entry in seconds"""
        return time.time() - self.timestamp

    def age_steps(self, current_step: int) -> int:
        """Get age of entry in steps"""
        return current_step - self.step


@dataclass
class LevelStats:
    """Statistics for a memory level"""

    name: str
    total_encodes: int = 0
    total_updates: int = 0
    total_retrievals: int = 0
    avg_surprise: float = 0.0
    last_update_step: int = 0
    memory_size: int = 0
    update_freq: int = 1
    frozen: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "total_encodes": self.total_encodes,
            "total_updates": self.total_updates,
            "total_retrievals": self.total_retrievals,
            "avg_surprise": self.avg_surprise,
            "last_update_step": self.last_update_step,
            "memory_size": self.memory_size,
            "update_freq": self.update_freq,
            "frozen": self.frozen,
        }


@dataclass
class CMSStats:
    """Statistics for Continuum Memory System"""

    global_step: int
    total_levels: int
    total_memory_size: int
    index_size: int
    levels: Dict[str, LevelStats]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "global_step": self.global_step,
            "total_levels": self.total_levels,
            "total_memory_size": self.total_memory_size,
            "index_size": self.index_size,
            "levels": {name: stats.to_dict() for name, stats in self.levels.items()},
        }
