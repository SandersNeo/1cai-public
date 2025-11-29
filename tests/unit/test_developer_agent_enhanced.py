"""
Test for Developer Agent Enhanced
"""

import pytest
from src.ai.agents.developer_agent_enhanced import DeveloperAgentEnhanced
from src.ai.agents.base_agent import AgentCapability


@pytest.mark.asyncio
async def test_developer_agent_bsl_generation():
    """Test BSL code generation"""
    agent = DeveloperAgentEnhanced()
    
    result = await agent.execute(
        input_data={
            "action": "generate_code",
            "prompt": "Создай функцию для получения текущей даты",
            "context": {"module": "ОбщийМодуль"}
        },
        capability=AgentCapability.CODE_GENERATION
    )
    
    assert result["success"] is True
    assert "code" in result["result"]
    assert "Функция" in result["result"]["code"]


@pytest.mark.asyncio
async def test_developer_agent_code_review():
    """Test code review"""
    agent = DeveloperAgentEnhanced()
    
    code = """
    Функция ПолучитьДату() Экспорт
        Возврат ТекущаяДата();
    КонецФункции
    """
    
    result = await agent.execute(
        input_data={
            "action": "review_code",
            "code": code
        },
        capability=AgentCapability.CODE_REVIEW
    )
    
    assert result["success"] is True
    assert "review" in result["result"]
    assert "score" in result["result"]


@pytest.mark.asyncio
async def test_developer_agent_metrics():
    """Test that metrics are tracked"""
    agent = DeveloperAgentEnhanced()
    
    # Generate code
    await agent.execute(
        input_data={
            "action": "generate_code",
            "prompt": "Test function"
        },
        capability=AgentCapability.CODE_GENERATION
    )
    
    # Check stats
    status = agent.get_status()
    assert status["requests_processed"] > 0
    assert status["agent_name"] == "developer_agent_enhanced"
