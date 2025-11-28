"""
Code Documentation Generator Service

Сервис для генерации документации кода.
"""

import re
from typing import List

from src.modules.technical_writer.domain.exceptions import \
    CodeDocGenerationError
from src.modules.technical_writer.domain.models import (FunctionDocumentation,
                                                        Parameter)
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class CodeDocGenerator:
    """
    Сервис генерации code documentation

    Features:
    - BSL function documentation
    - Parameter extraction
    - Return type detection
    """

    async def document_function(
        self,
        function_code: str,
        language: str = "bsl"
    ) -> FunctionDocumentation:
        """
        Генерация документации для функции

        Args:
            function_code: Код функции
            language: Язык программирования

        Returns:
            FunctionDocumentation
        """
        try:
