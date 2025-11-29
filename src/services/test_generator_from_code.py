# [NEXUS IDENTITY] ID: -1200289240077096987 | DATE: 2025-11-19

"""
Генератор YAxUnit тестов из существующего BSL кода.

Автоматически анализирует код и генерирует тесты с использованием YAxUnit.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional


from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


@dataclass
class FunctionInfo:
    """Информация о функции BSL"""

    name: str
    parameters: List[Dict[str, str]]  # [{"name": "param1", "type": "Число"}]
    return_type: Optional[str] = None
    code: str = ""
    docstring: Optional[str] = None
    complexity: int = 1  # Простая оценка сложности


class CodeToTestGenerator:
    """
    Генератор тестов из BSL кода.
    """

    def __init__(self):
        from src.ai.agents.qa_engineer_agent_extended import QAEngineerAgentExtended
        self.qa_agent = QAEngineerAgentExtended()
        logger.info("CodeToTestGenerator initialized")

    async def generate_from_function(
        self,
        function_code: str,
        function_name: Optional[str] = None,
        test_style: str = "yaxunit",
        include_edge_cases: bool = True,
        include_negative_tests: bool = True,
    ) -> str:
        """
        Генерирует тесты из кода функции.

        Args:
            function_code: Код функции BSL
            function_name: Имя функции (если не указано, извлекается из кода)
            test_style: Стиль тестов (yaxunit, vanilla)
            include_edge_cases: Включать edge cases
            include_negative_tests: Включать негативные тесты

        Returns:
            Код тестов в формате YAxUnit
        """
        logger.info(
            "Generating tests from function code",
            extra={
                "function_name": function_name,
                "test_style": test_style,
                "include_edge_cases": include_edge_cases,
            },
        )

        # 1. Парсинг функции
        func_info = self._parse_function(function_code, function_name)

        # 2. Генерация тестов
        if test_style == "yaxunit":
            tests = await self._generate_yaxunit_tests(
                func_info=func_info,
                include_edge_cases=include_edge_cases,
                include_negative_tests=include_negative_tests,
            )
        else:
            tests = await self._generate_vanilla_tests(
                func_info=func_info,
                include_edge_cases=include_edge_cases,
            )

        return tests

    def _parse_function(
        self,
        code: str,
        function_name: Optional[str] = None,
    ) -> FunctionInfo:
        """
        Парсит BSL функцию и извлекает информацию.

        Args:
            code: Код функции
            function_name: Имя функции (опционально)

        Returns:
            FunctionInfo с информацией о функции
        """
        # Извлечение имени функции
        if not function_name:
            match = re.search(r"Функция\s+(\w+)", code, re.IGNORECASE)
            if match:
                function_name = match.group(1)
            else:
                function_name = "НеизвестнаяФункция"

        # Извлечение параметров
        params_match = re.search(
            r"Функция\s+\w+\s*\((.*?)\)", code, re.IGNORECASE | re.DOTALL
        )
        parameters = []
        if params_match:
            params_str = params_match.group(1).strip()
            if params_str:
                # Парсинг параметров (простой вариант)
                for param in params_str.split(","):
                    param = param.strip()
                    if param:
                        # Попытка определить тип по имени
                        param_type = self._guess_parameter_type(param)
                        parameters.append(
                            {
                                "name": param,
                                "type": param_type,
                            }
                        )

        # Извлечение типа возвращаемого значения
        return_type = None
        return_match = re.search(r"Возврат\s+([^;]+)", code, re.IGNORECASE)
        if return_match:
            return_value = return_match.group(1).strip()
            return_type = self._guess_return_type(return_value)

        # Оценка сложности (простая)
        complexity = self._estimate_complexity(code)

        return FunctionInfo(
            name=function_name,
            parameters=parameters,
            return_type=return_type,
            code=code,
            complexity=complexity,
        )

    def _guess_parameter_type(self, param_name: str) -> str:
        """Угадывает тип параметра по имени."""
        param_lower = param_name.lower()

        if any(
            word in param_lower
            for word in ["сумма", "количество", "число", "count", "amount"]
        ):
            return "Число"
        elif any(
            word in param_lower
            for word in ["строка", "текст", "имя", "string", "text", "name"]
        ):
            return "Строка"
        elif any(word in param_lower for word in ["дата", "date", "время", "time"]):
            return "Дата"
        elif any(
            word in param_lower
            for word in ["список", "массив", "массив", "list", "array"]
        ):
            return "Массив"
        elif any(word in param_lower for word in ["таблица", "table"]):
            return "ТаблицаЗначений"
        else:
            return "Произвольный"

    def _guess_return_type(self, return_value: str) -> Optional[str]:
        """Угадывает тип возвращаемого значения."""
        return_value_lower = return_value.lower()

        if re.match(r"^\d+$", return_value.strip()):
            return "Число"
        elif return_value.strip().startswith('"') or return_value.strip().startswith(
            "'"
        ):
            return "Строка"
        elif "истина" in return_value_lower or "ложь" in return_value_lower:
            return "Булево"
        elif "новый" in return_value_lower:
            if "массив" in return_value_lower:
                return "Массив"
            elif "таблица" in return_value_lower:
                return "ТаблицаЗначений"
            elif "структура" in return_value_lower:
                return "Структура"
        elif "неопределено" in return_value_lower:
            return None

        return "Произвольный"

    def _estimate_complexity(self, code: str) -> int:
        """Оценивает сложность функции (1-10)."""
        complexity = 1

        # Количество условий
        if_count = len(re.findall(r"\bЕсли\b", code, re.IGNORECASE))
        complexity += if_count

        # Количество циклов
        loop_count = len(re.findall(r"\b(Для|Пока|Цикл)\b", code, re.IGNORECASE))
        complexity += loop_count * 2

        # Количество вызовов функций
        func_call_count = len(re.findall(r"\w+\s*\(", code))
        complexity += min(func_call_count // 5, 3)

        return min(complexity, 10)

    async def _generate_yaxunit_tests(
        self,
        func_info: FunctionInfo,
        include_edge_cases: bool = True,
        include_negative_tests: bool = True,
    ) -> str:
        """Генерирует YAxUnit тесты."""
        tests = []

        # 1. Базовый тест (happy path)
        basic_test = self._generate_basic_test(func_info)
        tests.append(basic_test)

        # 2. Edge cases
        if include_edge_cases:
            edge_tests = self._generate_edge_case_tests(func_info)
            tests.extend(edge_tests)

        # 3. Негативные тесты
        if include_negative_tests:
            negative_tests = self._generate_negative_tests(func_info)
            tests.extend(negative_tests)

        # Объединение в файл
        file_header = f"""// Тесты для функции {func_info.name}
