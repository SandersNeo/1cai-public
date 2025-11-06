"""
Agent Orchestrator

Центральный компонент для оркестрации AI агентов с Code Execution
"""

import asyncio
import logging
from typing import Dict, Any, Optional
import uuid
from datetime import datetime

from execution_service import CodeExecutionService, ExecutionResult
from secure_mcp_client import SecureMCPClient
from pii_tokenizer import PIITokenizer, get_tokenizer

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Оркестратор для AI агентов с code execution
    
    Координирует:
    - Генерацию кода агентами
    - Безопасное выполнение в sandbox
    - PII protection
    - Metrics и logging
    - (Опционально) Сохранение skills
    
    Usage:
        orchestrator = AgentOrchestrator()
        
        result = await orchestrator.execute_agent_task(
            task="Получить метаданные конфигурации УТ",
            agent_id="architect_agent"
        )
    """
    
    def __init__(
        self,
        execution_service: Optional[CodeExecutionService] = None,
        secure_client: Optional[SecureMCPClient] = None,
        tokenizer: Optional[PIITokenizer] = None
    ):
        self.execution_service = execution_service or CodeExecutionService()
        self.secure_client = secure_client or SecureMCPClient()
        self.tokenizer = tokenizer or get_tokenizer()
    
    async def execute_agent_task(
        self,
        task: str,
        agent_id: str = "default_agent",
        timeout: Optional[int] = None,
        save_skill: bool = False
    ) -> Dict[str, Any]:
        """
        Выполнить задачу агента с code execution
        
        Workflow:
        1. Agent генерирует TypeScript код
        2. Выполнение в sandbox (Deno)
        3. PII protection (если нужно)
        4. Возврат результатов
        5. (Опционально) Сохранение skill
        
        Args:
            task: Описание задачи для агента
            agent_id: ID агента
            timeout: Timeout выполнения (ms)
            save_skill: Автоматически сохранить как skill если успешно
        
        Returns:
            Dict с результатами:
                - success: bool
                - output: str (safe for model context)
                - execution_time_ms: int
                - memory_used_mb: float
                - code: str (generated code)
                - skill_id: str (if saved)
                - task_id: str
        """
        
        task_id = self._generate_task_id()
        
        logger.info(
            f"Starting task - Agent: {agent_id}, Task ID: {task_id}, "
            f"Description: {task[:100]}..."
        )
        
        try:
            # Step 1: Agent генерирует код
            # TODO: Интегрировать с вашими AI agents
            code = await self._agent_generate_code(task, agent_id)
            
            if not code:
                return {
                    'success': False,
                    'error': 'Agent failed to generate code',
                    'task_id': task_id,
                }
            
            # Step 2: Execute в sandbox
            execution_result = await self.execution_service.execute_with_monitoring(
                code=code,
                agent_id=agent_id,
                task_id=task_id,
                timeout=timeout
            )
            
            if not execution_result.success:
                logger.error(
                    f"Execution failed - Task: {task_id}, "
                    f"Errors: {execution_result.errors}"
                )
                return {
                    'success': False,
                    'error': execution_result.errors,
                    'code': code,
                    'task_id': task_id,
                    'execution_time_ms': execution_result.execution_time_ms,
                }
            
            # Step 3: PII protection (токенизировать output если есть PII)
            safe_output = self.tokenizer.tokenize(
                execution_result.output,
                auto_detect=True
            )
            
            # Step 4: (Опционально) Сохранить как skill
            skill_id = None
            if save_skill and self._should_save_as_skill(code, execution_result):
                skill_id = await self._save_as_skill(
                    code=code,
                    task_description=task,
                    execution_result=execution_result
                )
            
            # Success!
            logger.info(
                f"Task completed - Task: {task_id}, "
                f"Time: {execution_result.execution_time_ms}ms, "
                f"Memory: {execution_result.memory_used_mb}MB"
            )
            
            return {
                'success': True,
                'output': safe_output,
                'execution_time_ms': execution_result.execution_time_ms,
                'memory_used_mb': execution_result.memory_used_mb,
                'code': code,
                'skill_id': skill_id,
                'task_id': task_id,
            }
        
        except Exception as e:
            logger.error(f"Orchestration error - Task: {task_id}: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'task_id': task_id,
            }
    
    async def _agent_generate_code(
        self,
        task: str,
        agent_id: str
    ) -> Optional[str]:
        """
        Агент генерирует TypeScript код для задачи
        
        TODO: Интегрировать с вашими существующими AI agents
        
        Сейчас: Mock implementation
        """
        
        # System prompt для agent
        system_prompt = self._get_system_prompt(agent_id)
        
        # User prompt
        user_prompt = f"""
Задача: {task}

Сгенерируй TypeScript код для выполнения этой задачи.

Используй доступные MCP tools через import:
- ./servers/1c/ - работа с 1С
- ./servers/neo4j/ - графовая база
- ./servers/qdrant/ - векторный поиск
- ./servers/postgres/ - SQL база

Сначала найди нужные tools через searchTools если нужно.

Код должен быть полным и выполняемым.
"""
        
        # TODO: Вызвать LLM (OpenAI, Claude, или local Ollama)
        # code = await self._call_llm(system_prompt, user_prompt)
        
        # Mock для тестирования
        code = self._generate_mock_code(task)
        
        return code
    
    def _get_system_prompt(self, agent_id: str) -> str:
        """Получить system prompt для агента"""
        
        base_prompt = """
Ты - AI агент для проекта 1C AI Stack.

У тебя есть доступ к MCP tools через TypeScript API.

