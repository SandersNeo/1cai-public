"""
Vector Index - Fast similarity search using FAISS

Provides efficient nearest neighbor search for embeddings in the
Continuum Memory System.

Uses FAISS (Facebook AI Similarity Search) for high-performance
vector indexing and retrieval.
"""

from typing import Callable, Dict, List, Optional, Tuple

import numpy as np

from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

# Try to import FAISS, fall back to simple implementation if not available
try:
    import faiss

    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS not available, using fallback implementation")


class VectorIndex:
    """
    Vector similarity search using FAISS

    Provides fast nearest neighbor search for embeddings.
    Falls back to simple numpy implementation if FAISS not available.
    """

    def __init__(self, dimension: int, index_type: str = "flat"):
        """
        Initialize vector index

        Args:
            dimension: Embedding dimension
            index_type: "flat" or "hnsw" (if FAISS available)
        """
        self.dimension = dimension
        self.index_type = index_type

        # Create index
        if FAISS_AVAILABLE:
            self._create_faiss_index(index_type)
        else:
            self._create_fallback_index()

        # Metadata storage
        self.keys: List[str] = []
        self.metadata_list: List[Optional[Dict]] = []
        self.embeddings: List[np.ndarray] = []  # For fallback

        logger.info(
            f"Created vector index",
            extra={
                "dimension": dimension,
                "index_type": index_type,
                "backend": "faiss" if FAISS_AVAILABLE else "numpy",
            },
        )

    def _create_faiss_index(self, index_type: str):
        """Create FAISS index"""
        if index_type == "flat":
            self.index = faiss.IndexFlatL2(self.dimension)
        elif index_type == "hnsw":
            self.index = faiss.IndexHNSWFlat(self.dimension, 32)
        else:
            raise ValueError(f"Unknown index type: {index_type}")

    def _create_fallback_index(self):
        """Create fallback numpy-based index"""
        self.index = None  # Will use self.embeddings

    def add(self, key: str, embedding: np.ndarray, metadata: Optional[Dict] = None):
        """
        Add embedding to index

        Args:
            key: Unique key
            embedding: Embedding vector
            metadata: Optional metadata
        """
        # Ensure correct shape and type
        if embedding.ndim == 1:
            embedding = embedding.reshape(1, -1)
        embedding = embedding.astype("float32")

        # Add to index
        if FAISS_AVAILABLE:
            self.index.add(embedding)
        else:
            self.embeddings.append(embedding[0])

        # Store key and metadata
        self.keys.append(key)
        self.metadata_list.append(metadata)

        logger.debug(f"Added embedding to index", extra={
                     "key": key, "total_size": len(self.keys)})

    def search(
        self, query: np.ndarray, k: int = 5, filter_fn: Optional[Callable[[Dict], bool]] = None
    ) -> List[Tuple[str, float]]:
        """
        Search for similar embeddings

        Args:
            query: Query embedding
            k: Number of results
            filter_fn: Optional filter function for metadata

        Returns:
            List of (key, similarity) tuples
        """
        # Ensure correct shape and type
        if query.ndim == 1:
            query = query.reshape(1, -1)
        query = query.astype("float32")

        # Search
        if FAISS_AVAILABLE:
            results = self._search_faiss(query, k, filter_fn)
        else:
            results = self._search_fallback(query, k, filter_fn)

        logger.debug(f"Search completed", extra={"k": k, "results_count": len(results)})

        return results

    def _search_faiss(
        self, query: np.ndarray, k: int, filter_fn: Optional[Callable[[Dict], bool]]
    ) -> List[Tuple[str, float]]:
        """Search using FAISS"""
        # Get extra results for filtering
        search_k = min(k * 2, len(self.keys))
        if search_k == 0:
            return []

        # Search in FAISS
        distances, indices = self.index.search(query, search_k)

        # Convert to results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self.keys):
                continue

            key = self.keys[idx]

            # Apply filter
            if filter_fn:
                meta = self.metadata_list[idx]
                if meta and not filter_fn(meta):
                    continue

            # Convert distance to similarity (0-1)
            similarity = 1.0 / (1.0 + float(dist))
            results.append((key, similarity))

            if len(results) >= k:
                break

        return results

    def _search_fallback(
        self, query: np.ndarray, k: int, filter_fn: Optional[Callable[[Dict], bool]]
    ) -> List[Tuple[str, float]]:
        """Search using numpy (fallback)"""
        if not self.embeddings:
            return []

        # Compute distances
        embeddings_matrix = np.array(self.embeddings)
        distances = np.linalg.norm(embeddings_matrix - query[0], axis=1)

        # Sort by distance
        sorted_indices = np.argsort(distances)

        # Convert to results
        results = []
        for idx in sorted_indices:
            key = self.keys[idx]

            # Apply filter
            if filter_fn:
                meta = self.metadata_list[idx]
                if meta and not filter_fn(meta):
                    continue

            # Convert distance to similarity
            dist = distances[idx]
            similarity = 1.0 / (1.0 + float(dist))
            results.append((key, similarity))

            if len(results) >= k:
                break

        return results

    def size(self) -> int:
        """Get number of vectors in index"""
        if FAISS_AVAILABLE:
            return self.index.ntotal
        else:
            return len(self.embeddings)

    def clear(self):
        """Clear all vectors"""
        if FAISS_AVAILABLE:
            self.index.reset()
        else:
            self.embeddings.clear()

        self.keys.clear()
        self.metadata_list.clear()

        logger.info("Cleared vector index")

    def __len__(self) -> int:
        """Get number of vectors"""
        return self.size()

    def __repr__(self) -> str:
        """String representation"""
        return (
            f"VectorIndex(dimension={self.dimension}, "
            f"size={self.size()}, "
            f"backend={'faiss' if FAISS_AVAILABLE else 'numpy'})"
        )