// Сгенерировано автоматически из кода
// Формат: YAxUnit

#Область Тесты_{func_info.name}

"""

        file_footer = """
#КонецОбласти
"""

        return file_header + "\n\n".join(tests) + file_footer

    def _generate_basic_test(self, func_info: FunctionInfo) -> str:
        """Генерирует базовый тест."""
        # Генерация Arrange секции
        arrange_lines = []
        for param in func_info.parameters:
            test_value = self._generate_test_value(param["type"], param["name"])
            arrange_lines.append(f"    {param['name']} = {test_value};")

        arrange_code = (
            "\n".join(arrange_lines) if arrange_lines else "    // Нет параметров"
        )

        # Генерация Assert секции
        assert_code = self._generate_assert_code(func_info.return_type, "Результат")

        return f"""// Базовый тест функции {func_info.name}
Процедура Тест_{func_info.name}_Базовый() Экспорт

    // Arrange (подготовка)
{arrange_code}

    // Act (действие)
    Результат = {func_info.name}({', '.join(p['name'] for p in func_info.parameters)});

    // Assert (проверка через YAxUnit)
{assert_code}

КонецПроцедуры
"""

    def _generate_test_value(self, param_type: str, param_name: str) -> str:
        """Генерирует тестовое значение для параметра."""
        if param_type == "Число":
            return "100"
        elif param_type == "Строка":
            return f'"{param_name}_test"'
        elif param_type == "Дата":
            return "ТекущаяДата()"
        elif param_type == "Булево":
            return "Истина"
        elif param_type == "Массив":
            return "Новый Массив"
        elif param_type == "ТаблицаЗначений":
            return "Новый ТаблицаЗначений"
        else:
            return "Неопределено"

    def _generate_edge_case_tests(self, func_info: FunctionInfo) -> List[str]:
        """Генерирует тесты для edge cases."""
        tests = []

        # Edge case: нулевые значения
        if any(p["type"] == "Число" for p in func_info.parameters):
            param_assignments = []
            for p in func_info.parameters:
                if p["type"] == "Число":
                    val = "0"
                else:
                    val = "Неопределено"
                param_assignments.append(f"{p['name']} = {val}")

            tests.append(
                f"""// Edge case: нулевые значения
