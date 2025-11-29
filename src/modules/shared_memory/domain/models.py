"""
Shared Memory Domain Models

Модели для модуля общей памяти.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class MemoryItem(BaseModel):
    """Единица памяти (воспоминание)"""
    id: str = Field(..., description="Уникальный ID")
    content: str = Field(..., description="Текстовое содержание")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Метаданные (автор, тип, дата)")
    created_at: datetime = Field(default_factory=datetime.now, description="Дата создания")
    embedding: Optional[List[float]] = Field(None, description="Векторное представление (если есть)")

class SearchResult(BaseModel):
    """Результат поиска в памяти"""
    item: MemoryItem
    score: float = Field(..., description="Оценка релевантности (0-1)")

__all__ = ["MemoryItem", "SearchResult"]
