# [NEXUS IDENTITY] ID: 4376615904632233838 | DATE: 2025-11-19

"""
MCP Server for IDE Integration (Cursor, VSCode)
Версия: 2.1.0

Улучшения:
- Structured logging
- Улучшена обработка ошибок
- Input validation

Model Context Protocol implementation
"""

import os
from typing import Any, Dict, Optional

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

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
            "inputSchema": self.input_schema,
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
                    "description": "Запрос для поиска (например: 'Найди все документы связанные с регистром Продажи')",
                },
                "configuration": {
                    "type": "string",
                    "description": "Фильтр по конфигурации (DO, ERP, ZUP, BUH)",
                    "enum": ["DO", "ERP", "ZUP", "BUH"],
                },
                "object_type": {
                    "type": "string",
                    "description": "Тип объекта (Документ, Справочник, Регистр, и т.д.)",
                },
            },
            "required": ["query"],
        },
    ),
    MCPTool(
        name="search_code_semantic",
        description="Семантический поиск процедур и функций по их описаниям и содержанию. Использует векторный поиск в Qdrant.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Описание искомой функциональности",
                },
                "configuration": {
                    "type": "string",
                    "description": "Фильтр по конфигурации",
                },
                "limit": {
                    "type": "integer",
                    "description": "Количество результатов",
                    "default": 10,
                },
            },
            "required": ["query"],
        },
    ),
    MCPTool(
        name="generate_bsl_code",
        description="Генерация BSL кода на основе описания. Использует Qwen3-Coder для создания функций и процедур.",
        input_schema={
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Описание требуемой функциональности",
                },
                "function_name": {"type": "string", "description": "Имя функции"},
                "parameters": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Список параметров",
                },
                "context": {
                    "type": "object",
                    "description": "Дополнительный контекст (модуль, объект)",
                },
            },
            "required": ["description"],
        },
    ),
    MCPTool(
        name="analyze_dependencies",
        description="Анализ зависимостей функции или модуля. Строит граф вызовов и показывает все связи.",
        input_schema={
            "type": "object",
            "properties": {
                "module_name": {"type": "string", "description": "Полное имя модуля"},
                "function_name": {"type": "string", "description": "Имя функции"},
            },
            "required": ["module_name", "function_name"],
        },
    ),
]

TOOLS = BASE_TOOLS.copy()

if os.getenv("ENABLE_MCP_EXTERNAL_TOOLS", "false").lower() == "true":
    TOOLS.extend(
        [
            MCPTool(
                name="bsl_platform_context",
                description="Прокси к внешнему MCP (alkoleft/mcp-bsl-platform-context) для получения платформенного контекста 1С.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Что нужно найти (например, 'Документ Продажи, реквизиты, табличные части')",
                        },
                        "scope": {
                            "type": "object",
                            "description": "Дополнительные параметры запроса (см. документацию внешнего MCP сервера)",
                        },
                    },
                    "required": ["query"],
                },
            ),
            MCPTool(
                name="bsl_test_runner",
                description="Прокси к внешнему MCP (alkoleft/mcp-onec-test-runner) для запуска BSL/Vanessa тестов.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "workspace": {
                            "type": "string",
                            "description": "Путь к проекту или workspace, который должен запускать тесты",
                        },
                        "testPlan": {
                            "type": "string",
                            "description": "Опциональный путь к testplan для запуска (см. документацию внешнего runner)",
                        },
                        "arguments": {
                            "type": "object",
                            "description": "Дополнительные параметры запуска",
                        },
                    },
                    "required": ["workspace"],
                },
            ),
        ]
    )


# MCP Endpoints
@app.get("/mcp")
async def mcp_root():
    """MCP server info"""
    return {
        "name": "1C AI Assistant MCP Server",
        "version": "1.0.0",
        "protocol": "mcp/1.0",
        "capabilities": {"tools": True, "prompts": False, "resources": False},
    }


@app.get("/mcp/tools")
async def list_tools():
    """List available MCP tools"""
    return {"tools": [tool.to_dict() for tool in TOOLS]}


@app.post("/mcp/tools/call")
async def call_tool(request: Request):
    """Execute MCP tool"""
    try:
            f"HTTP error calling external MCP: {e}",
            extra = {
                "base_url": base_url,
                "tool_name": tool_name,
                "status_code": e.response.status_code,
                "error_type": "HTTPStatusError",
            },
            exc_info = True,
        )
        return {"error": f"HTTP error calling external MCP: {e.response.status_code}"}
    except httpx.RequestError as e:
        logger.error(
            f"Request error calling external MCP: {e}",
            extra={
                "base_url": base_url,
                "tool_name": tool_name,
                "error_type": "RequestError",
            },
            exc_info=True,
        )
        return {"error": f"Request error calling external MCP: {str(e)}"}
    except Exception as e:
        logger.error(
            f"Unexpected error calling external MCP: {e}",
            extra={
                "base_url": base_url,
                "tool_name": tool_name,
                "error_type": type(e).__name__,
            },
            exc_info=True,
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