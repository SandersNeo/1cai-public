# [NEXUS IDENTITY] ID: -6224874055347920224 | DATE: 2025-11-19

import pytest

from src.ai.agents.sql_optimizer import SQLOptimizer


@pytest.mark.asyncio
async def test_detects_select_star_and_no_where():
    optimizer = SQLOptimizer("postgresql")
    query = "SELECT * FROM orders JOIN customers ON orders.customer_id = customers.id"

    patterns = await optimizer._detect_sql_anti_patterns(query)
    types = {p["type"] for p in patterns}

    assert "SELECT_STAR" in types
    assert "NO_WHERE_CLAUSE" in types


@pytest.mark.asyncio
async def test_generates_optimizations_and_indexes():
    optimizer = SQLOptimizer("postgresql")
    query = "SELECT id, name FROM users"

    result = await optimizer.optimize_query(query, context={"database": "postgresql"})

    assert result["original_query"] == query
    assert "optimized_query" in result
    assert isinstance(result["optimizations"], list)
    assert isinstance(result["index_recommendations"], list)
    assert "expected_improvement" in result


@pytest.mark.asyncio
async def test_handles_n_plus_one_pattern():
    optimizer = SQLOptimizer("postgresql")
    query = """
Для Каждого Товар Из Товары Цикл
    Запрос = Новый Запрос;
    Запрос.Текст = "SELECT * FROM Prices WHERE Item = &Item";
    Запрос.УстановитьПараметр("Item", Товар);
    Результат = Запрос.Выполнить();
КонецЦикла;
"""
    patterns = await optimizer._detect_sql_anti_patterns(query)
    assert any(p["type"] == "N_PLUS_ONE" for p in patterns)
