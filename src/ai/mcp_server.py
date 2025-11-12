"""
MCP Server for IDE Integration (Cursor, VSCode)
Model Context Protocol implementation
"""

import json
import logging
import os
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
import asyncio
import httpx

from src.ai.orchestrator import AIOrchestrator
from src.config import settings

logger = logging.getLogger(__name__)

app = FastAPI(title="1C MCP Server")

# Orchestrator
orchestrator = AIOrchestrator()


# MCP Protocol Types
class MCPTool:
    """MCP Tool definition"""
    
    def __init__(self, name: str, description: str, input_schema: Dict):
        self.name = name
        self.description = description
        self.input_schema = input_schema
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema
        }


# Define MCP Tools
BASE_TOOLS = [
    MCPTool(
        name="search_metadata",
        description="Поиск объектов метаданных 1С по структурным свойствам, связям и отношениям. Использует граф метаданных в Neo4j.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Запрос для поиска (например: 'Найди все документы связанные с регистром Продажи')"
                },
                "configuration": {
                    "type": "string",
                    "description": "Фильтр по конфигурации (DO, ERP, ZUP, BUH)",
                    "enum": ["DO", "ERP", "ZUP", "BUH"]
                },
                "object_type": {
                    "type": "string",
                    "description": "Тип объекта (Документ, Справочник, Регистр, и т.д.)"
                }
            },
            "required": ["query"]
        }
    ),
    
    MCPTool(
        name="search_code_semantic",
        description="Семантический поиск процедур и функций по их описаниям и содержанию. Использует векторный поиск в Qdrant.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Описание искомой функциональности"
                },
                "configuration": {
                    "type": "string",
                    "description": "Фильтр по конфигурации"
                },
                "limit": {
                    "type": "integer",
                    "description": "Количество результатов",
                    "default": 10
                }
            },
            "required": ["query"]
        }
    ),
    
    MCPTool(
        name="generate_bsl_code",
        description="Генерация BSL кода на основе описания. Использует Qwen3-Coder для создания функций и процедур.",
        input_schema={
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Описание требуемой функциональности"
                },
                "function_name": {
                    "type": "string",
                    "description": "Имя функции"
                },
                "parameters": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Список параметров"
                },
                "context": {
                    "type": "object",
                    "description": "Дополнительный контекст (модуль, объект)"
                }
            },
            "required": ["description"]
        }
    ),
    
    MCPTool(
        name="analyze_dependencies",
        description="Анализ зависимостей функции или модуля. Строит граф вызовов и показывает все связи.",
        input_schema={
            "type": "object",
            "properties": {
                "module_name": {
                    "type": "string",
                    "description": "Полное имя модуля"
                },
                "function_name": {
                    "type": "string",
                    "description": "Имя функции"
                }
            },
            "required": ["module_name", "function_name"]
        }
    ),
]

TOOLS = BASE_TOOLS.copy()

if os.getenv("ENABLE_MCP_EXTERNAL_TOOLS", "false").lower() == "true":
    TOOLS.extend([
    MCPTool(
        name="bsl_platform_context",
        description="Прокси к внешнему MCP (alkoleft/mcp-bsl-platform-context) для получения платформенного контекста 1С.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Что нужно найти (например, 'Документ Продажи, реквизиты, табличные части')"
                },
                "scope": {
                    "type": "object",
                    "description": "Дополнительные параметры запроса (см. документацию внешнего MCP сервера)"
                }
            },
            "required": ["query"]
        }
    ),

    MCPTool(
        name="bsl_test_runner",
        description="Прокси к внешнему MCP (alkoleft/mcp-onec-test-runner) для запуска BSL/Vanessa тестов.",
        input_schema={
            "type": "object",
            "properties": {
                "workspace": {
                    "type": "string",
                    "description": "Путь к проекту или workspace, который должен запускать тесты"
                },
                "testPlan": {
                    "type": "string",
                    "description": "Опциональный путь к testplan для запуска (см. документацию внешнего runner)"
                },
                "arguments": {
                    "type": "object",
                    "description": "Дополнительные параметры запуска"
                }
            },
            "required": ["workspace"]
        }
    )
    ])


# MCP Endpoints
@app.get("/mcp")
async def mcp_root():
    """MCP server info"""
    return {
        "name": "1C AI Assistant MCP Server",
        "version": "1.0.0",
        "protocol": "mcp/1.0",
        "capabilities": {
            "tools": True,
            "prompts": False,
            "resources": False
        }
    }


@app.get("/mcp/tools")
async def list_tools():
    """List available MCP tools"""
    return {
        "tools": [tool.to_dict() for tool in TOOLS]
    }


