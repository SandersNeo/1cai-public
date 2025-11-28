"""Memory Optimizer Service."""

from typing import List

from ..domain import MemoryOptimization, MemorySettings, MemoryUsagePattern


class MemoryOptimizer:
    """Service for optimizing 1C server memory settings."""

    def analyze_usage_pattern(
        self, current_settings: MemorySettings, usage_data: List[float]
    ) -> MemoryUsagePattern:
        """
        Analyze memory usage pattern.

        Args:
            current_settings: Current memory settings
            usage_data: List of memory usage samples (MB)

        Returns:
            Memory usage pattern analysis
        """
        if not usage_data:
            return MemoryUsagePattern(
                avg_usage_mb=0.0,
                peak_usage_mb=0.0,
                min_usage_mb=0.0,
                gc_count=0,
                gc_time_ms=0,
            )

        return MemoryUsagePattern(
            avg_usage_mb=sum(usage_data) / len(usage_data),
            peak_usage_mb=max(usage_data),
            min_usage_mb=min(usage_data),
            gc_count=len(
                [u for u in usage_data if u < usage_data[0] * 0.8]
            ),  # Simplified
            gc_time_ms=0,  # TODO: Get from actual GC logs
        )

    def optimize_memory(
        self, current_settings: MemorySettings, usage_pattern: MemoryUsagePattern
    ) -> MemoryOptimization:
        """
        Generate memory optimization recommendations.

        Args:
            current_settings: Current memory settings
            usage_pattern: Usage pattern analysis

        Returns:
            Memory optimization recommendations
        """
        reasons = []
        warnings = []

        # Calculate recommended heap size (peak + 20% buffer)
        recommended_heap = int(usage_pattern.peak_usage_mb * 1.2)
        recommended_max_heap = int(recommended_heap * 1.5)

        # Optimize cache sizes based on usage
        recommended_metadata_cache = max(
            256, int(current_settings.metadata_cache_mb * 1.1)
        )
        recommended_data_cache = max(512, int(current_settings.data_cache_mb * 1.2))
        recommended_index_cache = max(256, int(current_settings.index_cache_mb * 1.1))

        # Create recommended settings
        recommended_settings = MemorySettings(
            heap_size_mb=recommended_heap,
            max_heap_size_mb=recommended_max_heap,
            metadata_cache_mb=recommended_metadata_cache,
            data_cache_mb=recommended_data_cache,
            index_cache_mb=recommended_index_cache,
            gc_type="G1GC",  # Recommended for large heaps
            gc_threads=4,
        )

        # Calculate improvement
        current_total = current_settings.total_memory_mb
        recommended_total = recommended_settings.total_memory_mb
        memory_saved = current_total - recommended_total

        if memory_saved > 0:
            improvement = (memory_saved / current_total) * 100
            reasons.append(f"Can save {memory_saved}MB ({improvement:.1f}%)")
        else:
            improvement = 0.0
            reasons.append("Memory increase needed for stability")
            warnings.append(f"Requires additional {abs(memory_saved)}MB")

        # Add specific recommendations
        if usage_pattern.avg_usage_percent < 50:
            reasons.append("Average usage is low - can reduce allocation")

        if usage_pattern.gc_count > 100:
            reasons.append("High GC frequency - increase heap size")
            warnings.append("Consider tuning GC parameters")

        return MemoryOptimization(
            current_settings=current_settings,
            recommended_settings=recommended_settings,
            expected_improvement_percent=abs(improvement),
            memory_saved_mb=memory_saved,
            reasons=reasons,
            warnings=warnings,
        )
