# [NEXUS IDENTITY] ID: 6396406680696838697 | DATE: 2025-11-19

"""
Tests for GraphQueryHelper (code_graph_query_helper.py).
"""

import pytest

from src.ai.code_graph import InMemoryCodeGraphBackend, Node, NodeKind
from src.ai.code_graph_query_helper import GraphQueryHelper


@pytest.mark.asyncio
async def test_find_nodes_by_query() -> None:
    """Тест поиска узлов по запросу."""
    backend = InMemoryCodeGraphBackend()
    helper = GraphQueryHelper(backend)

    # Создать тестовые узлы
    module_node = Node(
        id="module:ОбщийМодуль.УправлениеЗаказами",
        kind=NodeKind.MODULE,
        display_name="Module: ОбщийМодуль.УправлениеЗаказами",
        labels=["bsl", "1c", "module"],
        props={"path": "ОбщийМодуль.УправлениеЗаказами"},
    )
    await backend.upsert_node(module_node)

    function_node = Node(
        id="function:ОбщийМодуль.УправлениеЗаказами:СоздатьЗаказ",
        kind=NodeKind.FUNCTION,
        display_name="Function: СоздатьЗаказ",
        labels=["bsl", "1c", "function"],
        props={"name": "СоздатьЗаказ", "module": "ОбщийМодуль.УправлениеЗаказами"},
    )
    await backend.upsert_node(function_node)

    # Поиск по ключевому слову "заказ"
    found = await helper.find_nodes_by_query("где используется функция создания заказа")
    assert len(found) > 0
    assert any("заказ" in node.display_name.lower() for node in found)


@pytest.mark.asyncio
async def test_find_related_scenarios() -> None:
    """Тест поиска релевантных сценариев."""
    backend = InMemoryCodeGraphBackend()
    helper = GraphQueryHelper(backend)

    # Создать узлы разных типов
    module_node = Node(
        id="module:ОбщийМодуль.Тест",
        kind=NodeKind.MODULE,
        display_name="Module: ОбщийМодуль.Тест",
    )
    await backend.upsert_node(module_node)

    function_node = Node(
        id="function:ОбщийМодуль.Тест:Функция",
        kind=NodeKind.FUNCTION,
        display_name="Function: Функция",
    )
    await backend.upsert_node(function_node)

    test_node = Node(
        id="test_case:test_function",
        kind=NodeKind.TEST_CASE,
        display_name="test_function",
    )
    await backend.upsert_node(test_node)

    # Поиск сценариев для модулей и функций
    scenarios = await helper.find_related_scenarios(
        [module_node.id, function_node.id],
        max_scenarios=5,
    )
    assert len(scenarios) > 0
    # Должен быть рекомендован BA→Dev→QA сценарий
    assert any(s["id"] == "ba-dev-qa" for s in scenarios)

    # Поиск сценариев для тестов
    scenarios = await helper.find_related_scenarios(
        [test_node.id],
        max_scenarios=5,
    )
    assert len(scenarios) > 0
    # Должен быть рекомендован Code Review сценарий
    assert any(s["id"] == "code-review" for s in scenarios)


@pytest.mark.asyncio
async def test_extract_keywords() -> None:
    """Тест извлечения ключевых слов."""
    backend = InMemoryCodeGraphBackend()
    helper = GraphQueryHelper(backend)

    keywords = helper._extract_keywords("где используется функция создания заказа")
    assert "используется" in keywords
    assert "функция" in keywords
    assert "создания" in keywords
    assert "заказа" in keywords
    # Стоп-слова должны быть удалены
    assert "где" not in keywords


@pytest.mark.asyncio
async def test_search_by_display_name() -> None:
    """Тест поиска по display_name."""
    backend = InMemoryCodeGraphBackend()
    helper = GraphQueryHelper(backend)

    node = Node(
        id="module:Тест",
        kind=NodeKind.MODULE,
        display_name="Module: Тест",
    )
    await backend.upsert_node(node)

    found = await helper._search_by_display_name("тест", None)
    assert len(found) > 0
    assert any(n.id == node.id for n in found)


@pytest.mark.asyncio
async def test_deduplicate_and_rank() -> None:
    """Тест удаления дубликатов и ранжирования."""
    backend = InMemoryCodeGraphBackend()
    helper = GraphQueryHelper(backend)

    # Создать узлы с разной релевантностью
    node1 = Node(
        id="node1",
        kind=NodeKind.MODULE,
        display_name="Module: Заказ",
        labels=["заказ"],
    )
    node2 = Node(
        id="node2",
        kind=NodeKind.FUNCTION,
        display_name="Function: СоздатьЗаказ",
        labels=["заказ", "создание"],
    )
    node3 = Node(
        id="node3",
        kind=NodeKind.MODULE,
        display_name="Module: Другое",
    )

    # Дубликат node1
    node1_dup = Node(
        id="node1",
        kind=NodeKind.MODULE,
        display_name="Module: Заказ",
    )

    nodes = [node1, node2, node3, node1_dup]
    keywords = ["заказ", "создание"]

    ranked = helper._deduplicate_and_rank(nodes, keywords)
    # Должен быть удалён дубликат
    assert len(ranked) == 3
    # node2 должен быть первым (больше совпадений)
    assert ranked[0].id == "node2" or ranked[0].id == "node1"


@pytest.mark.asyncio
async def test_helper_without_backend() -> None:
    """Тест работы без backend (graceful degradation)."""
    helper = GraphQueryHelper(None)

    found = await helper.find_nodes_by_query("тест")
    assert len(found) == 0

    scenarios = await helper.find_related_scenarios(["node1"])
    assert len(scenarios) == 0
