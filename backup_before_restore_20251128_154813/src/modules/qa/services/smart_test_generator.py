"""
Smart Test Generator Service

Сервис для AI-powered генерации тестов для BSL кода.
"""

import re
from typing import Any, Dict, List

from src.modules.qa.domain.exceptions import TestGenerationError
from src.modules.qa.domain.models import (TestCase, TestGenerationResult,
                                          TestParameter, TestType)
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class SmartTestGenerator:
    """
    Сервис генерации тестов

    Features:
    - AI test generation для BSL функций
    - YAxUnit test generation
    - Vanessa BDD scenario generation
    - Edge case detection
    - Parameter extraction
    """

    def __init__(self, test_templates_repository=None):
        """
        Args:
            test_templates_repository: Repository для шаблонов тестов
                                      (опционально, для dependency injection)
        """
        if test_templates_repository is None:
            from src.modules.qa.repositories import TestTemplatesRepository
            test_templates_repository = TestTemplatesRepository()

        self.test_templates_repository = test_templates_repository
        self.test_templates = (
            self.test_templates_repository.get_test_templates()
        )

    async def generate_tests_for_function(
        self,
        function_code: str,
        function_name: str,
        module_type: str = "common_module"
    ) -> TestGenerationResult:
        """
        AI генерация тестов для функции

        Args:
            function_code: Код функции BSL
            function_name: Название функции
            module_type: Тип модуля (common_module, server, client)

        Returns:
            TestGenerationResult с generated tests
        """
        try:
