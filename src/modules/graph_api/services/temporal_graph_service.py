"""
Temporal Graph Service

Service layer for temporal graph operations with code evolution tracking.
"""

import time
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import numpy as np
import torch

if TYPE_CHECKING:
    from src.modules.graph_api.services.graph_service import GraphService

from src.ml.graph.temporal_gnn import GraphEvolutionTracker, TemporalGNN
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class TemporalGraphService:
    """
    Temporal graph service with code evolution tracking

    Features:
    - Track code changes over time
    - Predict impact of changes using Temporal GNN
    - Analyze dependency evolution
    - Multi-scale temporal queries

    Example:
        >>> service = TemporalGraphService(base_graph_service)
        >>> impact = await service.predict_impact(
        ...     node_id="Function:MyFunc",
        ...     change_type="modify"
        ... )
        >>> print(f"Impact score: {impact['impact_score']}")
        >>> print(f"Affected nodes: {len(impact['affected_nodes'])}")
    """

    def __init__(self, base_service: "GraphService"):
        """
        Initialize temporal graph service

        Args:
            base_service: Base graph service
        """
        self.base = base_service

        # Temporal GNN model
        self.tgnn = TemporalGNN(node_features=128, hidden_dim=256,
                                num_layers=3, num_heads=4)

        # Evolution tracker
        self.evolution_tracker = GraphEvolutionTracker(max_history=1000)

        # Node cache
        self.node_cache: Dict[str, Dict] = {}

        # Statistics
        self.stats = {
            "total_predictions": 0,
            "total_evolutions": 0,
            "avg_impact": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

        logger.info("Created TemporalGraphService")

    async def predict_impact(self, node_id: str, change_type: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Predict impact of code change

        Args:
            node_id: Node to change
            change_type: "add" | "modify" | "delete"
            context: Optional context

        Returns:
            Dict with:
                - node_id: Changed node ID
                - change_type: Type of change
                - impact_score: Overall impact score (0-1)
                - affected_nodes: List of affected node IDs
                - confidence: Prediction confidence
                - details: Additional details
        """
        context = context or {}
        self.stats["total_predictions"] += 1

        try:
            # Get graph data
            graph_data = await self._get_graph_data(node_id)

            if graph_data is None:
                logger.warning("No graph data for node: %s", node_id)
                return self._empty_impact_result(node_id, change_type)

            # Predict with TGNN
            with torch.no_grad():
                predictions = self.tgnn(
                    x=graph_data["node_features"],
                    edge_index=graph_data["edge_index"],
                    timestamps=graph_data["timestamps"],
                    edge_times=graph_data.get("edge_times"),
                )

            # Extract impact scores
            impact_scores = predictions["impact"].squeeze().numpy()

            # Find target node index
            graph_data["node_ids"].index(
                node_id) if node_id in graph_data["node_ids"] else 0

            # Find affected nodes
            affected_nodes = self._find_affected_nodes(
                graph_data["node_ids"], impact_scores, threshold=0.5)

            # Compute overall impact
            avg_impact = float(impact_scores.mean())
            max_impact = float(impact_scores.max())

            # Update stats
            self.stats["avg_impact"] = self.stats["avg_impact"] * 0.9 + avg_impact * 0.1

            logger.info(
                "Predicted impact",
                extra={
                    "node_id": node_id,
                    "change_type": change_type,
                    "affected_count": len(affected_nodes),
                    "avg_impact": avg_impact,
                    "max_impact": max_impact,
                },
            )

            return {
                "node_id": node_id,
                "change_type": change_type,
                "impact_score": avg_impact,
                "max_impact": max_impact,
                "affected_nodes": affected_nodes,
                "confidence": 0.85,
                "details": {"total_nodes": len(graph_data["node_ids"]), "prediction_time": time.time()},
            }

        except Exception as e:
            logger.error(f"Impact prediction failed: {e}", exc_info=True, extra={
                         "node_id": node_id})
            return self._empty_impact_result(node_id, change_type)

    async def track_evolution(self, node_id: str, change: Dict[str, Any], timestamp: Optional[float] = None):
        """
        Track code evolution

        Args:
            node_id: Changed node ID
            change: Change details (type, metadata, etc.)
            timestamp: Change timestamp (default: now)
        """
        timestamp = timestamp or time.time()
        self.stats["total_evolutions"] += 1

        # Record in tracker
        self.evolution_tracker.record_change(
            node_id=node_id,
            change_type=change.get("type", "modify"),
            timestamp=timestamp,
            metadata=change.get("metadata", {}),
        )

        # Invalidate cache for this node
        if node_id in self.node_cache:
            del self.node_cache[node_id]

        logger.debug(
            "Tracked evolution", extra={"node_id": node_id, "change_type": change.get("type"), "timestamp": timestamp}
        )

    async def get_evolution_history(
        self, node_id: Optional[str] = None, since: Optional[float] = None, limit: int = 100
    ) -> List[Dict]:
        """
        Get evolution history

        Args:
            node_id: Optional node ID filter
            since: Optional timestamp filter
            limit: Maximum results

        Returns:
            List of evolution records
        """
        if since:
            history = self.evolution_tracker.get_changes_since(since, node_id)
        else:
            history = [
                c for c in self.evolution_tracker.history if node_id is None or c["node_id"] == node_id]

        return history[:limit]

    async def get_change_frequency(self, node_id: str) -> float:
        """
        Get change frequency for node

        Args:
            node_id: Node ID

        Returns:
            Changes per day
        """
        return self.evolution_tracker.get_change_frequency(node_id)

    async def _get_graph_data(self, node_id: str) -> Optional[Dict]:
        """
        Get graph data for TGNN

        Args:
            node_id: Central node ID

        Returns:
            Dict with graph tensors or None
        """
        # Check cache
        if node_id in self.node_cache:
            self.stats["cache_hits"] += 1
            return self.node_cache[node_id]

        self.stats["cache_misses"] += 1

        try:
            # Query graph neighborhood
            query = """
            MATCH (n)
            WHERE id(n) = $node_id OR n.id = $node_id
            OPTIONAL MATCH (n)-[r]-(m)
            RETURN n, collect(DISTINCT m) as neighbors, collect(DISTINCT r) as relationships
            LIMIT 100
            """

            result = await self.base.execute_query(query, {"node_id": node_id})

            if not result:
                return None

            # Extract nodes and edges
            nodes = []
            node_ids = []

            # Process result
            for record in result:
                # Central node
                if "n" in record:
                    node = record["n"]
                    if node and node not in nodes:
                        nodes.append(node)
                        node_ids.append(str(node.get("id", node.id)))

                # Neighbors
                if "neighbors" in record:
                    for neighbor in record["neighbors"]:
                        if neighbor and neighbor not in nodes:
                            nodes.append(neighbor)
                            node_ids.append(str(neighbor.get("id", neighbor.id)))

            # Create dummy features (in production, extract from nodes)
            num_nodes = len(nodes)
            node_features = torch.randn(num_nodes, 128)

            # Create edge index (dummy for now)
            edge_index = torch.tensor([[0], [1]], dtype=torch.long)
            if num_nodes > 1:
                # Create simple chain
                sources = list(range(num_nodes - 1))
                targets = list(range(1, num_nodes))
                edge_index = torch.tensor([sources, targets], dtype=torch.long)

            # Create timestamps (dummy: current time for all)
            timestamps = torch.full((num_nodes,), time.time(), dtype=torch.float32)

            graph_data = {
                "node_features": node_features,
                "edge_index": edge_index,
                "timestamps": timestamps,
                "node_ids": node_ids,
            }

            # Cache
            self.node_cache[node_id] = graph_data

            return graph_data

        except Exception as e:
            logger.error(f"Failed to get graph data: {e}", exc_info=True, extra={
                         "node_id": node_id})
            return None

    def _find_affected_nodes(self, node_ids: List[str], impact_scores: np.ndarray, threshold: float = 0.5) -> List[str]:
        """
        Find nodes affected by change

        Args:
            node_ids: List of node IDs
            impact_scores: Impact scores for each node
            threshold: Impact threshold

        Returns:
            List of affected node IDs
        """
        affected_indices = np.where(impact_scores > threshold)[0]
        affected_nodes = [node_ids[i] for i in affected_indices if i < len(node_ids)]

        return affected_nodes

    def _empty_impact_result(self, node_id: str, change_type: str) -> Dict:
        """Create empty impact result"""
        return {
            "node_id": node_id,
            "change_type": change_type,
            "impact_score": 0.0,
            "max_impact": 0.0,
            "affected_nodes": [],
            "confidence": 0.0,
            "details": {"error": "No data available"},
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        tracker_stats = self.evolution_tracker.get_stats()

        return {
            **self.stats,
            "evolution_tracker": tracker_stats,
            "cache_size": len(self.node_cache),
            "cache_hit_rate": (
                self.stats["cache_hits"] / \
                    (self.stats["cache_hits"] + self.stats["cache_misses"])
                if (self.stats["cache_hits"] + self.stats["cache_misses"]) > 0
                else 0.0
            ),
        }

    def health_check(self) -> Dict[str, Any]:
        """Health check"""
        return {
            "status": "healthy",
            "total_predictions": self.stats["total_predictions"],
            "total_evolutions": self.stats["total_evolutions"],
            "avg_impact": self.stats["avg_impact"],
            "cache_size": len(self.node_cache),
        }
