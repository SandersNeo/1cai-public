# [NEXUS IDENTITY] ID: 6109070275312414487 | DATE: 2025-11-19

"""
Tests for EnablementGeneratorWithGraph (enablement_with_graph.py).
"""

import pytest

from src.ai.code_graph import InMemoryCodeGraphBackend, Node, NodeKind
from src.ai.agents.enablement_with_graph import EnablementGeneratorWithGraph


@pytest.mark.asyncio
async def test_generate_enablement_plan() -> None:
    """Тест генерации плана enablement-материалов."""
    backend = InMemoryCodeGraphBackend()
    enablement_generator = EnablementGeneratorWithGraph(backend)

    # Создать тестовые узлы
    req_node = Node(
        id="ba_requirement:FEATURE001",
        kind=NodeKind.BA_REQUIREMENT,
        display_name="Feature: FEATURE001",
    )
    await backend.upsert_node(req_node)

    # Сгенерировать план
    result = await enablement_generator.generate_enablement_plan(
        "FEATURE001",
        audience="BA+Dev+QA",
        include_examples=True,
        use_graph=True,
    )

    assert "modules" in result
    assert "feature_name" in result
    assert len(result["modules"]) > 0
    # Должны быть примеры из графа
    assert any(len(m.get("examples", [])) > 0 for m in result["modules"])


@pytest.mark.asyncio
async def test_generate_guide() -> None:
    """Тест генерации гайда."""
    backend = InMemoryCodeGraphBackend()
    enablement_generator = EnablementGeneratorWithGraph(backend)

    # Создать модуль
    module = Node(
        id="module:src/feature.py",
        kind=NodeKind.MODULE,
        display_name="Module: feature.py",
    )
    await backend.upsert_node(module)

    # Сгенерировать гайд
    result = await enablement_generator.generate_guide(
        "feature",
        format="markdown",
        include_code_examples=True,
    )

    assert "title" in result
    assert "sections" in result
    assert "examples" in result
    assert "content" in result


@pytest.mark.asyncio
async def test_generate_presentation_outline() -> None:
    """Тест генерации outline презентации."""
    backend = InMemoryCodeGraphBackend()
    enablement_generator = EnablementGeneratorWithGraph(backend)

    result = await enablement_generator.generate_presentation_outline(
        "Test Topic",
        audience="stakeholders",
        duration_minutes=30,
    )

    assert "title" in result
    assert "slides" in result
    assert "audience" in result
    assert len(result["slides"]) > 0


@pytest.mark.asyncio
async def test_generate_onboarding_checklist() -> None:
    """Тест генерации onboarding чек-листа."""
    backend = InMemoryCodeGraphBackend()
    enablement_generator = EnablementGeneratorWithGraph(backend)

    result = await enablement_generator.generate_onboarding_checklist(
        role="BA",
        include_practical_tasks=True,
    )

    assert "role" in result
    assert "sections" in result
    assert len(result["sections"]) > 0
    # Должны быть практические задачи
    assert any(len(s.get("items", [])) > 0 for s in result["sections"])


@pytest.mark.asyncio
async def test_enablement_without_backend() -> None:
    """Тест работы без backend (graceful degradation)."""
    enablement_generator = EnablementGeneratorWithGraph(None)

    result = await enablement_generator.generate_enablement_plan(
        "Test Feature",
        include_examples=False,
        use_graph=False,
    )

    assert "modules" in result
    assert "feature_name" in result
    # Без графа примеры должны быть пустыми
    assert all(len(m.get("examples", [])) == 0 for m in result["modules"])
