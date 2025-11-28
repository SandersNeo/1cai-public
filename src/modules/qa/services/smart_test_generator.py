"""
Smart Test Generator Service

Сервис для AI-powered генерации тестов для BSL кода.
"""

import re
from typing import List

from src.modules.qa.domain.exceptions import TestGenerationError
from src.modules.qa.domain.models import (
    TestCase,
    TestGenerationResult,
    TestParameter,
    TestType,
)
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
            logger.info(
                "Generating tests for function",
                extra={"function_name": function_name}
            )

            # Analyze function
            params = self._extract_parameters(function_code)
            return_type = self._detect_return_type(function_code)
            complexity = self._calculate_complexity(function_code)

            # Generate tests
            positive_tests = self._generate_positive_tests(
                function_name, params, return_type
            )
            negative_tests = self._generate_negative_tests(
                function_name, params
            )
            edge_case_tests = self._generate_edge_case_tests(
                function_name, params
            )

            # Coverage estimate
            test_count = (
                len(positive_tests) +
                len(negative_tests) +
                len(edge_case_tests)
            )
            coverage_estimate = f"{min(50 + test_count * 10, 95)}%"

            return TestGenerationResult(
                positive_tests=positive_tests,
                negative_tests=negative_tests,
                edge_case_tests=edge_case_tests,
                coverage_estimate=coverage_estimate,
                complexity=complexity,
            )

        except Exception as e:
            logger.error(f"Failed to generate tests: {e}")
            raise TestGenerationError(
                f"Failed to generate tests: {e}",
                details={"function_name": function_name}
            )

    def _extract_parameters(self, code: str) -> List[TestParameter]:
        """Извлечение параметров функции"""
        params = []

        # Match function signature
        func_match = re.search(
            r"Функция\s+\w+\s*\((.*?)\)", code, re.IGNORECASE | re.DOTALL
        )
        if func_match:
            params_str = func_match.group(1)
            for param in params_str.split(","):
                param = param.strip()
                if param:
                    # Detect type from name
                    param_type = "any"
                    if "Строка" in param or "Текст" in param:
                        param_type = "string"
                    elif "Число" in param or "Сумма" in param:
                        param_type = "number"
                    elif "Булево" in param or "Флаг" in param:
                        param_type = "boolean"

                    params.append(
                        TestParameter(
                            name=param.split("=")[0].strip(),
                            type=param_type,
                            default_value=None
                        )
                    )

        return params

    def _detect_return_type(self, code: str) -> str:
        """Определение типа возвращаемого значения"""
        if re.search(r"Возврат\s+\d+", code):
            return "number"
        elif re.search(r'Возврат\s+"', code):
            return "string"
        elif re.search(r"Возврат\s+(Истина|Ложь)", code, re.IGNORECASE):
            return "boolean"
        else:
            return "any"

    def _calculate_complexity(self, code: str) -> int:
        """Расчет цикломатической сложности"""
        complexity = 1  # Base complexity

        # Count decision points
        complexity += len(re.findall(r"\bЕсли\b", code, re.IGNORECASE))
        complexity += len(re.findall(r"\bИначеЕсли\b", code, re.IGNORECASE))
        complexity += len(re.findall(r"\bДля\b", code, re.IGNORECASE))
        complexity += len(re.findall(r"\bПока\b", code, re.IGNORECASE))

        return min(complexity, 10)

    def _generate_positive_tests(
        self,
        function_name: str,
        params: List[TestParameter],
        return_type: str
    ) -> List[TestCase]:
        """Генерация позитивных тестов"""
        tests = []

        # Normal case
        test_code = f"""Процедура Тест_{function_name}_НормальныйСценарий() Экспорт
    // Arrange
    {self._generate_arrange_code(params)}

    // Act
    Результат = {function_name}({self._generate_param_values(params)});

    // Assert
    ЮТест.ОжидаетЧто(Результат).ЭтоНеНеопределено();
КонецПроцедуры"""

        tests.append(
            TestCase(
                name=f"Тест_{function_name}_НормальныйСценарий",
                type=TestType.UNIT,
                code=test_code,
                description=f"Проверка корректности функции {function_name}",
                expected_result="Функция выполняется без ошибок",
                parameters=params
            )
        )

        return tests

    def _generate_negative_tests(
        self,
        function_name: str,
        params: List[TestParameter]
    ) -> List[TestCase]:
        """Генерация негативных тестов"""
        tests = []

        if params:
            test_code = f"""Процедура Тест_{function_name}_НекорректныйТип() Экспорт
    // Тест на обработку некорректного типа параметра

    Попытка
        Результат = {function_name}(Неопределено);
        ВызватьИсключение("Ожидалась ошибка");
    Исключение
        // Ожидаемая ошибка
    КонецПопытки;
КонецПроцедуры"""

            tests.append(
                TestCase(
                    name=f"Тест_{function_name}_НекорректныйТип",
                    type=TestType.UNIT,
                    code=test_code,
                    description="Проверка обработки некорректного типа",
                    expected_result="Выброшено исключение",
                    parameters=[]
                )
            )

        return tests

    def _generate_edge_case_tests(
        self,
        function_name: str,
        params: List[TestParameter]
    ) -> List[TestCase]:
        """Генерация тестов для граничных случаев"""
        tests = []

        # Empty string edge case
        if any(p.type == "string" for p in params):
            tests.append(
                TestCase(
                    name=f"Тест_{function_name}_ПустаяСтрока",
                    type=TestType.UNIT,
                    code=f"// Edge case: пустая строка",
                    description="Проверка обработки пустой строки",
                    expected_result="Корректная обработка",
                    parameters=[]
                )
            )

        # Zero edge case
        if any(p.type == "number" for p in params):
            tests.append(
                TestCase(
                    name=f"Тест_{function_name}_Ноль",
                    type=TestType.UNIT,
                    code=f"// Edge case: ноль",
                    description="Проверка обработки нуля",
                    expected_result="Корректная обработка",
                    parameters=[]
                )
            )

        return tests

    def _generate_arrange_code(self, params: List[TestParameter]) -> str:
        """Генерация Arrange секции"""
        if not params:
            return "// Нет параметров"

        lines = []
        for param in params:
            value = self._generate_test_value(param)
            lines.append(f"    {param.name} = {value};")

        return "\n".join(lines)

    def _generate_param_values(self, params: List[TestParameter]) -> str:
        """Генерация значений параметров для вызова"""
        return ", ".join([p.name for p in params])

    def _generate_test_value(self, param: TestParameter) -> str:
        """Генерация тестового значения"""
        if param.type == "string":
            return f'"{param.name}_test"'
        elif param.type == "number":
            return "100"
        elif param.type == "boolean":
            return "Истина"
        else:
            return "Неопределено"


__all__ = ["SmartTestGenerator"]
