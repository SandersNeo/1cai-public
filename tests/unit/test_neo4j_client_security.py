"""
Unit tests for Neo4jClient security features
"""

from unittest.mock import MagicMock, patch

import pytest

from src.db.neo4j_client import Neo4jClient


class TestNeo4jClientSecurity:
    """Test security hardening of Neo4jClient"""

    @pytest.fixture
    def mock_driver(self):
        with patch("src.db.neo4j_client.GraphDatabase") as mock_gd:
            driver = MagicMock()
            mock_gd.driver.return_value = driver
            yield driver

    def test_execute_query_parameters(self, mock_driver):
        """Test that execute_query uses parameters"""
        client = Neo4jClient(password="test")
        client.connect()

        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        cypher = "MATCH (n:User) WHERE n.name = $name RETURN n"
        params = {"name": "Admin"}

        client.execute_query(cypher, params)

        mock_session.run.assert_called_once_with(cypher, params)

    def test_execute_query_destructive_warning(self, mock_driver):
        """Test warning on destructive queries"""
        client = Neo4jClient(password="test")
        client.connect()

        with patch("src.db.neo4j_client.logger") as mock_logger:
            client.execute_query("MATCH (n) DETACH DELETE n")

            # Check if warning logged
            mock_logger.warning.assert_called()
            assert (
                "Destructive Cypher query detected"
                in mock_logger.warning.call_args[0][0]
            )

    def test_create_configuration_parameters(self, mock_driver):
        """Test that create_configuration uses parameters"""
        client = Neo4jClient(password="test")
        client.connect()

        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        config_data = {"name": "TestConfig", "full_name": "Full Name"}
        client.create_configuration(config_data)

        # Verify run was called
        args, kwargs = mock_session.run.call_args
        query = args[0]
        query_params = kwargs

        # Params should be passed as kwargs to run, not formatted into string
        assert "$name" in query
        assert config_data["name"] == query_params["name"]
