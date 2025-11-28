"""
API Documentation Generator Service

Сервис для генерации API документации.
"""

import re
from typing import Dict, List

from src.modules.technical_writer.domain.exceptions import APIDocGenerationError
from src.modules.technical_writer.domain.models import (
    APIDocumentation,
    APIEndpoint,
    APIExample,
    APIParameter,
    HTTPMethod,
)
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class APIDocGenerator:
    """
    Сервис генерации API документации

    Features:
    - OpenAPI 3.0 spec generation
    - Markdown docs generation
    - Examples generation
    - Postman collection generation
    """

    def __init__(self, templates_repository=None):
        """
        Args:
            templates_repository: Repository для templates
                                (опционально, для dependency injection)
        """
        if templates_repository is None:
            from src.modules.technical_writer.repositories import TemplatesRepository
            templates_repository = TemplatesRepository()

        self.templates_repository = templates_repository

    async def generate_api_docs(
        self,
        code: str,
        module_type: str = "http_service"
    ) -> APIDocumentation:
        """
        Генерация API документации

        Args:
            code: Код HTTP сервиса (1С) или REST API
            module_type: Тип модуля

        Returns:
            APIDocumentation
        """
        try:
            logger.info(
                "Generating API documentation",
                extra={"module_type": module_type}
            )

            # Extract endpoints
            endpoints = self._extract_endpoints(code)

            # Generate OpenAPI spec
            openapi_spec = self._generate_openapi_spec(endpoints)

            # Generate Markdown docs
            markdown_docs = self._generate_markdown_docs(endpoints)

            # Generate examples
            examples = self._generate_examples(endpoints)

            # Generate Postman collection
            postman_collection = self._generate_postman_collection(
                endpoints
            )

            return APIDocumentation(
                openapi_spec=openapi_spec,
                markdown_docs=markdown_docs,
                examples=examples,
                postman_collection=postman_collection,
                endpoints_count=len(endpoints)
            )

        except Exception as e:
            logger.error("Failed to generate API docs: %s", e)
            raise APIDocGenerationError(
                f"Failed to generate API docs: {e}",
                details={"module_type": module_type}
            )

    def _extract_endpoints(self, code: str) -> List[APIEndpoint]:
        """Извлечение API endpoints"""
        endpoints = []
        pattern = r"Функция\s+(\w+)\s*\((.*?)\)"
        matches = re.finditer(pattern, code, re.IGNORECASE)

        for match in matches:
            function_name = match.group(1)
            params = match.group(2)

            # Determine HTTP method
            http_method = HTTPMethod.GET
            if any(kw in function_name.lower() for kw in ["создать", "add"]):
                http_method = HTTPMethod.POST
            elif any(kw in function_name.lower() for kw in ["обновить"]):
                http_method = HTTPMethod.PUT
            elif any(kw in function_name.lower() for kw in ["удалить"]):
                http_method = HTTPMethod.DELETE

            endpoints.append(
                APIEndpoint(
                    method=http_method,
                    path=f"/api/{function_name.lower()}",
                    function_name=function_name,
                    parameters=self._parse_parameters(params),
                    description=f"Endpoint for {function_name}"
                )
            )

        return endpoints

    def _parse_parameters(self, params_str: str) -> List[APIParameter]:
        """Парсинг параметров"""
        params = []
        if not params_str.strip():
            return params

        for param in params_str.split(","):
            param = param.strip()
            if param:
                param_name = param.split("=")[0].strip()
                params.append(
                    APIParameter(
                        name=param_name,
                        type="string",
                        required="=" not in param,
                        description=f"Parameter {param_name}"
                    )
                )

        return params

    def _generate_openapi_spec(
        self,
        endpoints: List[APIEndpoint]
    ) -> Dict:
        """Генерация OpenAPI 3.0 spec"""
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "1C API",
                "version": "1.0.0",
                "description": "Auto-generated API documentation"
            },
            "paths": {}
        }

        for endpoint in endpoints:
            path = endpoint.path
            method = endpoint.method.value.lower()

            if path not in spec["paths"]:
                spec["paths"][path] = {}

            spec["paths"][path][method] = {
                "summary": endpoint.description,
                "operationId": endpoint.function_name,
                "responses": {
                    "200": {"description": "Successful response"}
                }
            }

        return spec

    def _generate_markdown_docs(
        self,
        endpoints: List[APIEndpoint]
    ) -> str:
        """Генерация Markdown документации"""
        md = "# API Documentation\n\n"
        md += "## Endpoints\n\n"

        for endpoint in endpoints:
            md += f"### `{endpoint.method.value} {endpoint.path}`\n\n"
            md += f"{endpoint.description}\n\n"
            md += "---\n\n"

        return md

    def _generate_examples(
        self,
        endpoints: List[APIEndpoint]
    ) -> List[APIExample]:
        """Генерация примеров"""
        examples = []

        for endpoint in endpoints:
            curl = f"curl -X {endpoint.method.value} '{endpoint.path}'"

            examples.append(
                APIExample(
                    endpoint=f"{endpoint.method.value} {endpoint.path}",
                    curl=curl,
                    request={
                        "method": endpoint.method.value,
                        "url": endpoint.path
                    },
                    response={"status": 200, "body": {}}
                )
            )

        return examples

    def _generate_postman_collection(
        self,
        endpoints: List[APIEndpoint]
    ) -> Dict:
        """Генерация Postman collection"""
        return {
            "info": {"name": "1C API Collection"},
            "item": [
                {
                    "name": e.function_name,
                    "request": {
                        "method": e.method.value,
                        "url": f"{{{{base_url}}}}{e.path}"
                    }
                }
                for e in endpoints
            ]
        }


__all__ = ["APIDocGenerator"]
