import re
from typing import Any, Dict, List, Optional

from src.config import USE_TEMPORAL_GNN
from src.db.neo4j_client import Neo4jClient
from src.db.qdrant_client import QdrantClient
from src.services.embedding_service import EmbeddingService
from src.utils.retry_utils import retry_on_transient_error
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

MAX_SEMANTIC_QUERY_LENGTH = 5000


class GraphService:
    """
    Service for graph database operations with async support.

    With optional Temporal GNN for code evolution tracking.
    """

    def __init__(self, neo4j_client: Neo4jClient):
        self.neo4j = neo4j_client

        # Temporal GNN integration (optional)
        self._temporal = None
        if USE_TEMPORAL_GNN:
            try:
