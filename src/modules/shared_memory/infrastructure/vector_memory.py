"""
Vector Memory Service Implementation

Реализация сервиса памяти на основе TF-IDF и Cosine Similarity.
"""

import uuid
import numpy as np
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.modules.shared_memory.domain.models import MemoryItem, SearchResult
from src.modules.shared_memory.domain.ports import IMemoryService

class VectorMemoryService(IMemoryService):
    def __init__(self):
        self.items: List[MemoryItem] = []
        self.vectorizer = TfidfVectorizer()
        self.vectors = None
        self._is_dirty = False

    async def add(self, content: str, metadata: Dict[str, Any] = None) -> str:
        item_id = str(uuid.uuid4())
        item = MemoryItem(
            id=item_id,
            content=content,
            metadata=metadata or {}
        )
        self.items.append(item)
        self._is_dirty = True
        return item_id

    async def search(self, query: str, limit: int = 5) -> List[SearchResult]:
        if not self.items:
            return []

        # Re-fit vectorizer if data changed
        # Note: In production, we would use a pre-trained model or incremental learning
        # For MVP with small context, re-fitting is acceptable
        if self._is_dirty or self.vectors is None:
            corpus = [item.content for item in self.items]
            self.vectors = self.vectorizer.fit_transform(corpus)
            self._is_dirty = False

        query_vec = self.vectorizer.transform([query])
        
        # Calculate similarity
        similarities = cosine_similarity(query_vec, self.vectors).flatten()
        
        # Get top k indices
        top_indices = similarities.argsort()[-limit:][::-1]
        
        results = []
        for idx in top_indices:
            score = similarities[idx]
            if score > 0.0: # Filter out irrelevant results
                results.append(SearchResult(item=self.items[idx], score=float(score)))
                
        return results

    async def clear(self) -> None:
        self.items = []
        self.vectors = None
        self._is_dirty = False
