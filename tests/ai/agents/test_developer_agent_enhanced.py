"""
Unit tests for Developer Agent Enhanced

Tests cover:
- BSL code generation with LLM
- BSL code generation fallback
- BSL code validation
- BSL prompt building
- Self-healing
- Code DNA stub
- Predictive Generation stub
"""

import pytest
from unittest.mock import AsyncMock
from src.ai.agents.developer_agent_enhanced import DeveloperAgentEnhanced


@pytest.fixture
def developer_agent():
    """Create Developer Agent instance for testing"""
    agent = DeveloperAgentEnhanced()
    return agent


@pytest.fixture
def mock_llm_selector():
    """Mock LLM Selector"""
    mock = AsyncMock()
    mock.generate = AsyncMock(return_value={
        "response": "Функция ПолучитьДанныеКлиента()\n  // Code\nКонецФункции",
        "model": "qwen-test"
    })
    return mock


class TestBSLCodeGeneration:
    """Test BSL code generation functionality"""
    
    @pytest.mark.asyncio
    async def test_generate_bsl_code_with_llm(
        self, 
        developer_agent, 
        mock_llm_selector
    ):
        """Test BSL generation with LLM"""
        developer_agent.llm_selector = mock_llm_selector
        
        result = await developer_agent.generate_bsl_code(
            prompt="Создать функцию получения данных клиента",
            context={"module_type": "common_module"}
        )
        
        assert "code" in result
        assert "Функция" in result["code"]
        assert "КонецФункции" in result["code"]
        mock_llm_selector.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_bsl_code_fallback(self, developer_agent):
        """Test BSL generation fallback without LLM"""
        developer_agent.llm_selector = None
        
        result = await developer_agent.generate_bsl_code(
            prompt="Создать функцию",
            context={"module_type": "common_module"}
        )
        
        assert "code" in result
        assert "placeholder" in result["code"].lower()
    
    @pytest.mark.asyncio
    async def test_generate_bsl_code_with_error(
        self, 
        developer_agent, 
        mock_llm_selector
    ):
        """Test BSL generation with LLM error"""
        mock_llm_selector.generate.side_effect = Exception("LLM Error")
        developer_agent.llm_selector = mock_llm_selector
        
        result = await developer_agent.generate_bsl_code(
            prompt="Создать функцию",
            context={}
        )
        
        assert "code" in result
        # Should fallback to placeholder


class TestBSLCodeValidation:
    """Test BSL code validation"""
    
    def test_validate_bsl_code_valid(self, developer_agent):
        """Test validation of valid BSL code"""
        valid_code = """
        Функция ПолучитьДанные()
            Попытка
                // Code here
                Возврат Результат;
            Исключение
                ЗаписьЖурналаРегистрации("Ошибка");
                ВызватьИсключение;
            КонецПопытки;
        КонецФункции
        """
        
        result = developer_agent._validate_bsl_code(valid_code)
        
        assert result["valid"] is True
        assert result["stats"]["functions"] == 1
        assert result["stats"]["has_error_handling"] is True
    
    def test_validate_bsl_code_invalid_structure(self, developer_agent):
        """Test validation of invalid BSL code structure"""
        invalid_code = """
        Функция ПолучитьДанные()
            // Missing КонецФункции
        """
        
        result = developer_agent._validate_bsl_code(invalid_code)
        
        assert result["valid"] is False
        assert len(result["issues"]) > 0
        assert any(i["type"] == "error" for i in result["issues"])
    
    def test_validate_bsl_code_no_error_handling(self, developer_agent):
        """Test validation warns about missing error handling"""
        code_without_try = """
        Функция ПолучитьДанные()
            Возврат Результат;
        КонецФункции
        """
        
        result = developer_agent._validate_bsl_code(code_without_try)
        
        assert result["stats"]["has_error_handling"] is False
    
    def test_validate_bsl_code_deprecated(self, developer_agent):
        """Test validation detects deprecated constructions"""
        code_with_deprecated = """
        Функция Тест()
            Сообщить("Тест");
        КонецФункции
        """
        
        result = developer_agent._validate_bsl_code(code_with_deprecated)
        
        warnings = [i for i in result["issues"] if i["type"] == "warning"]
        assert len(warnings) > 0


