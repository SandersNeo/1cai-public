"""
API Documentation Generator Service

Сервис для генерации API документации.
"""

import re
from typing import Dict, List

from src.modules.technical_writer.domain.exceptions import \
    APIDocGenerationError
from src.modules.technical_writer.domain.models import (APIDocumentation,
                                                        APIEndpoint,
                                                        APIExample,
                                                        APIParameter,
                                                        HTTPMethod)
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
            from src.modules.technical_writer.repositories import \
                TemplatesRepository
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
