"""
Meta Optimizer - Self-referential optimization for Nested Learning

Implements self-modifying optimization inspired by Hope architecture.
Optimizes selection criteria based on historical success patterns.

Based on:
- Hope architecture (self-referential process)
- Nested Learning paradigm
"""

from typing import Any, Dict, List

import numpy as np

from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class SelfReferencialOptimizer:
    """
    Self-referential optimizer for adaptive criteria

    Key insight from Hope architecture:
    - Optimize its own optimization criteria
    - Learn from success/failure patterns
    - Self-modify based on feedback

    Example:
        >>> optimizer = SelfReferencialOptimizer()
        >>> patterns = [{"cost": 0.01, "success": True}, ...]
        >>> new_criteria = optimizer.optimize_criteria(base_criteria, patterns)
    """

    def __init__(self, learning_rate: float = 0.1):
        """
        Initialize meta optimizer

        Args:
            learning_rate: How quickly to adapt criteria
        """
        self.learning_rate = learning_rate
        self.optimization_history: List[Dict] = []

        logger.info("Created SelfReferencialOptimizer with lr=%s")

    def optimize_criteria(
        self, base_criteria: Dict[str, Any], success_patterns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Optimize selection criteria based on success patterns

        Self-modifies criteria to maximize success rate

        Args:
            base_criteria: Base criteria (cost, latency, etc.)
            success_patterns: Historical patterns with success flags

        Returns:
            Modified criteria
        """
        if not success_patterns:
            return base_criteria

        # Analyze patterns
        analysis = self._analyze_patterns(success_patterns)

        # Modify criteria based on analysis
        modified = base_criteria.copy()

        # Adjust cost threshold
        if "cost_threshold" in analysis:
            current_cost = base_criteria.get("max_cost", 0.01)
            optimal_cost = analysis["cost_threshold"]

            # Gradual adjustment
            new_cost = current_cost + self.learning_rate * (optimal_cost - current_cost)
            modified["max_cost"] = new_cost

        # Adjust latency threshold
        if "latency_threshold" in analysis:
            current_latency = base_criteria.get("max_latency_ms", 1000)
            optimal_latency = analysis["latency_threshold"]

            new_latency = current_latency + self.learning_rate * (
                optimal_latency - current_latency
            )
            modified["max_latency_ms"] = int(new_latency)

        # Add quality weight if patterns show quality matters
        if analysis.get("quality_important", False):
            modified["quality_weight"] = analysis.get("quality_weight", 0.5)

        # Record optimization
        self.optimization_history.append(
            {
                "base": base_criteria,
                "modified": modified,
                "analysis": analysis,
                "num_patterns": len(success_patterns),
            }
        )

        logger.info(
            "Optimized criteria",
            extra={
                "base_cost": base_criteria.get("max_cost"),
                "new_cost": modified.get("max_cost"),
                "num_patterns": len(success_patterns),
            },
        )

        return modified

    def _analyze_patterns(self, patterns: List[Dict]) -> Dict[str, Any]:
        """
        Analyze success patterns to extract insights

        Args:
            patterns: List of historical patterns

        Returns:
            Analysis results
        """
        if not patterns:
            return {}

        # Separate successful and failed patterns
        successful = [p for p in patterns if p.get("success", False)]
        failed = [p for p in patterns if not p.get("success", False)]

        analysis = {}

        # Analyze cost patterns
        if successful:
            costs = [p.get("cost", 0.0) for p in successful]
            analysis["cost_threshold"] = np.percentile(costs, 75)  # 75th percentile

        # Analyze latency patterns
        if successful:
            latencies = [p.get("latency_ms", 0) for p in successful]
            analysis["latency_threshold"] = np.percentile(latencies, 75)

        # Check if quality correlates with success
        if len(successful) > 0 and len(failed) > 0:
            avg_quality_success = np.mean([p.get("quality", 0.5) for p in successful])
            avg_quality_failed = np.mean([p.get("quality", 0.5) for p in failed])

            if avg_quality_success > avg_quality_failed + 0.1:
                analysis["quality_important"] = True
                analysis["quality_weight"] = 0.7

        # Success rate
        analysis["success_rate"] = len(successful) / len(patterns)

        return analysis

    def optimize_scenario(
        self,
        base_scenario: Dict[str, Any],
        success_patterns: List[Dict[str, Any]],
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Optimize scenario execution based on patterns

        For Scenario Hub integration

        Args:
            base_scenario: Base scenario definition
            success_patterns: Historical execution patterns
            params: Current parameters

        Returns:
            Modified scenario
        """
        if not success_patterns:
            return base_scenario

        modified = base_scenario.copy()

        # Analyze what worked
        successful = [p for p in success_patterns if p.get("success", False)]

        if successful:
            # Extract common parameters from successful executions
            common_params = self._extract_common_params(successful)

            # Merge with base scenario
            if "params" not in modified:
                modified["params"] = {}

            modified["params"].update(common_params)

            # Adjust retry strategy if needed
            if any(p.get("retries", 0) > 0 for p in successful):
                modified["max_retries"] = max(p.get("retries", 0) for p in successful)

        return modified

    def _extract_common_params(self, patterns: List[Dict]) -> Dict[str, Any]:
        """Extract common parameters from successful patterns"""
        if not patterns:
            return {}

        # Find parameters that appear in most successful patterns
        param_counts: Dict[str, int] = {}
        param_values: Dict[str, List[Any]] = {}

        for pattern in patterns:
            params = pattern.get("params", {})
            for key, value in params.items():
                param_counts[key] = param_counts.get(key, 0) + 1
                if key not in param_values:
                    param_values[key] = []
                param_values[key].append(value)

        # Keep parameters that appear in >50% of patterns
        threshold = len(patterns) * 0.5
        common = {}

        for key, count in param_counts.items():
            if count >= threshold:
                # Use most common value
                values = param_values[key]
                if all(isinstance(v, (int, float)) for v in values):
                    # Numeric: use median
                    common[key] = np.median(values)
                else:
                    # Categorical: use mode
                    common[key] = max(set(values), key=values.count)

        return common

    def get_stats(self) -> Dict[str, Any]:
        """Get optimizer statistics"""
        return {
            "total_optimizations": len(self.optimization_history),
            "learning_rate": self.learning_rate,
            "recent_optimizations": (
                self.optimization_history[-5:] if self.optimization_history else []
            ),
        }
