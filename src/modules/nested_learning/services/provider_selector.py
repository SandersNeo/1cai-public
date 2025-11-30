"""
Nested Provider Selector Service
"""
import time
import hashlib
from typing import Any, Dict, List, Optional, Tuple

from src.ai.llm_provider_abstraction import LLMProviderAbstraction, ModelProfile, QueryType
from src.utils.structured_logging import StructuredLogger
from src.modules.nested_learning.services.meta_optimizer import MetaOptimizer
from src.modules.nested_learning.domain.models import OptimizationCriteria, SuccessPattern

logger = StructuredLogger(__name__).logger


class NestedProviderSelector:
    """
    Adaptive provider selection service using Nested Learning.
    """

    def __init__(self, base_abstraction: LLMProviderAbstraction):
        self.base = base_abstraction
        self.query_memory = self._create_query_cms()
        self.meta_optimizer = MetaOptimizer(learning_rate=0.1)

        self.stats = {
            "total_selections": 0,
            "total_feedback": 0,
            "success_count": 0,
            "failure_count": 0,
            "cost_savings": 0.0,
        }

        logger.info("Created NestedProviderSelector service")

    def select_provider_adaptive(
        self,
        query: str,
        query_type: QueryType,
        context: Optional[Dict] = None,
        max_cost: Optional[float] = None,
        max_latency_ms: Optional[int] = None,
    ) -> ModelProfile:
        """Adaptive provider selection"""
        context = context or {}
        self.stats["total_selections"] += 1

        # 1. Retrieve similar queries
        similar_queries = self.query_memory.retrieve_similar(query, levels=["immediate", "session", "daily"], k=10)

        # 2. Extract patterns
        success_patterns = self._extract_success_patterns(similar_queries)

        # 3. Optimize criteria
        base_criteria = OptimizationCriteria(max_cost=max_cost or 0.01, max_latency_ms=max_latency_ms or 1000)

        modified_criteria = self.meta_optimizer.optimize_criteria(base_criteria, success_patterns)

        # Log optimizer state occasionally
        if self.stats["total_selections"] % 10 == 0:
            state = self.meta_optimizer.get_state()
            logger.debug("Optimizer state", extra=state.model_dump())

        # 4. Select provider
        provider = self.base.select_provider(
            query_type,
            max_cost=modified_criteria.max_cost,
            max_latency_ms=modified_criteria.max_latency_ms,
        )

        # 5. Store decision
        query_id = self._generate_query_id(query)
        decision = {
            "query": query,
            "query_type": str(query_type),
            "provider": provider.provider_id if provider else None,
            "criteria": modified_criteria.model_dump(),
            "timestamp": time.time(),
        }
        self.query_memory.store("immediate", query_id, decision)

        return provider

    def learn_from_feedback(self, query_id: str, success: bool, metrics: Dict[str, Any]):
        """Continual learning from feedback"""
        self.stats["total_feedback"] += 1
        if success:
            self.stats["success_count"] += 1
        else:
            self.stats["failure_count"] += 1

        surprise = self._compute_feedback_surprise(success, metrics)
        feedback_data = {"success": success, "metrics": metrics, "surprise": surprise, "timestamp": time.time()}

        # Update levels based on surprise
        if surprise > 0.7:
            self.query_memory.update_level("immediate", query_id, feedback_data, surprise)
            self.query_memory.update_level("session", query_id, feedback_data, surprise)
            self.query_memory.update_level("daily", query_id, feedback_data, surprise)
        elif surprise > 0.4:
            self.query_memory.update_level("immediate", query_id, feedback_data, surprise)
            self.query_memory.update_level("session", query_id, feedback_data, surprise)
            self.query_memory.update_level("immediate", query_id, feedback_data, surprise)

        self.query_memory.step()

    def _create_query_cms(self):
        # Lazy import to avoid circular dependency if any
        from src.modules.nested_learning.services.cms import ContinuumMemorySystem

        levels = [
            ("immediate", 1, 0.01),
            ("session", 10, 0.001),
            ("daily", 100, 0.0001),
            ("historical", 1000, 0.00001),
        ]
        cms = ContinuumMemorySystem(levels, embedding_dim=32)

        # Inject custom encoder
        for level in cms.levels.values():
            level.encode = self._query_encoder

        return cms

    def _query_encoder(self, data: Any, context: Dict) -> Any:
        import numpy as np

        if isinstance(data, str):
            query_hash = hashlib.sha256(data.encode()).digest()
            embedding = [float(b) / 255.0 for b in query_hash[:32]]
        elif isinstance(data, dict):
            query_text = data.get("query", str(data))
            query_hash = hashlib.sha256(query_text.encode()).digest()
            embedding = [float(b) / 255.0 for b in query_hash[:32]]
        else:
            embedding = [0.5] * 32
        return np.array(embedding, dtype="float32")

    def _extract_success_patterns(self, similar_queries: Dict) -> List[SuccessPattern]:
        patterns = []
        for level_name, results in similar_queries.items():
            for _, similarity, data in results:
                if isinstance(data, dict):
                    patterns.append(
                        SuccessPattern(
                            level=level_name,
                            similarity=similarity,
                            success=data.get("success", False),
                            metrics=data.get("metrics", {}),
                            timestamp=data.get("timestamp", 0.0),
                        )
                    )
        return patterns

    def _compute_feedback_surprise(self, success: bool, metrics: Dict) -> float:
        success_rate = (
            self.stats["success_count"] / self.stats["total_feedback"] if self.stats["total_feedback"] > 0 else 0.5
        )

        if success and success_rate < 0.3:
            surprise = 0.8
        elif not success and success_rate > 0.7:
            surprise = 0.9
        else:
            surprise = 0.2

        return min(surprise, 1.0)

    def _generate_query_id(self, query: str) -> str:
        timestamp = str(time.time())
        return hashlib.sha256(f"{query}_{timestamp}".encode()).hexdigest()