Процедура Тест_{func_info.name}_НулевыеЗначения() Экспорт

    // Arrange
    {', '.join(param_assignments)};

    // Act
    Результат = {func_info.name}({', '.join(p['name'] for p in func_info.parameters)});

    // Assert
    ЮТест.ОжидаетЧто(Результат, "Результат с нулевыми значениями")
        .ЭтоНеНеопределено();

КонецПроцедуры
"""
            )

        # Edge case: максимальные значения
        if any(p["type"] == "Число" for p in func_info.parameters):
            # Подготовка значения для строки (вынесено из f-string из-за ограничений backslash)
            long_string_val = "A" * 1000
            long_string_expr = f'"{long_string_val}"'

            param_init_list = []
            for p in func_info.parameters:
                if p["type"] == "Число":
                    param_init_list.append(f"{p['name']} = 999999999")
                elif p["type"] == "Строка":
                    param_init_list.append(f"{p['name']} = {long_string_expr}")
                else:
                    param_init_list.append(f"{p['name']} = Неопределено")

            param_inits = ", ".join(param_init_list)

            tests.append(
                f"""// Edge case: максимальные значения
Процедура Тест_{func_info.name}_МаксимальныеЗначения() Экспорт

    // Arrange
    {param_inits};

    // Act
    Результат = {func_info.name}({', '.join(p['name'] for p in func_info.parameters)});

    // Assert
    ЮТест.ОжидаетЧто(Результат, "Результат с максимальными значениями")
        .ЭтоНеНеопределено();

КонецПроцедуры
"""
            )

        return tests

    def _generate_negative_tests(self, func_info: FunctionInfo) -> List[str]:
        """Генерирует негативные тесты."""
        tests = []

        # Негативный тест: неопределенные параметры
        param_assignments = []
        for p in func_info.parameters:
            param_assignments.append(f"{p['name']} = Неопределено")

        tests.append(
            f"""// Негативный тест: неопределенные параметры
Процедура Тест_{func_info.name}_НеопределенныеПараметры() Экспорт

    // Arrange
    {', '.join(param_assignments)};

    // Act & Assert
    Попытка
        Результат = {func_info.name}({', '.join(p['name'] for p in func_info.parameters)});
        ВызватьИсключение("Ожидалась ошибка при неопределенных параметрах");
    Исключение
        ЮТест.ОжидаетЧто(ОписаниеОшибки(), "Описание ошибки")
            .Заполнено();
    КонецПопытки;

КонецПроцедуры
"""
        )

        return tests

    async def _generate_vanilla_tests(
        self,
        func_info: FunctionInfo,
        include_edge_cases: bool = True,
    ) -> str:
        """Генерирует обычные тесты (без YAxUnit)."""
        # Базовая реализация для vanilla тестов
        return f"""// Тесты для функции {func_info.name}
// Сгенерировано автоматически

Процедура Тест_{func_info.name}() Экспорт
    // TODO: Реализовать тест
КонецПроцедуры
"""

    def _generate_assert_code(self, return_type: Optional[str], result_var: str) -> str:
        """Генерирует код проверки результата."""
        if not return_type:
            return (
                f'    ЮТест.ОжидаетЧто({result_var}, "Результат").ЭтоНеНеопределено();'
            )

        return f'    ЮТест.ОжидаетЧто({result_var}, "Результат").ЭтоНеНеопределено();'