class TestBSLPromptBuilding:
    """Test BSL prompt building"""
    
    def test_build_bsl_prompt_common_module(self, developer_agent):
        """Test prompt for common module"""
        prompt = developer_agent._build_bsl_prompt(
            "Создать функцию",
            {"module_type": "common_module"}
        )
        
        assert "common_module" in prompt.lower() or "общего модуля" in prompt.lower()
        assert "Экспорт" in prompt
        assert "Clean Architecture" in prompt
    
    def test_build_bsl_prompt_object_module(self, developer_agent):
        """Test prompt for object module"""
        prompt = developer_agent._build_bsl_prompt(
            "Создать обработчик",
            {"module_type": "object_module"}
        )
        
        assert "object_module" in prompt.lower() or "модуля объекта" in prompt.lower()
        assert "ЭтотОбъект" in prompt or "ПередЗаписью" in prompt
    
    def test_build_bsl_prompt_manager_module(self, developer_agent):
        """Test prompt for manager module"""
        prompt = developer_agent._build_bsl_prompt(
            "Создать функцию",
            {"module_type": "manager_module"}
        )
        
        assert "manager_module" in prompt.lower() or "менеджера" in prompt.lower()


class TestSelfHealing:
    """Test self-healing functionality"""
    
    @pytest.mark.asyncio
    async def test_apply_self_healing_with_llm(
        self, 
        developer_agent, 
        mock_llm_selector
    ):
        """Test self-healing with LLM"""
        developer_agent.llm_selector = mock_llm_selector
        developer_agent.use_self_healing = True
        
        code = "Функция Тест() КонецФункции"
        concerns = [{"auto_fixable": True, "issue": "Missing error handling"}]
        
        result = await developer_agent._apply_self_healing(code, concerns)
        
        assert result is not None
        mock_llm_selector.generate.assert_called()
    
    @pytest.mark.asyncio
    async def test_apply_self_healing_no_fixable(self, developer_agent):
        """Test self-healing with no auto-fixable issues"""
        developer_agent.use_self_healing = True
        
        code = "Функция Тест() КонецФункции"
        concerns = [{"auto_fixable": False, "issue": "Manual fix needed"}]
        
        result = await developer_agent._apply_self_healing(code, concerns)
        
        assert result == code  # Should return original
    
    @pytest.mark.asyncio
    async def test_apply_self_healing_disabled(self, developer_agent):
        """Test self-healing when disabled"""
        developer_agent.use_self_healing = False
        
        code = "Функция Тест() КонецФункции"
        concerns = [{"auto_fixable": True}]
        
        result = await developer_agent._apply_self_healing(code, concerns)
        
        assert result == code


class TestRevolutionaryComponents:
    """Test revolutionary components stubs"""
    
    @pytest.mark.asyncio
    async def test_evolve_code_stub(self, developer_agent):
        """Test Code DNA stub"""
        developer_agent.code_dna = None
        
        result = await developer_agent.evolve_code(
            code="Функция Тест() КонецФункции",
            target_metrics={"complexity": "low"}
        )
        
        assert result["status"] == "code_dna_not_available"
        assert "original" in result
        assert "evolved" in result
    
    @pytest.mark.asyncio
    async def test_predict_next_code_stub(self, developer_agent):
        """Test Predictive Generation stub"""
        developer_agent.predictive_gen = None
        
        result = await developer_agent.predict_next_code(
            current_context="Функция Тест()"
        )
        
        assert result["status"] == "predictive_gen_not_available"
        assert "suggestions" in result
        assert result["confidence"] == 0.0


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_validate_empty_code(self, developer_agent):
        """Test validation of empty code"""
        result = developer_agent._validate_bsl_code("")
        
        assert result["valid"] is False
        assert any("empty" in i["message"].lower() for i in result["issues"])
    
    def test_validate_whitespace_only(self, developer_agent):
        """Test validation of whitespace-only code"""
        result = developer_agent._validate_bsl_code("   \n  \n  ")
        
        assert result["valid"] is False
    
    @pytest.mark.asyncio
    async def test_generate_with_empty_prompt(self, developer_agent):
        """Test generation with empty prompt"""
        result = await developer_agent.generate_bsl_code(
            prompt="",
            context={}
        )
        
        assert "code" in result


# Performance tests
class TestPerformance:
    """Test performance requirements"""
    
    @pytest.mark.asyncio
    async def test_validation_performance(self, developer_agent):
        """Test validation completes quickly"""
        import time
        
        large_code = "Функция Тест() КонецФункции\n" * 1000
        
        start = time.time()
        result = developer_agent._validate_bsl_code(large_code)
        duration = time.time() - start
        
        assert duration < 1.0  # Should complete in < 1 second
        assert result["valid"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
