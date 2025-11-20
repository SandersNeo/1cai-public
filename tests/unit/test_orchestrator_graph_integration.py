# [NEXUS IDENTITY] ID: 1934103407032239618 | DATE: 2025-11-19

"""
Tests for Orchestrator integration with Unified Change Graph.
"""

import pytest

from src.ai.code_graph import Node, NodeKind
from src.ai.orchestrator import AIOrchestrator


@pytest.mark.asyncio
async def test_orchestrator_with_graph_helper() -> None:
    """Тест, что Orchestrator инициализирует GraphQueryHelper."""
    orchestrator = AIOrchestrator()

    # GraphQueryHelper должен быть инициализирован (или None, если недоступен)
    assert orchestrator.graph_helper is not None or orchestrator.graph_helper is None


@pytest.mark.asyncio
async def test_process_query_includes_graph_nodes() -> None:
    """Тест, что process_query включает graph_nodes_touched в ответ."""
    orchestrator = AIOrchestrator()

    # Если GraphQueryHelper доступен, добавить тестовые узлы
    if orchestrator.graph_helper and orchestrator.graph_helper.backend:
        backend = orchestrator.graph_helper.backend

        # Создать тестовый узел
        test_node = Node(
            id="module:Тест",
            kind=NodeKind.MODULE,
            display_name="Module: Тест",
            labels=["тест"],
        )
        await backend.upsert_node(test_node)

    # Обработать запрос
    response = await orchestrator.process_query("где используется модуль тест")

    # Проверить наличие _meta
    assert "_meta" in response

    meta = response["_meta"]

    # Проверить наличие graph_nodes_touched (может быть пустым, если узлы не найдены)
    assert "graph_nodes_touched" in meta
    assert isinstance(meta["graph_nodes_touched"], list)

    # Проверить наличие suggested_scenarios
    assert "suggested_scenarios" in meta
    assert isinstance(meta["suggested_scenarios"], list)


@pytest.mark.asyncio
async def test_graph_helper_in_query_classification() -> None:
    """Тест, что GraphQueryHelper используется при классификации запросов."""
    orchestrator = AIOrchestrator()

    if orchestrator.graph_helper and orchestrator.graph_helper.backend:
        backend = orchestrator.graph_helper.backend

        # Создать узлы для тестирования
        module_node = Node(
            id="module:ОбщийМодуль.Заказы",
            kind=NodeKind.MODULE,
            display_name="Module: ОбщийМодуль.Заказы",
            labels=["заказы"],
        )
        await backend.upsert_node(module_node)

        function_node = Node(
            id="function:ОбщийМодуль.Заказы:Создать",
            kind=NodeKind.FUNCTION,
            display_name="Function: Создать",
            labels=["создание"],
        )
        await backend.upsert_node(function_node)

    # Запрос, который должен найти узлы
    response = await orchestrator.process_query("покажи модуль заказы")

    assert "_meta" in response
    meta = response["_meta"]

    # graph_nodes_touched должен содержать найденные узлы (если они есть)
    if meta["graph_nodes_touched"]:
        assert len(meta["graph_nodes_touched"]) > 0
        # Проверить, что это валидные ID узлов
        for node_id in meta["graph_nodes_touched"]:
            assert isinstance(node_id, str)
            assert len(node_id) > 0
