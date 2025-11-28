"""Memory optimization domain models."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class MemorySettings:
    """1C Server memory settings."""

    # Heap settings
    heap_size_mb: int
    max_heap_size_mb: int

    # Cache settings
    metadata_cache_mb: int
    data_cache_mb: int
    index_cache_mb: int

    # GC settings
    gc_type: str = "G1GC"
    gc_threads: int = 4

    def __post_init__(self):
        """Validate memory settings."""
        if self.heap_size_mb > self.max_heap_size_mb:
            raise ValueError("Heap size cannot exceed max heap size")
        if self.heap_size_mb < 512:
            raise ValueError("Heap size must be at least 512MB")

    @property
    def total_memory_mb(self) -> int:
        """Calculate total memory usage."""
        return (
            self.max_heap_size_mb
            + self.metadata_cache_mb
            + self.data_cache_mb
            + self.index_cache_mb
        )


@dataclass
class MemoryUsagePattern:
    """Memory usage pattern analysis."""

    avg_usage_mb: float
    peak_usage_mb: float
    min_usage_mb: float

    # GC statistics
    gc_count: int
    gc_time_ms: int

    @property
    def avg_usage_percent(self) -> float:
        """Calculate average usage percentage."""
        if self.peak_usage_mb == 0:
            return 0.0
        return (self.avg_usage_mb / self.peak_usage_mb) * 100


@dataclass
class MemoryOptimization:
    """Memory optimization recommendation."""

    current_settings: MemorySettings
    recommended_settings: MemorySettings

    expected_improvement_percent: float
    memory_saved_mb: int

    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def is_beneficial(self) -> bool:
        """Check if optimization is beneficial."""
        return self.expected_improvement_percent > 5.0
