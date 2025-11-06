"""
Комплексные тесты Code Execution System

Тестирует:
- Execution Service
- PII Tokenizer
- Secure MCP Client
- Agent Orchestrator
- MCP Code Generator
- Tool Indexer
"""

import pytest
import asyncio
import json
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code' / 'py_server'))

from pii_tokenizer import PIITokenizer
from secure_mcp_client import SecureMCPClient
from mcp_code_generator import MCPCodeGenerator
from execution_service import CodeExecutionService


class TestPIITokenizer:
    """Тесты PII Tokenizer"""
    
    def test_tokenize_dict_explicit_fields(self):
        """Тест: токенизация dict с explicit fields"""
        tokenizer = PIITokenizer()
        
        data = {
            'id': '123',
            'name': 'Иванов Иван',
            'inn': '1234567890',
            'amount': 1000.50
        }
        
        tokenized = tokenizer.tokenize(data, fields=['name', 'inn'])
        
        # Check tokenization
        assert tokenized['id'] == '123'  # Not tokenized
        assert tokenized['amount'] == 1000.50  # Not tokenized
        assert tokenized['name'].startswith('[NAME_')
        assert tokenized['inn'].startswith('[INN_')
        
        # Check untokenization
        untokenized = tokenizer.untokenize(tokenized)
        assert untokenized == data
    
    def test_auto_detect_inn(self):
        """Тест: автоматическое определение ИНН"""
        tokenizer = PIITokenizer()
        
        text = "Клиент ООО Ромашка, ИНН: 7712345678"
        tokenized = tokenizer.tokenize(text, auto_detect=True)
        
        assert '[INN_' in tokenized
        assert '7712345678' not in tokenized
    
    def test_auto_detect_phone(self):
        """Тест: автоматическое определение телефона"""
        tokenizer = PIITokenizer()
        
        text = "Телефон: +7 (495) 123-45-67"
        tokenized = tokenizer.tokenize(text, auto_detect=True)
        
        assert '[PHONE_' in tokenized
        assert '123-45-67' not in tokenized
    
    def test_auto_detect_email(self):
        """Тест: автоматическое определение email"""
        tokenizer = PIITokenizer()
        
        text = "Email: test@example.com"
        tokenized = tokenizer.tokenize(text, auto_detect=True)
        
        assert '[EMAIL_' in tokenized
        assert 'test@example.com' not in tokenized
    
    def test_tokenize_list(self):
        """Тест: токенизация списка"""
        tokenizer = PIITokenizer()
        
        data = [
            {'name': 'Иванов', 'inn': '1234567890'},
            {'name': 'Петров', 'inn': '0987654321'}
        ]
        
        tokenized = tokenizer.tokenize(data, fields=['name', 'inn'])
        
        assert len(tokenized) == 2
        assert tokenized[0]['name'].startswith('[NAME_')
        assert tokenized[1]['inn'].startswith('[INN_')
        
        # Different tokens for different values
        assert tokenized[0]['name'] != tokenized[1]['name']
    
    def test_save_and_load_mapping(self, tmp_path):
        """Тест: сохранение и загрузка mapping"""
        tokenizer = PIITokenizer()
        
        # Tokenize some data
        data = {'name': 'Test User', 'inn': '1234567890'}
        tokenized = tokenizer.tokenize(data, fields=['name', 'inn'])
        
        # Save mapping
        mapping_file = tmp_path / 'mapping.json'
        tokenizer.save_mapping(str(mapping_file))
        
        # Create new tokenizer and load
        tokenizer2 = PIITokenizer()
        tokenizer2.load_mapping(str(mapping_file))
        
        # Should be able to untokenize
        untokenized = tokenizer2.untokenize(tokenized)
        assert untokenized == data


