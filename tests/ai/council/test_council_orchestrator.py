"""
Tests for Council Orchestrator
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.ai.council.council_orchestrator import (
    CouncilOrchestrator,
    CouncilConfig,
    CouncilResponse,
)


@pytest.fixture
def mock_orchestrator():
    """Mock AI orchestrator"""
    orchestrator = MagicMock()
    orchestrator._get_provider = MagicMock()
    return orchestrator


@pytest.fixture
def council_orchestrator(mock_orchestrator):
    """Council orchestrator instance"""
    return CouncilOrchestrator(mock_orchestrator)


@pytest.mark.asyncio
async def test_process_query_success(council_orchestrator, mock_orchestrator):
    """Test successful council query"""
    # Mock provider responses
    mock_provider = AsyncMock()
    mock_provider.generate = AsyncMock(
        side_effect=[
            "Response from kimi",
            "Response from qwen",
            "Response from gigachat",
            "Rankings: [1, 2, 3]",  # Peer review
            "Rankings: [2, 1, 3]",
            "Rankings: [1, 3, 2]",
            "Final synthesized answer",  # Chairman
        ]
    )

    mock_orchestrator._get_provider.return_value = mock_provider

    # Execute
    config = CouncilConfig(models=["kimi", "qwen", "gigachat"], chairman="kimi")

    result = await council_orchestrator.process_query(query="Test query", context={}, config=config)

    # Verify
    assert isinstance(result, CouncilResponse)
    assert result.final_answer == "Final synthesized answer"
    assert len(result.individual_opinions) == 3
    assert result.metadata["council_size"] == 3
    assert result.metadata["chairman"] == "kimi"


@pytest.mark.asyncio
async def test_process_query_with_defaults(council_orchestrator, mock_orchestrator):
    """Test council query with default config"""
    mock_provider = AsyncMock()
    mock_provider.generate = AsyncMock(return_value="Test response")
    mock_orchestrator._get_provider.return_value = mock_provider

    result = await council_orchestrator.process_query(query="Test query", context={})

    assert isinstance(result, CouncilResponse)


@pytest.mark.asyncio
async def test_stage1_first_opinions(council_orchestrator, mock_orchestrator):
    """Test Stage 1: First opinions"""
    mock_provider = AsyncMock()
    mock_provider.generate = AsyncMock(
        side_effect=[
            "Response 1",
            "Response 2",
            "Response 3",
        ]
    )
    mock_orchestrator._get_provider.return_value = mock_provider

    opinions = await council_orchestrator._stage1_first_opinions(
        query="Test", models=["kimi", "qwen", "gigachat"], context={}
    )

    assert len(opinions) == 3
    assert opinions[0]["model"] == "kimi"
    assert opinions[0]["response"] == "Response 1"


@pytest.mark.asyncio
async def test_stage1_handles_errors(council_orchestrator, mock_orchestrator):
    """Test Stage 1 handles provider errors"""
    mock_provider = AsyncMock()
    mock_provider.generate = AsyncMock(
        side_effect=[
            "Response 1",
            Exception("Provider error"),
            "Response 3",
        ]
    )
    mock_orchestrator._get_provider.return_value = mock_provider

    opinions = await council_orchestrator._stage1_first_opinions(
        query="Test", models=["kimi", "qwen", "gigachat"], context={}
    )

    # Should have 2 valid responses (error filtered out)
    assert len(opinions) == 2


def test_validate_config_min_size(council_orchestrator):
    """Test config validation: minimum size"""
    config = CouncilConfig(models=["kimi"], chairman="kimi")  # Only 1 model

    with pytest.raises(ValueError, match="minimum"):
        council_orchestrator._validate_config(config)


def test_validate_config_max_size(council_orchestrator):
    """Test config validation: maximum size"""
    config = CouncilConfig(models=["model" + str(i) for i in range(10)], chairman="kimi")  # 10 models

    with pytest.raises(ValueError, match="maximum"):
        council_orchestrator._validate_config(config)


def test_council_response_to_dict():
    """Test CouncilResponse to_dict conversion"""
    response = CouncilResponse(
        final_answer="Test answer",
        individual_opinions=[{"model": "kimi", "response": "test"}],
        peer_reviews=[],
        chairman_synthesis="Test synthesis",
        metadata={"council_size": 3},
    )

    result = response.to_dict()

    assert isinstance(result, dict)
    assert result["final_answer"] == "Test answer"
    assert result["metadata"]["council_size"] == 3
