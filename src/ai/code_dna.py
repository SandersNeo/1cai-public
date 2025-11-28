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
            # Парсинг AST
            tree = ast.parse(code)

            genes = []

            # Извлечение функций, классов и т.д.
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    gene = Gene(
                        type=GeneType.FUNCTION,
                        name=node.name,
                        code=ast.unparse(node),
                        dependencies=self._extract_dependencies(node),
                    )
                    genes.append(gene)

                elif isinstance(node, ast.ClassDef):
                    gene = Gene(
                        type=GeneType.CLASS,
                        name=node.name,
                        code=ast.unparse(node),
                        dependencies=self._extract_dependencies(node),
                    )
                    genes.append(gene)

            dna = CodeDNA(genes=genes, generation=0)

            logger.info(
                f"Code converted to DNA: {len(genes)} genes",
                extra={"genes_count": len(genes)},
            )

            return dna

        except Exception as e:
            logger.error(
                "Failed to convert code to DNA", extra={"error": str(e)}, exc_info=True
            )
            # Возврат пустого ДНК при ошибке
            return CodeDNA()

    def _extract_dependencies(self, node: ast.AST) -> List[str]:
        """Извлечение зависимостей из узла AST"""
        dependencies = []

        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                if child.id not in dependencies:
                    dependencies.append(child.id)
            elif isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    if child.func.id not in dependencies:
                        dependencies.append(child.func.id)

        return dependencies

    def dna_to_code(self, dna: CodeDNA) -> str:
        """
        Преобразование ДНК обратно в код

        Args:
            dna: ДНК кода

        Returns:
            Код
        """
        return dna.to_code()

    def mutate(self, dna: CodeDNA) -> CodeDNA:
        """
        Генерация мутации ДНК

        Args:
            dna: Исходное ДНК

        Returns:
            Мутированное ДНК
        """
        mutated = CodeDNA(
            genes=dna.genes.copy(),
            generation=dna.generation + 1,
            parent_ids=[dna.id],
            mutations=dna.mutations.copy(),
        )

        # Мутация случайных генов
        for gene in mutated.genes:
            if random.random() < self._mutation_rate:
                # Применение мутации
                mutated_gene = self._apply_mutation(gene)
                mutated.genes[mutated.genes.index(gene)] = mutated_gene
                mutated.mutations.append(f"mutated_{gene.id}")

        logger.debug(
            f"DNA mutated: {len(mutated.mutations)} mutations",
            extra={"dna_id": mutated.id, "mutations_count": len(mutated.mutations)},
        )

        return mutated

    def _apply_mutation(self, gene: Gene) -> Gene:
        """Применение мутации к гену"""
        # Простые мутации:
        # 1. Переименование переменных
        # 2. Изменение порядка операций
        # 3. Оптимизация кода

        # TODO: Реальная реализация мутаций
        # Здесь можно использовать AI для генерации улучшений

        mutated = Gene(
            id=gene.id,
            type=gene.type,
            name=gene.name,
            code=gene.code,  # Пока без изменений
            dependencies=gene.dependencies,
            fitness=gene.fitness,
            metadata=gene.metadata,
        )

        return mutated

    def crossover(self, dna1: CodeDNA, dna2: CodeDNA) -> CodeDNA:
        """
        Скрещивание двух ДНК

        Args:
            dna1: Первое ДНК
            dna2: Второе ДНК

        Returns:
            Новое ДНК (потомок)
        """
        # Выбор лучших генов от каждого родителя
        child_genes = []

        # Гены от первого родителя (лучшие по fitness)
        top_genes_1 = sorted(dna1.genes, key=lambda g: g.fitness, reverse=True)[
            : len(dna1.genes) // 2
        ]
        child_genes.extend(top_genes_1)

        # Гены от второго родителя (лучшие по fitness)
        top_genes_2 = sorted(dna2.genes, key=lambda g: g.fitness, reverse=True)[
            : len(dna2.genes) // 2
        ]
        child_genes.extend(top_genes_2)

        # Удаление дубликатов
        unique_genes = []
        seen_ids = set()
        for gene in child_genes:
            if gene.id not in seen_ids:
                unique_genes.append(gene)
                seen_ids.add(gene.id)

        child = CodeDNA(
            genes=unique_genes,
            generation=max(dna1.generation, dna2.generation) + 1,
            parent_ids=[dna1.id, dna2.id],
        )

        logger.debug(
            f"DNA crossover: {len(child.genes)} genes",
            extra={"child_id": child.id, "parent1_id": dna1.id, "parent2_id": dna2.id},
        )

        return child

    async def evolve(
        self, initial_code: str, fitness_fn: callable, generations: int = 10
    ) -> CodeDNA:
        """
        Эволюция кода

        Args:
            initial_code: Исходный код
            fitness_fn: Функция оценки приспособленности
            generations: Количество поколений

        Returns:
            Лучшее ДНК после эволюции
        """
        # 1. Преобразование в ДНК
        initial_dna = self.code_to_dna(initial_code)

        # 2. Инициализация популяции
        self._population = [initial_dna]
        self._generation = 0

        # 3. Эволюция
        for generation in range(generations):
            logger.info("Generation {generation + 1}/%s", generations)

            # Оценка приспособленности
            await self._evaluate_fitness(fitness_fn)

            # Естественный отбор
            self._natural_selection()

            # Генерация нового поколения
            self._generate_next_generation()

            # Лучшее ДНК
            best = max(self._population, key=lambda d: d.fitness)
            logger.info(
                f"Best fitness: {best.fitness:.4f}",
                extra={"generation": generation + 1, "best_id": best.id},
            )

        # Возврат лучшего
        return max(self._population, key=lambda d: d.fitness)

    async def _evaluate_fitness(self, fitness_fn: callable) -> None:
        """Оценка приспособленности популяции"""
        for dna in self._population:
            code = self.dna_to_code(dna)
            fitness = await fitness_fn(code)
            dna.fitness = fitness

            # Обновление fitness генов
            for gene in dna.genes:
                gene.fitness = fitness  # Упрощенная версия

    def _natural_selection(self) -> None:
        """Естественный отбор - выбор лучших"""
        # Сортировка по fitness
        self._population.sort(key=lambda d: d.fitness, reverse=True)

        # Сохранение элиты
        elite = self._population[: self._elite_size]

        # Отбор остальных (50% лучших)
        selection_size = (self._population_size - self._elite_size) // 2
        selected = self._population[:selection_size]

        self._population = elite + selected

    def _generate_next_generation(self) -> None:
        """Генерация нового поколения"""
        new_population = self._population.copy()

        # Генерация потомков
        while len(new_population) < self._population_size:
            # Выбор родителей
            parent1 = random.choice(self._population)
            parent2 = random.choice(self._population)

            if random.random() < self._crossover_rate:
                # Скрещивание
                child = self.crossover(parent1, parent2)
            else:
                # Мутация
                child = self.mutate(parent1)

            new_population.append(child)

        self._population = new_population[: self._population_size]
        self._generation += 1