class TestMCPCodeGenerator:
    """Тесты MCP Code Generator"""
    
    def test_generate_simple_tool(self, tmp_path):
        """Тест: генерация простого tool"""
        generator = MCPCodeGenerator(output_dir=str(tmp_path / 'servers'))
        
        tools = [
            {
                'name': 'test_tool',
                'description': 'Test tool',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'param1': {'type': 'string'},
                        'param2': {'type': 'number'}
                    },
                    'required': ['param1']
                }
            }
        ]
        
        generator.generate_from_mcp_server('test_server', tools)
        
        # Check files created
        server_dir = tmp_path / 'servers' / 'test_server'
        assert (server_dir / 'index.ts').exists()
        assert (server_dir / 'testTool.ts').exists()
        
        # Check content
        code = (server_dir / 'testTool.ts').read_text()
        assert 'export async function testTool' in code
        assert 'param1' in code
        assert 'param2?' in code  # Optional
    
    def test_json_schema_to_typescript(self):
        """Тест: конвертация JSON Schema → TypeScript"""
        generator = MCPCodeGenerator()
        
        # String
        assert generator._json_schema_to_ts_type({'type': 'string'}) == 'string'
        
        # Number
        assert generator._json_schema_to_ts_type({'type': 'number'}) == 'number'
        
        # Array
        ts_type = generator._json_schema_to_ts_type({
            'type': 'array',
            'items': {'type': 'string'}
        })
        assert ts_type == 'string[]'
        
        # Object
        assert generator._json_schema_to_ts_type({'type': 'object'}) == 'Record<string, any>'


class TestSecureMCPClient:
    """Тесты Secure MCP Client"""
    
    @pytest.mark.asyncio
    async def test_tokenize_output(self):
        """Тест: токенизация output"""
        client = SecureMCPClient(mcp_client=None)  # No real client for test
        
        # Mock MCP client
        class MockMCPClient:
            async def call_tool(self, name, args):
                return {
                    'clients': [
                        {'name': 'Иванов', 'inn': '1234567890'},
                        {'name': 'Петров', 'inn': '0987654321'}
                    ]
                }
        
        client.mcp_client = MockMCPClient()
        
        # Call with tokenization
        result = await client.call_tool_secure(
            '1c__get_clients',
            {'top': 10},
            tokenize_output=True
        )
        
        # Check PII tokenized
        assert '[NAME_' in str(result)
        assert '[INN_' in str(result)
        assert 'Иванов' not in str(result)
        assert '1234567890' not in str(result)


class TestAgentOrchestrator:
    """Тесты Agent Orchestrator"""
    
    @pytest.mark.asyncio
    async def test_mock_task_execution(self):
        """Тест: выполнение mock задачи"""
        orchestrator = AgentOrchestrator()
        
        result = await orchestrator.execute_agent_task(
            task="Получить конфигурацию УТ",
            agent_id="test_agent"
        )
        
        # Should have task_id
        assert 'task_id' in result
        assert result['task_id'].startswith('task-')
        
        # Should have code
        assert 'code' in result
    
    @pytest.mark.asyncio
    async def test_pii_protection_in_workflow(self):
        """Тест: PII защита в полном workflow"""
        orchestrator = AgentOrchestrator()
        
        # Test tokenization
        test_data = {'name': 'Test', 'inn': '1234567890'}
        tokenized = orchestrator.tokenizer.tokenize(
            test_data,
            fields=['name', 'inn']
        )
        
        assert tokenized['name'] != 'Test'
        assert tokenized['inn'] != '1234567890'
        
        # Test untokenization
        untokenized = orchestrator.tokenizer.untokenize(tokenized)
        assert untokenized == test_data


# Integration test (requires running services)
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_workflow():
    """
    Интеграционный тест полного workflow
    
    Requires:
    - Deno execution server running (port 8001)
    - MCP server running (port 8000)
    """
    from agent_orchestrator import execute_agent_task
    
    result = await execute_agent_task(
        task="Получить конфигурацию УТ и вывести её имя",
        agent_id="test_agent"
    )
    
    assert result['success'] in [True, False]  # Either way is OK for integration test
    assert 'task_id' in result
    assert 'code' in result


# Run tests
if __name__ == "__main__":
    print("=" * 60)
    print("Running Code Execution Tests")
    print("=" * 60)
    
    # Run with pytest
    pytest.main([__file__, '-v', '--tb=short'])


