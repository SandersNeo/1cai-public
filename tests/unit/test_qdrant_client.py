# [NEXUS IDENTITY] ID: 3426978045458353627 | DATE: 2025-11-19

"""
Unit tests for QdrantClient
"""

from unittest.mock import MagicMock, patch

from src.db.qdrant_client import QdrantClient


class TestQdrantClient:
    """Test Qdrant client functionality"""

    @patch("qdrant_client.QdrantClient")
    def test_connect_success(self, mock_qdrant):
        """Test successful connection"""
        mock_client_instance = MagicMock()
        mock_qdrant.return_value = mock_client_instance

        client = QdrantClient()
        result = client.connect()

        assert result is True
        assert client.client is not None
        mock_client_instance.get_collections.assert_called_once()

    @patch("qdrant_client.QdrantClient")
    def test_create_collections(self, mock_qdrant):
        """Test creating collections"""
        mock_client_instance = MagicMock()
        mock_qdrant.return_value = mock_client_instance

        client = QdrantClient()
        client.connect()
        client.create_collections()

        # Should create 2 collections
        assert mock_client_instance.recreate_collection.call_count == 2

    @patch("qdrant_client.QdrantClient")
    def test_add_code(self, mock_qdrant, mock_embedding):
        """Test adding code embedding"""
        mock_client_instance = MagicMock()
        mock_qdrant.return_value = mock_client_instance

        client = QdrantClient()
        client.connect()

        metadata = {
            "function_name": "Test",
            "module": "TestModule",
            "configuration": "DO",
        }

        result = client.add_code("test-id", mock_embedding, metadata)

        assert result is True
        mock_client_instance.upsert.assert_called_once()

    @patch("qdrant_client.QdrantClient")
    def test_search_code(self, mock_qdrant, mock_embedding):
        """Test semantic code search"""
        mock_client_instance = MagicMock()

        # Mock search results
        mock_hit = MagicMock()
        mock_hit.id = "hit-1"
        mock_hit.score = 0.95
        mock_hit.payload = {"function_name": "TestFunc"}
        mock_client_instance.search.return_value = [mock_hit]

        mock_qdrant.return_value = mock_client_instance

        client = QdrantClient()
        client.connect()

        results = client.search_code(mock_embedding, limit=10)

        assert len(results) == 1
        assert results[0]["id"] == "hit-1"
        assert results[0]["score"] == 0.95
        assert results[0]["payload"]["function_name"] == "TestFunc"
