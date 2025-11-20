from typing import Dict, Any
import asyncio
from src.ai.strategies.base import AIStrategy
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class SemanticSearchStrategy(AIStrategy):
    def __init__(self, qdrant_client=None, embedding_service=None):
        self.qdrant_client = qdrant_client
        self.embedding_service = embedding_service

    async def execute(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle semantic code search using Qdrant vector database
        Generates embedding and finds similar code snippets
        """
        try:
            # Generate embedding for the query
            # Assuming embedding_service is passed or we import it if not
            if not self.embedding_service:
                from src.services.embedding_service import EmbeddingService

                self.embedding_service = EmbeddingService()

            query_embedding = await self.embedding_service.generate_embedding(query)

            logger.info(
                "Generated embedding for query",
                extra={"embedding_dimension": len(query_embedding)},
            )

            # Search in Qdrant
            try:
                if not self.qdrant_client:
                    from src.db.qdrant_client import QdrantClient

                    self.qdrant_client = QdrantClient()

                # Search for similar code
                search_results = await asyncio.to_thread(
                    self.qdrant_client.search,
                    collection_name="code_snippets",
                    query_vector=query_embedding,
                    limit=context.get("limit", 10),
                )

                # Format results
                formatted_results = []
                for result in search_results:
                    formatted_results.append(
                        {
                            "code": result.payload.get("code", ""),
                            "function_name": result.payload.get(
                                "function_name", "Unknown"
                            ),
                            "module": result.payload.get("module", "Unknown"),
                            "score": float(result.score),
                            "description": result.payload.get("description", ""),
                        }
                    )

                logger.info(
                    "Found similar code snippets",
                    extra={"results_count": len(formatted_results)},
                )

                return {
                    "type": "semantic_search",
                    "service": "qdrant",
                    "query": query,
                    "results": formatted_results,
                    "count": len(formatted_results),
                    "explanation": f"Found {len(formatted_results)} code snippets similar to your query",
                }

            except ImportError:
                logger.warning("Qdrant client not available")
                return {
                    "type": "semantic_search",
                    "service": "qdrant",
                    "message": "Qdrant not configured. Install and configure Qdrant for semantic search.",
                    "query": query,
                }

        except Exception as e:
            logger.error(
                "Error in semantic search",
                extra={"error": str(e), "error_type": type(e).__name__},
                exc_info=True,
            )
            return {"type": "semantic_search", "error": str(e), "service": "qdrant"}
