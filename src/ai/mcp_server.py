"""
MCP Server for IDE Integration (Cursor, VSCode)
Версия: 2.1.0

Улучшения:
- Structured logging
- Улучшена обработка ошибок
- Input validation

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
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

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
        
        # Input validation
        if not tool_name or not isinstance(tool_name, str):
            logger.warning(
                f"Invalid tool_name: {tool_name}",
                extra={"tool_name": tool_name, "tool_name_type": type(tool_name).__name__}
            )
            return JSONResponse(
                status_code=400,
                content={"error": "Tool name is required and must be a string"}
            )
        
        logger.info(
            f"MCP tool called: {tool_name}",
            extra={
                "tool_name": tool_name,
                "arguments_keys": list(arguments.keys()) if isinstance(arguments, dict) else []
            }
        )
        
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
            logger.warning(
                f"Tool not found: {tool_name}",
                extra={"tool_name": tool_name}
            )
            return JSONResponse(
                status_code=404,
                content={"error": f"Tool not found: {tool_name}"}
            )
        
        logger.debug(
            f"MCP tool executed successfully: {tool_name}",
            extra={"tool_name": tool_name}
        )
        
        return {"result": result}
        
    except Exception as e:
        logger.error(
            f"Tool execution error: {e}",
            extra={
                "tool_name": tool_name if 'tool_name' in locals() else None,
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


# Tool handlers
async def handle_search_metadata(args: Dict) -> Dict:
    """Handle metadata search with input validation and error handling"""
    try:
        query = args.get("query")
        
        # Input validation
        if not query or not isinstance(query, str):
            logger.warning(
                "Invalid query in handle_search_metadata",
                extra={"query_type": type(query).__name__ if query else None}
            )
            return {"error": "Query is required and must be a non-empty string"}
        
        # Validate query length
        max_query_length = 5000
        if len(query) > max_query_length:
            logger.warning(
                "Query too long in handle_search_metadata",
                extra={"query_length": len(query), "max_length": max_query_length}
            )
            return {"error": f"Query too long. Maximum length: {max_query_length} characters"}
        
        logger.debug(
            "Processing metadata search",
            extra={"query_length": len(query)}
        )
        
        response = await orchestrator.process_query(
            query,
            context={"type": "metadata_search", **args}
        )
        
        return response
    except Exception as e:
        logger.error(
            f"Error in handle_search_metadata: {e}",
            extra={"error_type": type(e).__name__},
            exc_info=True
        )
        return {"error": f"Failed to process metadata search: {str(e)}"}


async def handle_search_code(args: Dict) -> Dict:
    """Handle semantic code search with input validation and error handling"""
    try:
        query = args.get("query")
        
        # Input validation
        if not query or not isinstance(query, str):
            logger.warning(
                "Invalid query in handle_search_code",
                extra={"query_type": type(query).__name__ if query else None}
            )
            return {"error": "Query is required and must be a non-empty string"}
        
        # Validate query length
        max_query_length = 5000
        if len(query) > max_query_length:
            logger.warning(
                "Query too long in handle_search_code",
                extra={"query_length": len(query), "max_length": max_query_length}
            )
            return {"error": f"Query too long. Maximum length: {max_query_length} characters"}
        
        logger.debug(
            "Processing semantic code search",
            extra={"query_length": len(query)}
        )
        
        response = await orchestrator.process_query(
            query,
            context={"type": "semantic_search", **args}
        )
        
        return response
    except Exception as e:
        logger.error(
            f"Error in handle_search_code: {e}",
            extra={"error_type": type(e).__name__},
            exc_info=True
        )
        return {"error": f"Failed to process semantic search: {str(e)}"}


async def handle_generate_code(args: Dict) -> Dict:
    """Handle code generation with input validation and error handling"""
    try:
        description = args.get("description")
        
        # Input validation
        if not description or not isinstance(description, str):
            logger.warning(
                "Invalid description in handle_generate_code",
                extra={"description_type": type(description).__name__ if description else None}
            )
            return {"error": "Description is required and must be a non-empty string"}
        
        # Validate description length
        max_description_length = 5000
        if len(description) > max_description_length:
            logger.warning(
                "Description too long in handle_generate_code",
                extra={"description_length": len(description), "max_length": max_description_length}
            )
            return {"error": f"Description too long. Maximum length: {max_description_length} characters"}
        
        logger.debug(
            "Processing code generation",
            extra={"description_length": len(description)}
        )
        
        response = await orchestrator.process_query(
            f"Создай функцию: {description}",
            context={"type": "code_generation", **args}
        )
        
        return response
    except Exception as e:
        logger.error(
            f"Error in handle_generate_code: {e}",
            extra={"error_type": type(e).__name__},
            exc_info=True
        )
        return {"error": f"Failed to generate code: {str(e)}"}


async def handle_analyze_dependencies(args: Dict) -> Dict:
    """Handle dependency analysis with input validation and error handling"""
    try:
        module = args.get("module_name")
        function = args.get("function_name")
        
        # Input validation
        if not module or not isinstance(module, str):
            logger.warning(
                "Invalid module_name in handle_analyze_dependencies",
                extra={"module_type": type(module).__name__ if module else None}
            )
            return {"error": "module_name is required and must be a non-empty string"}
        
        if not function or not isinstance(function, str):
            logger.warning(
                "Invalid function_name in handle_analyze_dependencies",
                extra={"function_type": type(function).__name__ if function else None}
            )
            return {"error": "function_name is required and must be a non-empty string"}
        
        logger.debug(
            "Processing dependency analysis",
            extra={"module": module, "function": function}
        )
        
        response = await orchestrator.process_query(
            f"Покажи зависимости функции {function} в модуле {module}",
            context={"type": "dependency_analysis", **args}
        )
        
        return response
    except Exception as e:
        logger.error(
            f"Error in handle_analyze_dependencies: {e}",
            extra={"error_type": type(e).__name__},
            exc_info=True
        )
        return {"error": f"Failed to analyze dependencies: {str(e)}"}


async def call_external_mcp(base_url: str, tool_name: str, args: Dict, auth_token: Optional[str] = None) -> Dict:
    """Invoke an external MCP-compatible server with input validation and error handling."""
    # Input validation
    if not base_url or not isinstance(base_url, str):
        logger.warning(
            "Invalid base_url in call_external_mcp",
            extra={"base_url_type": type(base_url).__name__ if base_url else None}
        )
        return {"error": "base_url is required and must be a non-empty string"}
    
    if not tool_name or not isinstance(tool_name, str):
        logger.warning(
            "Invalid tool_name in call_external_mcp",
            extra={"tool_name_type": type(tool_name).__name__ if tool_name else None}
        )
        return {"error": "tool_name is required and must be a non-empty string"}
    
    try:
        endpoint = base_url.rstrip("/") + "/mcp/tools/call"
        headers = {"Content-Type": "application/json"}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        logger.debug(
            "Calling external MCP",
            extra={"base_url": base_url, "tool_name": tool_name}
        )

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                endpoint,
                json={"name": tool_name, "arguments": args},
                headers=headers,
            )
            response.raise_for_status()
            payload = response.json()
            return payload.get("result", payload)
    except httpx.TimeoutException as e:
        logger.error(
            f"Timeout calling external MCP: {e}",
            extra={"base_url": base_url, "tool_name": tool_name, "error_type": "TimeoutException"},
            exc_info=True
        )
        return {"error": f"Timeout calling external MCP: {str(e)}"}
    except httpx.HTTPStatusError as e:
        logger.error(
            f"HTTP error calling external MCP: {e}",
            extra={
                "base_url": base_url,
                "tool_name": tool_name,
                "status_code": e.response.status_code,
                "error_type": "HTTPStatusError"
            },
            exc_info=True
        )
        return {"error": f"HTTP error calling external MCP: {e.response.status_code}"}
    except httpx.RequestError as e:
        logger.error(
            f"Request error calling external MCP: {e}",
            extra={"base_url": base_url, "tool_name": tool_name, "error_type": "RequestError"},
            exc_info=True
        )
        return {"error": f"Request error calling external MCP: {str(e)}"}
    except Exception as e:
        logger.error(
            f"Unexpected error calling external MCP: {e}",
            extra={"base_url": base_url, "tool_name": tool_name, "error_type": type(e).__name__},
            exc_info=True
        )
        return {"error": f"Unexpected error calling external MCP: {str(e)}"}


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
        logger.error(
            f"External MCP (platform context) call failed: {exc}",
            extra={
                "error_type": type(exc).__name__,
                "service": "platform_context",
                "base_url": base_url
            },
            exc_info=True
        )
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
        logger.error(
            f"External MCP (test runner) call failed: {exc}",
            extra={
                "error_type": type(exc).__name__,
                "service": "test_runner"
            },
            exc_info=True
        )
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







