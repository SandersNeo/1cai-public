"""
Code Documentation Generator Service

Сервис для генерации документации кода.
"""

import re
from typing import List

from src.modules.technical_writer.domain.exceptions import CodeDocGenerationError
from src.modules.technical_writer.domain.models import FunctionDocumentation, Parameter
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
            logger.info(
                "Generating function documentation",
                extra={"language": language}
            )

            if language == "bsl":
                return await self._document_bsl_function(function_code)
            else:
                raise CodeDocGenerationError(
                    f"Language {language} not supported",
                    details={"language": language}
                )

        except Exception as e:
            logger.error("Failed to document function: %s", e)
            raise CodeDocGenerationError(
                f"Failed to document function: {e}",
                details={"language": language}
            )

    async def _document_bsl_function(
        self,
        code: str
    ) -> FunctionDocumentation:
        """Документирование BSL функции"""
        # Extract function signature
        func_match = re.search(
            r"Функция\s+(\w+)\s*\((.*?)\)",
            code,
            re.IGNORECASE | re.DOTALL
        )

        if not func_match:
            raise CodeDocGenerationError(
                "Function signature not found",
                details={}
            )

        func_name = func_match.group(1)
        params_str = func_match.group(2)

        # Parse parameters
        params = self._parse_parameters(params_str)

        # Detect return type
        return_type = self._detect_return_type(code)

        # Generate documentation
        doc = self._generate_doc_comment(func_name, params, return_type)

        # Insert documentation
        documented_code = re.sub(
            r"(Функция\s+" + func_name + r")",
            doc + r"\1",
            code,
            count=1
        )

        return FunctionDocumentation(
            function_name=func_name,
            parameters=params,
            return_type=return_type,
            description=f"Функция выполняет {func_name.lower()}",
            examples=[f"Результат = {func_name}();"],
            documented_code=documented_code
        )

    def _parse_parameters(self, params_str: str) -> List[Parameter]:
        """Парсинг параметров"""
        params = []

        if not params_str.strip():
            return params

        for param in params_str.split(","):
            param = param.strip()
            if param:
                param_name = param.split("=")[0].strip()
                params.append(
                    Parameter(
                        name=param_name,
                        type="Произвольный",
                        description=f"Описание параметра {param_name}"
                    )
                )

        return params

    def _detect_return_type(self, code: str) -> str:
        """Детекция типа возвращаемого значения"""
        if re.search(r"Возврат\s+\d+", code):
            return "Число"
        elif re.search(r'Возврат\s+"', code):
            return "Строка"
        elif re.search(r"Возврат\s+(Истина|Ложь)", code, re.IGNORECASE):
            return "Булево"
        else:
            return "Произвольный"

    def _generate_doc_comment(
        self,
        func_name: str,
        params: List[Parameter],
        return_type: str
    ) -> str:
        """Генерация doc comment"""
        doc = f"// Функция выполняет {func_name.lower()}\n"
        doc += "//\n"
        doc += "// Параметры:\n"

        for param in params:
            doc += f"//   {param.name} - {param.type} - {param.description}\n"

        doc += "//\n"
        doc += "// Возвращаемое значение:\n"
        doc += f"//   {return_type} - Результат выполнения\n"
        doc += "//\n"

        return doc


__all__ = ["CodeDocGenerator"]
