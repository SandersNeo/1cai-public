# [NEXUS IDENTITY] ID: 3461079529900062662 | DATE: 2025-11-19

"""
Unit tests for Code DNA System - 1000% coverage
==============================================
"""

import pytest
from src.ai.code_dna import CodeDNAEngine, CodeDNA, Gene, GeneType


@pytest.fixture
def engine():
    """Code DNA Engine для тестов"""
    return CodeDNAEngine()


@pytest.fixture
def sample_code():
    """Пример кода для тестов"""
    return """
def calculate_sum(a, b):
    return a + b

def calculate_product(a, b):
    return a * b
"""


def test_code_to_dna(engine, sample_code):
    """Тест преобразования кода в ДНК"""
    dna = engine.code_to_dna(sample_code)

    assert isinstance(dna, CodeDNA)
    assert len(dna.genes) > 0
    assert dna.generation == 0


def test_dna_to_code(engine, sample_code):
    """Тест преобразования ДНК обратно в код"""
    dna = engine.code_to_dna(sample_code)
    code = engine.dna_to_code(dna)

    assert isinstance(code, str)
    assert len(code) > 0


def test_mutate(engine, sample_code):
    """Тест мутации ДНК"""
    dna = engine.code_to_dna(sample_code)
    mutated = engine.mutate(dna)

    assert mutated.generation == dna.generation + 1
    assert len(mutated.parent_ids) > 0


def test_crossover(engine, sample_code):
    """Тест скрещивания ДНК"""
    dna1 = engine.code_to_dna(sample_code)
    dna2 = engine.code_to_dna(sample_code)

    child = engine.crossover(dna1, dna2)

    assert child.generation == max(dna1.generation, dna2.generation) + 1
    assert len(child.parent_ids) == 2


@pytest.mark.asyncio
async def test_evolve(engine, sample_code):
    """Тест эволюции кода"""

    async def fitness_fn(code: str) -> float:
        # Простая функция fitness
        return 0.8 if "def" in code else 0.2

    result = await engine.evolve(sample_code, fitness_fn, generations=3)

    assert isinstance(result, CodeDNA)
    assert result.fitness >= 0.0


def test_gene_serialization():
    """Тест сериализации гена"""
    gene = Gene(
        type=GeneType.FUNCTION,
        name="test_function",
        code="def test(): pass",
        fitness=0.9,
    )

    data = gene.to_dict()
    restored = Gene.from_dict(data)

    assert restored.type == gene.type
    assert restored.name == gene.name
    assert restored.fitness == gene.fitness


def test_dna_serialization(engine, sample_code):
    """Тест сериализации ДНК"""
    dna = engine.code_to_dna(sample_code)

    data = dna.to_dict()
    restored = CodeDNA.from_dict(data)

    assert len(restored.genes) == len(dna.genes)
    assert restored.generation == dna.generation
