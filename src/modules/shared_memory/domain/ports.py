"""
Shared Memory Service Interface

Интерфейс сервиса общей памяти.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from .models import MemoryItem, SearchResult

class IMemoryService(ABC):
    @abstractmethod
    async def add(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """Добавить воспоминание"""
        pass

    @abstractmethod
    async def search(self, query: str, limit: int = 5) -> List[SearchResult]:
        """Поиск похожих воспоминаний"""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Очистить память"""
        pass
