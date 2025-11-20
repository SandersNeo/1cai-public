# [NEXUS IDENTITY] ID: 1730073979839046536 | DATE: 2025-11-19

"""
Unit tests for Neo4jClient
"""

from unittest.mock import patch, MagicMock
from src.db.neo4j_client import Neo4jClient


class TestNeo4jClient:
    """Test Neo4j client functionality"""

    @patch("neo4j.GraphDatabase.driver")
    def test_connect_success(self, mock_driver):
        """Test successful Neo4j connection"""
        mock_driver_instance = MagicMock()
        mock_driver.return_value = mock_driver_instance

        client = Neo4jClient(password="test")
        result = client.connect()

        assert result is True
        assert client.driver is not None
        mock_driver_instance.verify_connectivity.assert_called_once()

    @patch("neo4j.GraphDatabase.driver")
    def test_create_configuration(self, mock_driver, sample_configuration_data):
        """Test creating configuration node"""
        mock_driver_instance = MagicMock()
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.single.return_value = {"name": "TEST"}
        mock_session.run.return_value = mock_result
        mock_driver_instance.session.return_value.__enter__.return_value = mock_session
        mock_driver.return_value = mock_driver_instance

        client = Neo4jClient(password="test")
        client.connect()

        success = client.create_configuration(sample_configuration_data)

        assert success is True
        mock_session.run.assert_called_once()

    @patch("neo4j.GraphDatabase.driver")
    def test_get_function_dependencies(self, mock_driver):
        """Test getting function dependencies"""
        mock_driver_instance = MagicMock()
        mock_session = MagicMock()

        # Mock result records
        mock_record1 = {"module": "Module1", "function": "Func1"}
        mock_record2 = {"module": "Module2", "function": "Func2"}
        mock_result = [mock_record1, mock_record2]
        mock_session.run.return_value = mock_result
        mock_driver_instance.session.return_value.__enter__.return_value = mock_session
        mock_driver.return_value = mock_driver_instance

        client = Neo4jClient(password="test")
        client.connect()

        deps = client.get_function_dependencies("TestModule", "TestFunction")

        assert len(deps) == 2
        assert deps[0]["module"] == "Module1"
        assert deps[1]["function"] == "Func2"

    @patch("neo4j.GraphDatabase.driver")
    def test_get_statistics(self, mock_driver):
        """Test getting database statistics"""
        mock_driver_instance = MagicMock()
        mock_session = MagicMock()
        mock_record = {
            "configurations": 4,
            "objects": 100,
            "modules": 500,
            "functions": 3000,
            "function_calls": 5000,
        }
        mock_result = MagicMock()
        mock_result.single.return_value = mock_record
        mock_session.run.return_value = mock_result
        mock_driver_instance.session.return_value.__enter__.return_value = mock_session
        mock_driver.return_value = mock_driver_instance

        client = Neo4jClient(password="test")
        client.connect()

        stats = client.get_statistics()

        assert stats["configurations"] == 4
        assert stats["modules"] == 500
        assert stats["functions"] == 3000
