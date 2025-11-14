"""
Technical Writer AI Agent Extended
AI ассистент для технических писателей с полным функционалом
"""

import os
import re
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class APIDocumentationGenerator:
    """Генератор API документации (OpenAPI, Markdown)"""
    
    async def generate_api_docs(
        self,
        code: str,
        module_type: str = "http_service"
    ) -> Dict[str, Any]:
        """
        Генерация API документации
        
        Args:
            code: Код HTTP сервиса (1С) или REST API
            module_type: Тип модуля (http_service, odata, rest_api)
        
        Returns:
            {
                "openapi_spec": {...},
                "markdown_docs": "...",
                "examples": [...],
                "postman_collection": {...}
            }
        """
        logger.info(
            "Generating API documentation",
            extra={"module_type": module_type}
        )
        
        # Extract API endpoints
        endpoints = self._extract_endpoints(code)
        
        # Generate OpenAPI 3.0 spec
        openapi_spec = self._generate_openapi_spec(endpoints)
        
        # Generate Markdown documentation
        markdown_docs = self._generate_markdown_docs(endpoints)
        
        # Generate examples
        examples = self._generate_examples(endpoints)
        
        # Generate Postman collection
        postman_collection = self._generate_postman_collection(endpoints)
        
        return {
            "module_type": module_type,
            "openapi_spec": openapi_spec,
            "markdown_docs": markdown_docs,
            "examples": examples,
            "postman_collection": postman_collection,
            "endpoints_count": len(endpoints),
            "generated_at": datetime.now().isoformat(),
            "openapi": openapi_spec,
            "documentation": markdown_docs,
        }
    
    def _extract_endpoints(self, code: str) -> List[Dict]:
        """Извлечение API endpoints из кода"""
        endpoints = []
        
        # Patterns for 1C HTTP Service
        # Функция ПолучитьДанные(Запрос)
        function_pattern = r'Функция\s+(\w+)\s*\((.*?)\)'
        
        matches = re.finditer(function_pattern, code, re.IGNORECASE)
        
        for match in matches:
            function_name = match.group(1)
            params = match.group(2)
            
            # Try to determine HTTP method and path
            http_method = "GET"
            if any(kw in function_name.lower() for kw in ["создать", "добавить", "create", "add"]):
                http_method = "POST"
            elif any(kw in function_name.lower() for kw in ["обновить", "изменить", "update"]):
                http_method = "PUT"
            elif any(kw in function_name.lower() for kw in ["удалить", "delete"]):
                http_method = "DELETE"
            
            path = f"/api/{function_name.lower()}"
            
            endpoints.append({
                "method": http_method,
                "path": path,
                "function_name": function_name,
                "parameters": self._parse_parameters(params),
                "description": f"Endpoint for {function_name}"
            })
        
        return endpoints
    
    def _parse_parameters(self, params_str: str) -> List[Dict]:
        """Парсинг параметров"""
        params = []
        
        if not params_str.strip():
            return params
        
        for param in params_str.split(','):
            param = param.strip()
            if param:
                # Parse parameter name and type
                param_parts = param.split('=')
                param_name = param_parts[0].strip()
                
                # Detect type from name
                param_type = "string"
                if "Число" in param_name or "ID" in param_name:
                    param_type = "integer"
                elif "Дата" in param_name or "Время" in param_name:
                    param_type = "string"  # ISO 8601
                elif "Булево" in param_name or "Флаг" in param_name:
                    param_type = "boolean"
                
                params.append({
                    "name": param_name,
                    "type": param_type,
                    "required": "=" not in param,
                    "description": f"Parameter {param_name}"
                })
        
        return params
    
    def _generate_openapi_spec(self, endpoints: List[Dict]) -> Dict:
        """Генерация OpenAPI 3.0 specification"""
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "1C API",
                "version": "1.0.0",
                "description": "Auto-generated API documentation"
            },
            "servers": [
                {
                    "url": "https://api.example.com",
                    "description": "Production server"
                }
            ],
            "paths": {}
        }
        
        for endpoint in endpoints:
            path = endpoint["path"]
            method = endpoint["method"].lower()
            
            if path not in spec["paths"]:
                spec["paths"][path] = {}
            
            # Build operation
            operation = {
                "summary": endpoint["description"],
                "operationId": endpoint["function_name"],
                "parameters": [],
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object"
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "Bad request"
                    },
                    "500": {
                        "description": "Internal server error"
                    }
                }
            }
            
            # Add parameters
            for param in endpoint["parameters"]:
                operation["parameters"].append({
                    "name": param["name"],
                    "in": "query" if method == "get" else "body",
                    "required": param["required"],
                    "schema": {
                        "type": param["type"]
                    },
                    "description": param["description"]
                })
            
            spec["paths"][path][method] = operation
        
        return spec
    
    def _generate_markdown_docs(self, endpoints: List[Dict]) -> str:
        """Генерация Markdown документации"""
        md = "# API Documentation\n\n"
        md += "Auto-generated documentation for the API.\n\n"
        md += "## Endpoints\n\n"
        
        for endpoint in endpoints:
            md += f"### `{endpoint['method']} {endpoint['path']}`\n\n"
            md += f"{endpoint['description']}\n\n"
            
            if endpoint["parameters"]:
                md += "**Parameters:**\n\n"
                md += "| Name | Type | Required | Description |\n"
                md += "|------|------|----------|-------------|\n"
                for param in endpoint["parameters"]:
                    required = "Yes" if param["required"] else "No"
                    md += f"| {param['name']} | {param['type']} | {required} | {param['description']} |\n"
                md += "\n"
            
            md += "**Response:**\n\n"
            md += "```json\n"
            md += "{\n"
            md += '  "status": "success",\n'
            md += '  "data": {}\n'
            md += "}\n"
            md += "```\n\n"
            md += "---\n\n"
        
        return md
    
    def _generate_examples(self, endpoints: List[Dict]) -> List[Dict]:
        """Генерация примеров использования"""
        examples = []
        
        for endpoint in endpoints:
            # cURL example
            curl = f"curl -X {endpoint['method']} '{endpoint['path']}'"
            if endpoint["parameters"]:
                params = "&".join([f"{p['name']}=value" for p in endpoint["parameters"]])
                curl += f"?{params}"
            
            examples.append({
                "endpoint": f"{endpoint['method']} {endpoint['path']}",
                "curl": curl,
                "request": {
                    "method": endpoint["method"],
                    "url": endpoint["path"],
                    "parameters": {p["name"]: "example_value" for p in endpoint["parameters"]}
                },
                "response": {
                    "status": 200,
                    "body": {
                        "status": "success",
                        "data": {}
                    }
                }
            })
        
        return examples
    
    def _generate_postman_collection(self, endpoints: List[Dict]) -> Dict:
        """Генерация Postman collection"""
        collection = {
            "info": {
                "name": "1C API Collection",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": []
        }
        
        for endpoint in endpoints:
            item = {
                "name": endpoint["function_name"],
                "request": {
                    "method": endpoint["method"],
                    "url": {
                        "raw": f"{{{{base_url}}}}{endpoint['path']}",
                        "host": ["{{base_url}}"],
                        "path": endpoint["path"].strip("/").split("/")
                    }
                },
                "response": []
            }
            
            collection["item"].append(item)
        
        return collection


class UserGuideGenerator:
    """Генератор руководств пользователя"""
    
    async def generate_user_guide(
        self,
        feature: str,
        target_audience: str = "end_user"
    ) -> Dict[str, Any]:
        """
        Генерация user guide
        
        Args:
            feature: Название функции/возможности
            target_audience: Целевая аудитория (end_user, developer, admin)
        
        Returns:
            {
                "guide_markdown": "...",
                "sections": [...],
                "faq": [...]
            }
        """
        logger.info(
            "Generating user guide",
            extra={"feature": feature}
        )
        
        # Generate sections based on audience
        sections = self._generate_sections(feature, target_audience)
        
        # Generate FAQ
        faq = self._generate_faq(feature)
        
        # Assemble markdown guide
        guide_markdown = self._assemble_guide(feature, sections, faq, target_audience)
        
        return {
            "feature": feature,
            "target_audience": target_audience,
            "guide_markdown": guide_markdown,
            "sections": sections,
            "faq": faq,
            "generated_at": datetime.now().isoformat()
        }
    
    def _generate_sections(self, feature: str, audience: str) -> List[Dict]:
        """Генерация разделов руководства"""
        sections = [
            {
                "title": "Обзор",
                "content": f"Функция '{feature}' предназначена для..."
            },
            {
                "title": "Начало работы",
                "content": "Для начала работы выполните следующие шаги:\n1. ...\n2. ...\n3. ..."
            }
        ]
        
        if audience == "end_user":
            sections.extend([
                {
                    "title": "Основные операции",
                    "content": "### Создание нового элемента\n...\n\n### Редактирование\n..."
                },
                {
                    "title": "Часто используемые сценарии",
                    "content": "..."
                }
            ])
        elif audience == "developer":
            sections.extend([
                {
                    "title": "API Reference",
                    "content": "..."
                },
                {
                    "title": "Code Examples",
                    "content": "```bsl\n// Example code\n```"
                }
            ])
        elif audience == "admin":
            sections.extend([
                {
                    "title": "Конфигурация",
                    "content": "..."
                },
                {
                    "title": "Мониторинг и обслуживание",
                    "content": "..."
                }
            ])
        
        return sections
    
    def _generate_faq(self, feature: str) -> List[Dict]:
        """Генерация FAQ"""
        return [
            {
                "question": f"Как использовать {feature}?",
                "answer": "Для использования функции выполните следующие шаги..."
            },
            {
                "question": "Что делать если возникла ошибка?",
                "answer": "Проверьте логи и убедитесь что..."
            },
            {
                "question": "Как настроить параметры?",
                "answer": "Параметры настраиваются через..."
            }
        ]
    
    def _assemble_guide(
        self,
        feature: str,
        sections: List[Dict],
        faq: List[Dict],
        audience: str
    ) -> str:
        """Сборка полного руководства"""
        guide = f"# Руководство: {feature}\n\n"
        guide += f"**Аудитория:** {audience}\n\n"
        guide += f"**Дата:** {datetime.now().strftime('%Y-%m-%d')}\n\n"
        guide += "---\n\n"
        
        # Sections
        for section in sections:
            guide += f"## {section['title']}\n\n"
            guide += f"{section['content']}\n\n"
        
        # FAQ
        guide += "## Часто задаваемые вопросы\n\n"
        for item in faq:
            guide += f"### {item['question']}\n\n"
            guide += f"{item['answer']}\n\n"
        
        return guide


class ReleaseNotesGenerator:
    """Генератор release notes"""
    
    async def generate_release_notes(
        self,
        git_commits: List[Dict],
        version: str
    ) -> str:
        """
        Генерация release notes
        
        Args:
            git_commits: [
                {
                    "hash": "abc123",
                    "message": "feat: add new feature",
                    "author": "John Doe",
                    "date": "2025-11-01"
                }
            ]
            version: "v1.2.0"
        
        Returns:
            Markdown release notes
        """
        logger.info(
            "Generating release notes",
            extra={"version": version}
        )
        
        # Parse commits using Conventional Commits
        features = []
        fixes = []
        breaking = []
        other = []
        
        for commit in git_commits:
            msg = commit.get("message", "")
            
            if msg.startswith("feat:") or msg.startswith("feature:"):
                features.append(msg.replace("feat:", "").replace("feature:", "").strip())
            elif msg.startswith("fix:"):
                fixes.append(msg.replace("fix:", "").strip())
            elif msg.startswith("BREAKING CHANGE:") or "!" in msg:
                breaking.append(msg)
            else:
                other.append(msg)
        
        # Generate release notes
        notes = f"# Release Notes - {version}\n\n"
        notes += f"**Release Date:** {datetime.now().strftime('%Y-%m-%d')}\n\n"
        
        if breaking:
            notes += "## ⚠️ BREAKING CHANGES\n\n"
            for item in breaking:
                notes += f"- {item}\n"
            notes += "\n"
        
        if features:
            notes += "## ✨ New Features\n\n"
            for item in features:
                notes += f"- {item}\n"
            notes += "\n"
        
        if fixes:
            notes += "## 🐛 Bug Fixes\n\n"
            for item in fixes:
                notes += f"- {item}\n"
            notes += "\n"
        
        if other:
            notes += "## 📝 Other Changes\n\n"
            for item in other[:10]:  # Limit
                notes += f"- {item}\n"
            notes += "\n"
        
        # Migration guide (if breaking changes)
        if breaking:
            notes += "## 🔄 Migration Guide\n\n"
            notes += "To migrate from the previous version:\n\n"
            notes += "1. Review breaking changes above\n"
            notes += "2. Update your code accordingly\n"
            notes += "3. Test thoroughly before deploying\n\n"
        
        notes += "---\n\n"
        notes += "For more details, see the [full changelog](CHANGELOG.md).\n"
        
        return notes


class CodeDocumentationGenerator:
    """Генератор документации для кода"""
    
    async def document_function(
        self,
        function_code: str,
        language: str = "bsl"
    ) -> str:
        """
        Генерация документации для функции
        
        Args:
            function_code: Код функции
            language: Язык программирования (bsl, python, js)
        
        Returns:
            Документированный код
        """
        logger.info("Generating function documentation")
        
        if language == "bsl":
            return self._document_bsl_function(function_code)
        else:
            return "// Documentation generation for this language is not yet implemented"
    
    def _document_bsl_function(self, code: str) -> str:
        """Документирование BSL функции"""
        # Extract function signature
        func_match = re.search(r'Функция\s+(\w+)\s*\((.*?)\)', code, re.IGNORECASE | re.DOTALL)
        
        if not func_match:
            return code
        
        func_name = func_match.group(1)
        params_str = func_match.group(2)
        
        # Parse parameters
        params = []
        if params_str.strip():
            for param in params_str.split(','):
                param = param.strip()
                if param:
                    param_name = param.split('=')[0].strip()
                    params.append(param_name)
        
        # Detect return type
        return_type = "Произвольный"
        if re.search(r'Возврат\s+\d+', code):
            return_type = "Число"
        elif re.search(r'Возврат\s+"', code):
            return_type = "Строка"
        elif re.search(r'Возврат\s+(Истина|Ложь)', code, re.IGNORECASE):
            return_type = "Булево"
        
        # Generate documentation
        doc = f"""// Функция выполняет {func_name.lower()}
//
// Параметры:
"""
        
        for param in params:
            doc += f"//   {param} - Тип - Описание параметра {param}\n"
        
        doc += f"""//
// Возвращаемое значение:
//   {return_type} - Результат выполнения
//
// Пример:
//   Результат = {func_name}({', '.join(params)});
//
"""
        
        # Insert documentation before function
        documented_code = re.sub(
            r'(Функция\s+' + func_name + r')',
            doc + r'\1',
            code,
            count=1
        )
        
        return documented_code


class TechnicalWriterAgentExtended:
    """
    Расширенный Technical Writer AI ассистент
    
    Возможности:
    - API Documentation Generation (OpenAPI, Markdown, Postman)
    - User Guide Generation
    - Release Notes Generation
    - Code Documentation Generation
    """
    
    def __init__(self):
        self.api_doc_generator = APIDocumentationGenerator()
        self.guide_generator = UserGuideGenerator()
        self.release_notes_generator = ReleaseNotesGenerator()
        self.code_doc_generator = CodeDocumentationGenerator()
        
        logger.info("Technical Writer Agent Extended initialized")
    
    async def generate_api_docs(
        self,
        code: str,
        module_type: str = "http_service"
    ) -> Dict[str, Any]:
        """Генерация API документации"""
        return await self.api_doc_generator.generate_api_docs(code, module_type)
    
    async def generate_user_guide(
        self,
        feature: str,
        audience: str = "end_user"
    ) -> Dict[str, Any]:
        """Генерация user guide"""
        return await self.guide_generator.generate_user_guide(feature, audience)
    
    async def generate_release_notes(
        self,
        commits: List[Dict],
        version: str
    ) -> str:
        """Генерация release notes"""
        return await self.release_notes_generator.generate_release_notes(commits, version)
    
    async def document_code(
        self,
        code: str,
        language: str = "bsl"
    ) -> str:
        """Документирование кода"""
        return await self.code_doc_generator.document_function(code, language)