@app.post("/mcp/tools/call")
async def call_tool(request: Request):
    """Execute MCP tool"""
    try:
        body = await request.json()
        
        tool_name = body.get("name")
        arguments = body.get("arguments", {})
        
        logger.info(f"MCP tool called: {tool_name}")
        
        # Route to appropriate handler
        if tool_name == "search_metadata":
            result = await handle_search_metadata(arguments)
        
        elif tool_name == "search_code_semantic":
            result = await handle_search_code(arguments)
        
        elif tool_name == "generate_bsl_code":
            result = await handle_generate_code(arguments)
        
        elif tool_name == "analyze_dependencies":
            result = await handle_analyze_dependencies(arguments)

        elif tool_name == "bsl_platform_context":
            result = await handle_bsl_platform_context(arguments)

        elif tool_name == "bsl_test_runner":
            result = await handle_bsl_test_runner(arguments)
        
        else:
            return JSONResponse(
                status_code=404,
                content={"error": f"Tool not found: {tool_name}"}
            )
        
        return {"result": result}
        
    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


# Tool handlers
async def handle_search_metadata(args: Dict) -> Dict:
    """Handle metadata search"""
    query = args.get("query")
    
    response = await orchestrator.process_query(
        query,
        context={"type": "metadata_search", **args}
    )
    
    return response


async def handle_search_code(args: Dict) -> Dict:
    """Handle semantic code search"""
    query = args.get("query")
    
    response = await orchestrator.process_query(
        query,
        context={"type": "semantic_search", **args}
    )
    
    return response


async def handle_generate_code(args: Dict) -> Dict:
    """Handle code generation"""
    description = args.get("description")
    
    response = await orchestrator.process_query(
        f"Создай функцию: {description}",
        context={"type": "code_generation", **args}
    )
    
    return response


async def handle_analyze_dependencies(args: Dict) -> Dict:
    """Handle dependency analysis"""
    module = args.get("module_name")
    function = args.get("function_name")
    
    response = await orchestrator.process_query(
        f"Покажи зависимости функции {function} в модуле {module}",
        context={"type": "dependency_analysis", **args}
    )
    
    return response


async def call_external_mcp(base_url: str, tool_name: str, args: Dict, auth_token: Optional[str] = None) -> Dict:
    """Invoke an external MCP-compatible server and return its result."""
    endpoint = base_url.rstrip("/") + "/mcp/tools/call"
    headers = {"Content-Type": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            endpoint,
            json={"name": tool_name, "arguments": args},
            headers=headers,
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("result", payload)


async def handle_bsl_platform_context(args: Dict) -> Dict:
    """Proxy to external MCP server providing platform context."""
    base_url = settings.mcp_bsl_context_base_url
    if not base_url:
        return {
            "error": "MCP_BSL_CONTEXT_BASE_URL is not configured. "
                     "Install and run alkoleft/mcp-bsl-platform-context, then set the environment variable.",
            "configured": False,
        }

    try:
        return await call_external_mcp(
            base_url=base_url,
            tool_name=settings.mcp_bsl_context_tool_name,
            args=args,
            auth_token=settings.mcp_bsl_context_auth_token,
        )
    except httpx.HTTPError as exc:
        logger.error("External MCP (platform context) call failed: %s", exc)
        return {"error": f"External MCP platform context call failed: {exc}"}


async def handle_bsl_test_runner(args: Dict) -> Dict:
    """Proxy to external MCP test runner."""
    base_url = settings.mcp_bsl_test_runner_base_url
    if not base_url:
        return {
            "error": "MCP_BSL_TEST_RUNNER_BASE_URL is not configured. "
                     "Install and run alkoleft/mcp-onec-test-runner, then set the environment variable.",
            "configured": False,
        }

    try:
        return await call_external_mcp(
            base_url=base_url,
            tool_name=settings.mcp_bsl_test_runner_tool_name,
            args=args,
            auth_token=settings.mcp_bsl_test_runner_auth_token,
        )
    except httpx.HTTPError as exc:
        logger.error("External MCP (test runner) call failed: %s", exc)
        return {"error": f"External MCP test runner call failed: {exc}"}


class MCPServer:
    """
    Легковесная обертка, используемая в интеграционных тестах.
    """

    def __init__(self):
        self._orchestrator = orchestrator

    async def search_metadata(self, query: str, metadata_type: Optional[str] = None) -> Dict[str, Any]:
        return {
            "query": query,
            "type": metadata_type,
            "results": [],
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6001)







