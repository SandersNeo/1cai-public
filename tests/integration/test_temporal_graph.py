"""
Integration tests for Temporal Graph Service

End-to-end tests for graph evolution tracking.
"""

import pytest

from src.modules.graph_api.services.temporal_graph_service import TemporalGraphService
from src.modules.graph_api.services.graph_service import GraphService
from src.db.neo4j_client import Neo4jClient


@pytest.mark.asyncio
class TestTemporalGraphIntegration:
    """Integration tests for temporal graph"""

    async def test_impact_prediction_flow(self):
        """Test complete impact prediction flow"""
        # Mock Neo4j client
        neo4j = Neo4jClient(uri="bolt://localhost:7687", user="neo4j", password="test")
        base_service = GraphService(neo4j)
        temporal_service = TemporalGraphService(base_service)

        # Predict impact
        result = await temporal_service.predict_impact(
            node_id="Function:TestFunc", change_type="modify", context={"project": "TestProject"}
        )

        assert "impact_score" in result
        assert "affected_nodes" in result
        assert isinstance(result["impact_score"], float)

    async def test_evolution_tracking_flow(self):
        """Test evolution tracking flow"""
        neo4j = Neo4jClient(uri="bolt://localhost:7687", user="neo4j", password="test")
        base_service = GraphService(neo4j)
        temporal_service = TemporalGraphService(base_service)

        # Track evolution
        await temporal_service.track_evolution(
            node_id="Function:TestFunc", change={"type": "modify", "author": "test"}, timestamp=1234567890.0
        )

        # Get history
        history = await temporal_service.get_evolution_history(node_id="Function:TestFunc", limit=10)

        assert isinstance(history, list)

    async def test_change_frequency(self):
        """Test change frequency calculation"""
        neo4j = Neo4jClient(uri="bolt://localhost:7687", user="neo4j", password="test")
        base_service = GraphService(neo4j)
        temporal_service = TemporalGraphService(base_service)

        # Track multiple changes
        for i in range(5):
            await temporal_service.track_evolution(
                node_id="Function:FrequentFunc", change={"type": "modify"}, timestamp=float(i * 86400)  # 1 day apart
            )

        # Get frequency
        freq = await temporal_service.get_change_frequency("Function:FrequentFunc")

        assert freq >= 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
