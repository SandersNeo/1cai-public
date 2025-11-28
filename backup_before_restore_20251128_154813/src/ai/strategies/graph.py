import asyncio
from typing import Any, Dict

from src.ai.nl_to_cypher import get_nl_to_cypher_converter
from src.ai.strategies.base import AIStrategy
from src.api.dependencies import get_neo4j_client
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class Neo4jStrategy(AIStrategy):
    """Strategy for Neo4j Graph Queries"""

    def __init__(self):
        # No side effects in init
        pass

    @property
    def service_name(self) -> str:
        return "neo4j"

    async def execute(self,
                      query: str,
                      context: Dict[str,
                                    Any]) -> Dict[str,
                                                  Any]:
        client = get_neo4j_client()
        if not client:
            return {
                "error": "Neo4j client not available",
                "service": self.service_name}

        try:
