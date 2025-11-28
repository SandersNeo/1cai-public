import asyncio
from typing import Any, Dict

from src.ai.strategies.base import AIStrategy
from src.db.qdrant_client import QdrantClient
from src.services.embedding_service import EmbeddingService
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class QdrantStrategy(AIStrategy):
    """Strategy for Semantic Search with Qdrant"""

    def __init__(self):
        try:
