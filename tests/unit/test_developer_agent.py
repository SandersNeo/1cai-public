import pytest
from unittest.mock import MagicMock, patch
from src.ai.agents.developer_agent import DeveloperAgent

@pytest.fixture
def developer_agent():
    return DeveloperAgent()

@pytest.mark.asyncio
async def test_initialization(developer_agent):
    assert developer_agent.agent_name == "developer_agent"
    assert "code_generation" in [c.value for c in developer_agent.capabilities]
    assert developer_agent.secure_core is not None

@pytest.mark.asyncio
async def test_process_generate_success(developer_agent):
    # Mock secure_core response
    developer_agent.secure_core.generate_code = MagicMock(return_value={
        "success": True,
        "suggestion": "print('Hello')",
        "token": "abc-123",
        "safety": {"safe": True, "score": 1.0},
        "requires_approval": True
    })

    input_data = {
        "action": "generate",
        "prompt": "Write hello world",
        "context": {}
    }

    result = await developer_agent.process(input_data)

    assert result["success"] is True
    assert result["data"]["suggestion"] == "print('Hello')"
    assert result["data"]["token"] == "abc-123"
    developer_agent.secure_core.generate_code.assert_called_once()

@pytest.mark.asyncio
async def test_process_generate_blocked(developer_agent):
    # Mock secure_core blocked response
    developer_agent.secure_core.generate_code = MagicMock(return_value={
        "blocked": True,
        "error": "Security violation"
    })

    input_data = {
        "action": "generate",
        "prompt": "Hack system",
    }

    result = await developer_agent.process(input_data)

    assert result["success"] is False
    assert result["error"] == "Security violation"

@pytest.mark.asyncio
async def test_process_review(developer_agent):
    # Mock secure_core analysis
    developer_agent.secure_core._analyze_code_safety = MagicMock(return_value={
        "safe": True,
        "concerns": [],
        "score": 1.0
    })

    input_data = {
        "action": "review",
        "code": "print('Safe')"
    }

    result = await developer_agent.process(input_data)

    assert result["success"] is True
    assert result["data"]["review_result"] == "Approved"
    developer_agent.secure_core._analyze_code_safety.assert_called_once_with("print('Safe')")

@pytest.mark.asyncio
async def test_unknown_action(developer_agent):
    input_data = {"action": "dance"}
    result = await developer_agent.process(input_data)
    assert result["success"] is False
    assert "Unknown action" in result["error"]
