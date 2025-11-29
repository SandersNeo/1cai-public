"""
Nested Provider Selector

Adaptive LLM provider selection with Continuum Memory System.
Self-modifies selection criteria based on historical success.

Inspired by Hope architecture (unbounded in-context learning).
"""

import hashlib
import time
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from src.ai.llm_provider_abstraction import (
    LLMProviderAbstraction,
    ModelProfile,
    QueryType,
)
from src.utils.structured_logging import StructuredLogger

if TYPE_CHECKING:
    from src.ml.continual_learning.cms import ContinuumMemorySystem
    from src.ml.continual_learning.meta_optimizer import SelfReferencialOptimizer

logger = StructuredLogger(__name__).logger


# QueryMemoryLevel moved to _create_query_cms to avoid circular/heavy imports


class NestedProviderSelector:
    """
    Self-modifying provider selection with Nested Learning

    Inspiration: Hope architecture (unbounded in-context learning)

    Key features:
    - Query history CMS with 4 levels
    - Self-referential optimization of criteria
    - Adaptive selection based on patterns
    - Continual learning from feedback

    Example:
        >>> selector = NestedProviderSelector(base_abstraction)
        >>> provider = selector.select_provider_adaptive(
        ...     query="Generate BSL code",
        ...     query_type=QueryType.CODE_GENERATION,
        ...     context={}
        ... )
        >>> selector.learn_from_feedback(query_id, success=True, metrics={})
    """

    def __init__(self, base_abstraction: LLMProviderAbstraction):
        """
        Initialize nested provider selector

        Args:
            base_abstraction: Base LLM provider abstraction
        """
        self.base = base_abstraction

        # Create CMS for query history
        self.query_memory = self._create_query_cms()

        # Self-referential optimizer
        self.meta_optimizer = SelfReferencialOptimizer(learning_rate=0.1)

        # Statistics
        self.stats = {
            "total_selections": 0,
            "total_feedback": 0,
            "success_count": 0,
            "failure_count": 0,
            "cost_savings": 0.0,
        }

        logger.info("Created NestedProviderSelector with 4-level query memory")

    def _create_query_cms(self) -> "ContinuumMemorySystem":
        """Create CMS for query history"""
        # Lazy import
        from src.ml.continual_learning.cms import ContinuumMemorySystem
        from src.ml.continual_learning.memory_level import MemoryLevel
        
        # Local definition of QueryMemoryLevel to avoid top-level dependency
        class QueryMemoryLevel(MemoryLevel):
            """Memory level for query history"""
        
            def encode(self, data: Any, context: Dict):
                """Encode query as simple hash-based embedding"""
                self.stats.total_encodes += 1
        
                # Simple encoding: hash query text to vector
                if isinstance(data, str):
                    query_hash = hashlib.sha256(data.encode()).digest()
                    # Convert to float vector
                    embedding = [float(b) / 255.0 for b in query_hash[:32]]
                elif isinstance(data, dict):
                    # Hash query text from dict
                    query_text = data.get("query", str(data))
                    query_hash = hashlib.sha256(query_text.encode()).digest()
                    embedding = [float(b) / 255.0 for b in query_hash[:32]]
                else:
                    # Fallback: random
                    embedding = [0.5] * 32
        
                import numpy as np
        
                return np.array(embedding, dtype="float32")

        levels = [
            ("immediate", 1, 0.01),  # Last 10 queries
            ("session", 10, 0.001),  # Current session
            ("daily", 100, 0.0001),  # Today's queries
            ("historical", 1000, 0.00001),  # All history
        ]

        cms = ContinuumMemorySystem(levels, embedding_dim=32)

        # Override with QueryMemoryLevel
        for name, level in cms.levels.items():
            config = level.config
            cms.levels[name] = QueryMemoryLevel(config)

        return cms

    def select_provider_adaptive(
        self,
        query: str,
        query_type: QueryType,
        context: Optional[Dict] = None,
        max_cost: Optional[float] = None,
        max_latency_ms: Optional[int] = None,
    ) -> ModelProfile:
        """
        Adaptive provider selection with self-modification

        Args:
            query: Query text
            query_type: Type of query
            context: Additional context
            max_cost: Maximum cost per 1K tokens
            max_latency_ms: Maximum latency in ms

        Returns:
            Selected provider profile
        """
        context = context or {}
        self.stats["total_selections"] += 1

        # 1. Retrieve similar queries from continuum memory
        similar_queries = self.query_memory.retrieve_similar(
            query, levels=["immediate", "session", "daily"], k=10)

        # 2. Analyze success patterns
        success_patterns = self._extract_success_patterns(similar_queries)

        # 3. Self-modify selection criteria based on patterns
        base_criteria = {"max_cost": max_cost or 0.01,
            "max_latency_ms": max_latency_ms or 1000}

        modified_criteria = self.meta_optimizer.optimize_criteria(
            base_criteria, success_patterns)

        # 4. Select provider with modified criteria
        provider = self.base.select_provider(
            query_type,
            max_cost=modified_criteria.get("max_cost"),
            max_latency_ms=modified_criteria.get("max_latency_ms"),
        )

        # 5. Store decision for future learning
        query_id = self._generate_query_id(query)
        decision = {
            "query": query,
            "query_type": query_type.value if hasattr(query_type, "value") else str(query_type),
            "provider": provider.provider_id if provider else None,
            "model": provider.model_name if provider else None,
            "criteria": modified_criteria,
            "timestamp": time.time(),
            "similar_count": sum(len(v) for v in similar_queries.values()),
        }

        # Store in immediate level
        self.query_memory.store("immediate", query_id, decision)

        logger.info(
            "Selected provider adaptively",
            extra={
                "provider": provider.provider_id if provider else None,
                "similar_queries": sum(len(v) for v in similar_queries.values()),
                "modified_cost": modified_criteria.get("max_cost"),
            },
        )

        return provider

    def learn_from_feedback(self, query_id: str, success: bool, metrics: Dict[str, Any]):
        """
        Continual learning from feedback

        Updates appropriate memory levels based on surprise

        Args:
            query_id: Query identifier
            success: Whether query was successful
            metrics: Performance metrics (cost, latency, quality, etc.)
        """
        self.stats["total_feedback"] += 1

        if success:
            self.stats["success_count"] += 1
        else:
            self.stats["failure_count"] += 1

        # Compute surprise (how unexpected was this result)
        surprise = self._compute_feedback_surprise(success, metrics)

        # Update appropriate levels based on surprise
        feedback_data = {"success": success, "metrics": metrics,
            "surprise": surprise, "timestamp": time.time()}

        if surprise > 0.7:  # High surprise
            # Update multiple levels
            self.query_memory.update_level(
                "immediate", query_id, feedback_data, surprise)
            self.query_memory.update_level("session", query_id, feedback_data, surprise)
            self.query_memory.update_level("daily", query_id, feedback_data, surprise)

        elif surprise > 0.4:  # Medium surprise
            self.query_memory.update_level(
                "immediate", query_id, feedback_data, surprise)
            self.query_memory.update_level("session", query_id, feedback_data, surprise)

        else:  # Low surprise
            self.query_memory.update_level(
                "immediate", query_id, feedback_data, surprise)

        # Track cost savings
        if success and "cost" in metrics:
            baseline_cost = metrics.get("baseline_cost", 0.01)
            actual_cost = metrics["cost"]
            if actual_cost < baseline_cost:
                savings = baseline_cost - actual_cost
                self.stats["cost_savings"] += savings

        # Advance step
        self.query_memory.step()

        logger.debug(
            "Learned from feedback", extra={"query_id": query_id[:16] + "...", "success": success, "surprise": surprise}
        )

    def _extract_success_patterns(
        self, similar_queries: Dict[str, List[Tuple[str, float, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        Extract success patterns from similar queries

        Args:
            similar_queries: Dict of level -> [(key, similarity, data)]

        Returns:
            List of success patterns
        """
        patterns = []

        for level_name, results in similar_queries.items():
            for key, similarity, data in results:
                if isinstance(data, dict):
                    # Extract pattern
                    pattern = {
                        "level": level_name,
                        "similarity": similarity,
                        "success": data.get("success", False),
                        "cost": data.get("metrics", {}).get("cost", 0.0),
                        "latency_ms": data.get("metrics", {}).get("latency_ms", 0),
                        "quality": data.get("metrics", {}).get("quality", 0.5),
                    }
                    patterns.append(pattern)

        return patterns

    def _compute_feedback_surprise(self, success: bool, metrics: Dict[str, Any]) -> float:
        """
        Compute surprise from feedback

        Args:
            success: Success flag
            metrics: Performance metrics

        Returns:
            Surprise score (0-1)
        """
        # Base surprise on success rate
        success_rate = (
            self.stats["success_count"] / \
                self.stats["total_feedback"] if self.stats["total_feedback"] > 0 else 0.5
        )

        # High surprise if result differs from expected
        if success and success_rate < 0.3:
            # Unexpected success
            surprise = 0.8
        elif not success and success_rate > 0.7:
            # Unexpected failure
            surprise = 0.9
        else:
            # Expected result
            surprise = 0.2

        # Adjust based on cost deviation
        if "cost" in metrics:
            expected_cost = 0.01  # Default
            actual_cost = metrics["cost"]
            cost_deviation = abs(actual_cost - expected_cost) / expected_cost
            surprise += cost_deviation * 0.2

        return min(surprise, 1.0)

    def _generate_query_id(self, query: str) -> str:
        """Generate unique ID for query"""
        timestamp = str(time.time())
        combined = f"{query}_{timestamp}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def get_stats(self) -> Dict[str, Any]:
        """Get selector statistics"""
        cms_stats = self.query_memory.get_stats()

        return {
            **self.stats,
            "success_rate": (
                self.stats["success_count"] / \
                    self.stats["total_feedback"] if self.stats["total_feedback"] > 0 else 0.0
            ),
            "cms": cms_stats.to_dict(),
            "optimizer": self.meta_optimizer.get_stats(),
        }

    def health_check(self) -> Dict[str, Any]:
        """Health check"""
        return {
            "status": "healthy",
            "query_memory_levels": len(self.query_memory.levels),
            "total_selections": self.stats["total_selections"],
            "success_rate": (
                self.stats["success_count"] / \
                    self.stats["total_feedback"] if self.stats["total_feedback"] > 0 else 0.0
            ),
        }