Доступные servers:
- ./servers/1c/ - работа с 1С (getConfiguration, executeQuery, getMetadata, etc.)
- ./servers/neo4j/ - граф зависимостей (runCypher, storeGraph)
- ./servers/qdrant/ - векторный поиск (search, insert)
- ./servers/postgres/ - SQL база
- ./servers/elasticsearch/ - логи и полнотекстовый поиск

ВАЖНО:
1. Сначала найди нужные tools через searchTools() если не уверен какие tools использовать
2. Импортируй только нужные tools
3. Обрабатывай ошибки (try-catch)
4. Выводи результаты через console.log()
5. Сохраняй промежуточные файлы в ./workspace/ если нужно

Пиши чистый, безопасный, эффективный TypeScript код.
"""
        
        # Agent-specific additions
        agent_prompts = {
            'architect_agent': '\nТы - AI Architect. Анализируй архитектуру, зависимости, anti-patterns.',
            'developer_agent': '\nТы - AI Developer. Генерируй код, оптимизируй, рефактори.',
            'qa_agent': '\nТы - QA Engineer. Анализируй код на баги, генерируй тесты.',
            'techlog_agent': '\nТы - Tech Log Analyzer. Анализируй логи, находи проблемы.',
        }
        
        return base_prompt + agent_prompts.get(agent_id, '')
    
    def _generate_mock_code(self, task: str) -> str:
        """
        Mock code generation для тестирования
        
        TODO: Заменить на реальную интеграцию с LLM
        """
        
        # Simple mock based on task keywords
        if 'конфигурация' in task.lower() or 'configuration' in task.lower():
            return '''
// Get 1C configuration
import { getConfiguration } from './servers/1c/getConfiguration.ts';

const config = await getConfiguration({
  name: 'УТ',
  includeMetadata: true
});

console.log(`Configuration: ${config.name || 'УТ'}`);
console.log(`Loaded successfully!`);
'''
        else:
            return f'''
// Task: {task}
console.log("Task: {task}");
console.log("Code generation not implemented for this task type");
console.log("TODO: Integrate with LLM");
'''
    
    def _should_save_as_skill(
        self,
        code: str,
        execution_result: ExecutionResult
    ) -> bool:
        """
        Определить, стоит ли сохранить код как skill
        
        Критерии:
        - Успешное выполнение
        - Код достаточно длинный (> 10 строк)
        - Есть function definitions
        - Переиспользуемая логика
        """
        
        if not execution_result.success:
            return False
        
        lines = code.strip().split('\n')
        if len(lines) < 10:
            return False
        
        # Check for function definitions
        has_function = (
            'async function' in code or
            'function' in code or
            'export' in code
        )
        
        if not has_function:
            return False
        
        # TODO: More sophisticated analysis
        
        return True
    
    async def _save_as_skill(
        self,
        code: str,
        task_description: str,
        execution_result: ExecutionResult
    ) -> Optional[str]:
        """
        Сохранить код как skill
        
        TODO: Интегрировать с SkillManager (TypeScript)
        Сейчас просто логируем
        """
        
        logger.info(
            f"Saving skill - Task: {task_description[:50]}..., "
            f"Code length: {len(code)} chars"
        )
        
        # TODO: Call SkillManager через HTTP API
        # skill_id = await self.skill_manager.save_skill(...)
        
        return f"skill-{uuid.uuid4().hex[:8]}"
    
    def _generate_task_id(self) -> str:
        """Генерировать уникальный task ID"""
        return f"task-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"


# Singleton instance
_orchestrator: Optional[AgentOrchestrator] = None


def get_orchestrator() -> AgentOrchestrator:
    """Получить singleton instance"""
    global _orchestrator
    
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    
    return _orchestrator


async def execute_agent_task(
    task: str,
    agent_id: str = "default_agent",
    timeout: Optional[int] = None
) -> Dict[str, Any]:
    """
    Convenience function для выполнения задачи агента
    
    Usage:
        from agent_orchestrator import execute_agent_task
        
        result = await execute_agent_task(
            task="Получить список справочников в УТ",
            agent_id="architect_agent"
        )
        
        if result['success']:
            print(result['output'])
    """
    orchestrator = get_orchestrator()
    return await orchestrator.execute_agent_task(task, agent_id, timeout)


# Example usage
if __name__ == "__main__":
    async def test_orchestrator():
        print("=" * 60)
        print("Тест Agent Orchestrator")
        print("=" * 60)
        
        orchestrator = AgentOrchestrator()
        
        # Test 1: Simple task
        print("\n📋 Test 1: Simple configuration task")
        
        result = await orchestrator.execute_agent_task(
            task="Получить конфигурацию УТ",
            agent_id="architect_agent"
        )
        
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"Output:\n{result['output']}")
            print(f"Execution time: {result['execution_time_ms']}ms")
            print(f"Memory used: {result['memory_used_mb']}MB")
        else:
            print(f"Error: {result.get('error', 'Unknown')}")
        
        # Test 2: Check PII protection
        print("\n" + "=" * 60)
        print("📋 Test 2: PII Protection")
        
        # Simulate data with PII
        test_data = {
            'name': 'Иванов Иван',
            'inn': '1234567890',
            'phone': '+7 (495) 123-45-67'
        }
        
        tokenized = orchestrator.tokenizer.tokenize(
            test_data,
            fields=['name', 'inn', 'phone']
        )
        
        print(f"Original: {test_data}")
        print(f"Tokenized: {tokenized}")
        
        untokenized = orchestrator.tokenizer.untokenize(tokenized)
        print(f"Untokenized: {untokenized}")
        
        assert untokenized == test_data, "Untokenization failed!"
        
        print("\n✅ All tests passed!")
    
    asyncio.run(test_orchestrator())


