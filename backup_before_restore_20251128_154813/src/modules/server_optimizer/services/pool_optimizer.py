"""Connection Pool Optimizer Service."""

from typing import List

from ..domain import ConnectionPool, PoolMetrics, PoolOptimization


class ConnectionPoolOptimizer:
    """Service for optimizing database connection pools."""

    def analyze_pool_metrics(
        self, pool: ConnectionPool, metrics_history: List[PoolMetrics]
    ) -> PoolOptimization:
        """
        Analyze pool metrics and generate optimization.

        Args:
            pool: Current connection pool
            metrics_history: Historical metrics

        Returns:
            Pool optimization recommendations
        """
        if not metrics_history:
            return PoolOptimization(
                current_pool=pool,
                recommended_min=pool.min_connections,
                recommended_max=pool.max_connections,
                expected_improvement="No data available",
                reasoning=["Need historical metrics for analysis"],
            )

        # Calculate averages
        avg_active = sum(m.avg_active for m in metrics_history) / len(metrics_history)
        peak_active = max(m.peak_active for m in metrics_history)
        avg_wait_time = sum(m.avg_wait_time_ms for m in metrics_history) / len(
            metrics_history
        )
        total_timeouts = sum(m.timeout_count for m in metrics_history)

        reasoning = []

        # Determine recommended sizes
        recommended_min = max(5, int(avg_active * 0.8))
        recommended_max = max(recommended_min * 2, int(peak_active * 1.3))

        # Add reasoning
        if avg_active < pool.min_connections * 0.5:
            reasoning.append(
                f"Average usage ({avg_active:.1f}) is below min connections"
            )
            reasoning.append("Can reduce min_connections to save resources")

        if peak_active > pool.max_connections * 0.9:
            reasoning.append(f"Peak usage ({peak_active}) near max capacity")
            reasoning.append("Should increase max_connections")

        if avg_wait_time > 100:
            reasoning.append(f"High average wait time ({avg_wait_time:.0f}ms)")
            reasoning.append("Increase pool size to reduce wait times")

        if total_timeouts > 0:
            reasoning.append(f"Found {total_timeouts} connection timeouts")
            reasoning.append("Critical: increase max_connections immediately")

        # Determine expected improvement
        if total_timeouts > 0:
            improvement = "Critical - eliminate timeouts"
        elif avg_wait_time > 100:
            improvement = f"Reduce wait time by ~{min(50, int((avg_wait_time - 50) / avg_wait_time * 100))}%"
        elif recommended_max < pool.max_connections:
            saved = pool.max_connections - recommended_max
            improvement = (
                f"Save {saved} connections ({saved / pool.max_connections * 100:.0f}%)"
            )
        else:
            improvement = "Maintain current performance with optimized settings"

        return PoolOptimization(
            current_pool=pool,
            recommended_min=recommended_min,
            recommended_max=recommended_max,
            expected_improvement=improvement,
            reasoning=reasoning,
        )

    def calculate_optimal_timeout(self, avg_query_time_ms: float) -> int:
        """
        Calculate optimal connection timeout.

        Args:
            avg_query_time_ms: Average query execution time

        Returns:
            Recommended timeout in seconds
        """
        # Timeout should be 3x average query time, min 30s, max 300s
        timeout_ms = avg_query_time_ms * 3
        timeout_sec = int(timeout_ms / 1000)

        return max(30, min(300, timeout_sec))
