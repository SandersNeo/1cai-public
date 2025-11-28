# [NEXUS IDENTITY] ID: -4185226648680435104 | DATE: 2025-11-19

"""
Code DNA System - Генетическое представление кода
=================================================

Система эволюционного улучшения кода:
- Генетическое представление кода
- Мутации (улучшения)
- Естественный отбор (тестирование)
- Эволюция (долгосрочное улучшение)

Научное обоснование:
- "Genetic Programming" (Koza, 1992+): Эволюционные алгоритмы
- "Evolutionary Code Improvement" (2024): Автоматическая оптимизация
"""

import ast
import logging
import random
import secrets
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List
from uuid import uuid4

logger = logging.getLogger(__name__)


class GeneType(str, Enum):
    """Типы генов в коде"""

    FUNCTION = "function"
    CLASS = "class"
    MODULE = "module"
    VARIABLE = "variable"
    CONSTANT = "constant"
    IMPORT = "import"


@dataclass
class Gene:
    """Ген в генетическом представлении кода"""

    id: str = field(default_factory=lambda: str(uuid4()))
    type: GeneType = GeneType.FUNCTION
    name: str = ""
    code: str = ""
    dependencies: List[str] = field(default_factory=list)
    fitness: float = 0.0  # Приспособленность (0.0-1.0)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Сериализация гена"""
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "code": self.code,
            "dependencies": self.dependencies,
            "fitness": self.fitness,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Gene":
        """Десериализация гена"""
        return cls(
            id=data["id"],
            type=GeneType(data["type"]),
            name=data["name"],
            code=data["code"],
            dependencies=data.get("dependencies", []),
            fitness=data.get("fitness", 0.0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class CodeDNA:
    """ДНК кода - генетическое представление"""

    id: str = field(default_factory=lambda: str(uuid4()))
    genes: List[Gene] = field(default_factory=list)
    fitness: float = 0.0  # Общая приспособленность
    generation: int = 0
    parent_ids: List[str] = field(default_factory=list)
    mutations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Сериализация ДНК"""
        return {
            "id": self.id,
            "genes": [g.to_dict() for g in self.genes],
            "fitness": self.fitness,
            "generation": self.generation,
            "parent_ids": self.parent_ids,
            "mutations": self.mutations,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CodeDNA":
        """Десериализация ДНК"""
        return cls(
            id=data["id"],
            genes=[Gene.from_dict(g) for g in data["genes"]],
            fitness=data.get("fitness", 0.0),
            generation=data.get("generation", 0),
            parent_ids=data.get("parent_ids", []),
            mutations=data.get("mutations", []),
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )

    def to_code(self) -> str:
        """Преобразование ДНК обратно в код"""
        # Сортировка генов по зависимостям
        sorted_genes = self._topological_sort()

        # Объединение кода
        code_parts = []
        for gene in sorted_genes:
            code_parts.append(gene.code)

        return "\n\n".join(code_parts)

    def _topological_sort(self) -> List[Gene]:
        """Топологическая сортировка генов по зависимостям"""
        # Простая реализация (можно улучшить)
        sorted_genes = []
        remaining = self.genes.copy()

        while remaining:
            # Поиск генов без зависимостей
            independent = [
                g
                for g in remaining
                if not any(dep in [r.id for r in remaining] for dep in g.dependencies)
            ]

            if not independent:
                # Циклические зависимости - добавляем все оставшиеся
                sorted_genes.extend(remaining)
                break

            sorted_genes.extend(independent)
            remaining = [g for g in remaining if g not in independent]

        return sorted_genes


class CodeDNAEngine:
    """
    Движок эволюции кода через генетические алгоритмы

    Процесс:
    1. Преобразование кода в ДНК
    2. Генерация мутаций
    3. Естественный отбор (тестирование)
    4. Скрещивание лучших вариантов
    5. Эволюция (повторение цикла)
    """

    def __init__(self):
        self._population: List[CodeDNA] = []
        self._generation = 0
        self._mutation_rate = 0.1  # 10% вероятность мутации
        self._crossover_rate = 0.7  # 70% вероятность скрещивания
        self._population_size = 50
        self._elite_size = 5  # Топ-5 сохраняются без изменений

        logger.info("CodeDNAEngine initialized")

    def code_to_dna(self, code: str) -> CodeDNA:
        """
        Преобразование кода в ДНК

        Args:
            code: Исходный код

        Returns:
            ДНК кода
        """
        try:
