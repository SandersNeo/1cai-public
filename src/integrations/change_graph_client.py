"""
Change Graph Client - Neo4j Integration

Provides integration with Neo4j Change Graph for:
- Affected tests selection
- Impact analysis
- Requirements traceability
- Code dependencies tracking
"""

import logging
from typing import Any, Dict, List, Optional

from neo4j.exceptions import AuthError, ServiceUnavailable

from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


class ChangeGraphClient:
    """
    Client for interacting with Neo4j Change Graph

    Features:
    - Affected tests selection based on changed files
    - Impact analysis for code changes
    - Requirements to code traceability
    - Dependency graph queries
    """

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        username: str = "neo4j",
        password: str = "password"
    ):
        """
        Initialize Change Graph client

        Args:
            uri: Neo4j connection URI
            username: Neo4j username
            password: Neo4j password
        """
        self.uri = uri
        self.username = username
        self.password = password
        self.driver = None
        self.logger = logging.getLogger("change_graph_client")

    async def connect(self) -> bool:
        """
        Connect to Neo4j database

        Returns:
            True if connected successfully
        """
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password)
            )

            # Test connection
            with self.driver.session() as session:
                result = session.run("RETURN 1")
                result.single()

            self.logger.info(f"Connected to Neo4j at {self.uri}")
            return True

        except (ServiceUnavailable, AuthError) as e:
            self.logger.error("Failed to connect to Neo4j: %s", e)
            return False
        except Exception as e:
            self.logger.error("Unexpected error connecting to Neo4j: %s", e)
            return False

    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            self.logger.info("Neo4j connection closed")

    async def get_affected_tests(
        self,
        changed_files: List[str]
    ) -> List[str]:
        """
        Get tests affected by changed files

        Args:
            changed_files: List of changed file paths

        Returns:
            List of affected test file paths
        """
        if not self.driver:
            self.logger.warning("Not connected to Neo4j")
            return []

        try:
            with self.driver.session() as session:
                # Cypher query to find affected tests
                query = """
                MATCH (file:File)-[:DEPENDS_ON*1..3]->(changed:File)
                WHERE changed.path IN $changed_files
                  AND file.type = 'test'
                RETURN DISTINCT file.path as test_path
                ORDER BY test_path
                """

                result = session.run(query, changed_files=changed_files)

                affected_tests = [record["test_path"] for record in result]

                self.logger.info(
                    f"Found {len(affected_tests)} affected tests "
                    f"for {len(changed_files)} changed files"
                )

                return affected_tests

        except Exception as e:
            self.logger.error("Error getting affected tests: %s", e)
            return []

    async def get_impact_analysis(
        self,
        change_description: str,
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze impact of a change

        Args:
            change_description: Description of the change
            file_path: Optional file path for targeted analysis

        Returns:
            Impact analysis results
        """
        if not self.driver:
            return {
                "status": "not_connected",
                "affected_components": [],
                "risk_level": "unknown"
            }

        try:
            with self.driver.session() as session:
                if file_path:
                    # Analyze impact for specific file
                    query = """
                    MATCH (file:File {path: $file_path})
                    MATCH (file)-[:DEPENDS_ON*1..2]->(dep:File)
                    RETURN DISTINCT dep.path as component,
                           dep.type as component_type
                    LIMIT 50
                    """
                    result = session.run(query, file_path=file_path)
                else:
                    # General impact analysis
                    query = """
                    MATCH (file:File)
                    WHERE file.path CONTAINS $keyword
                    RETURN file.path as component,
                           file.type as component_type
                    LIMIT 20
                    """
                    # Extract keyword from description
                    keyword = change_description.split(
                    )[0] if change_description else ""
                    result = session.run(query, keyword=keyword)

                affected_components = [
                    {
                        "path": record["component"],
                        "type": record["component_type"]
                    }
                    for record in result
                ]

                # Calculate risk level based on number of affected components
                risk_level = "low"
                if len(affected_components) > 20:
                    risk_level = "high"
                elif len(affected_components) > 10:
                    risk_level = "medium"

                return {
                    "status": "completed",
                    "affected_components": affected_components,
                    "risk_level": risk_level,
                    "component_count": len(affected_components)
                }

        except Exception as e:
            self.logger.error("Error in impact analysis: %s", e)
            return {
                "status": "error",
                "error": str(e),
                "affected_components": [],
                "risk_level": "unknown"
            }

    async def trace_requirement_to_code(
        self,
        requirement_id: str
    ) -> Dict[str, Any]:
        """
        Trace requirement to implementing code

        Args:
            requirement_id: Requirement identifier

        Returns:
            Traceability information
        """
        if not self.driver:
            return {
                "status": "not_connected",
                "implementations": [],
                "tests": []
            }

        try:
            with self.driver.session() as session:
                # Find code implementing requirement
                query = """
                MATCH (req:Requirement {id: $req_id})
                OPTIONAL MATCH (req)-[:IMPLEMENTED_BY]->(impl:File)
                OPTIONAL MATCH (req)-[:TESTED_BY]->(test:File)
                RETURN impl.path as implementation,
                       collect(DISTINCT test.path) as tests
                """

                result = session.run(query, req_id=requirement_id)
                record = result.single()

                if not record:
                    return {
                        "status": "not_found",
                        "requirement_id": requirement_id,
                        "implementations": [],
                        "tests": []
                    }

                return {
                    "status": "found",
                    "requirement_id": requirement_id,
                    "implementations": [record["implementation"]] if record["implementation"] else [],
                    "tests": record["tests"] or []
                }

        except Exception as e:
            self.logger.error("Error tracing requirement: %s", e)
            return {
                "status": "error",
                "error": str(e),
                "requirement_id": requirement_id,
                "implementations": [],
                "tests": []
            }

    async def get_code_dependencies(
        self,
        file_path: str,
        depth: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Get dependencies for a code file

        Args:
            file_path: Path to the file
            depth: Dependency depth (1-3)

        Returns:
            List of dependencies
        """
        if not self.driver:
            return []

        try:
            with self.driver.session() as session:
                query = f"""
                MATCH (file:File {{path: $file_path}})
                MATCH (file)-[:DEPENDS_ON*1..{depth}]->(dep:File)
                RETURN DISTINCT dep.path as dependency,
                       dep.type as dep_type,
                       dep.language as language
                ORDER BY dependency
                LIMIT 100
                """

                result = session.run(query, file_path=file_path)

                dependencies = [
                    {
                        "path": record["dependency"],
                        "type": record["dep_type"],
                        "language": record["language"]
                    }
                    for record in result
                ]

                return dependencies

        except Exception as e:
            self.logger.error("Error getting dependencies: %s", e)
            return []


# Singleton instance
_change_graph_client: Optional[ChangeGraphClient] = None


def get_change_graph_client(
    uri: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None
) -> ChangeGraphClient:
    """
    Get or create Change Graph client singleton

    Args:
        uri: Neo4j URI (optional, uses default if not provided)
        username: Neo4j username (optional)
        password: Neo4j password (optional)

    Returns:
        ChangeGraphClient instance
    """
    global _change_graph_client

    if _change_graph_client is None:
        _change_graph_client = ChangeGraphClient(
            uri=uri or "bolt://localhost:7687",
            username=username or "neo4j",
            password=password or "password"
        )

    return _change_graph_client


__all__ = ["ChangeGraphClient", "get_change_graph_client"]
