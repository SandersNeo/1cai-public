# [NEXUS IDENTITY] ID: -139712185354762754 | DATE: 2025-11-19

"""
API endpoints для автоматической генерации тестов
Версия: 1.1.0
Refactored: Uses BSLParser for robust parsing
"""

import asyncio
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Any, Dict
from datetime import datetime
from src.services.openai_code_analyzer import get_openai_analyzer
from src.middleware.rate_limiter import limiter
from src.utils.structured_logging import StructuredLogger
from src.ai.agents.code_review.bsl_parser import BSLParser

# Import TypeScript test generation (moved from conditional import)
try:
    from src.api.test_generation_ts import generate_typescript_tests
except ImportError:
    generate_typescript_tests = None

logger = StructuredLogger(__name__).logger
router = APIRouter()


# ==================== МОДЕЛИ ДАННЫХ ====================


class TestGenerationRequest(BaseModel):
    """Запрос на генерацию тестов"""

    code: str = Field(
        ..., max_length=50000, description="Исходный код для тестирования"
    )
    language: Literal["bsl", "typescript", "python"] = Field(
        default="bsl", description="Язык программирования"
    )
    functionName: Optional[str] = Field(
        None, max_length=200, description="Имя конкретной функции для тестирования"
    )
    testType: Literal["unit", "integration", "e2e", "all"] = Field(
        default="unit", description="Тип тестов для генерации"
    )
    includeEdgeCases: bool = Field(
        default=True, description="Включать граничные случаи"
    )
    framework: Optional[str] = Field(
        None, max_length=100, description="Фреймворк для тестирования"
    )


class TestCase(BaseModel):
    """Тестовый случай"""

    id: str = Field(..., max_length=100)
    name: str = Field(..., max_length=200)
    description: str = Field(..., max_length=1000)
    input: dict
    expectedOutput: Any
    type: Literal["unit", "integration", "e2e"]
    category: Literal["positive", "negative", "edge", "boundary"]


class CoverageMetrics(BaseModel):
    """Метрики покрытия"""

    lines: int = Field(..., ge=0, le=100)
    branches: int = Field(..., ge=0, le=100)
    functions: int = Field(..., ge=0, le=100)


class GeneratedTest(BaseModel):
    """Сгенерированный тест"""

    id: str = Field(..., max_length=100)
    functionName: str = Field(..., max_length=200)
    testCases: List[TestCase]
    code: str = Field(..., max_length=50000)
    language: str = Field(..., max_length=50)
    framework: str = Field(..., max_length=100)
    coverage: CoverageMetrics


class TestGenerationResponse(BaseModel):
    """Ответ генерации тестов"""

    tests: List[GeneratedTest]
    summary: dict
    timestamp: datetime = Field(default_factory=datetime.now)
    generationId: str = Field(..., max_length=100)


# ==================== ГЕНЕРАТОР ТЕСТОВ ====================


async def generate_bsl_tests(
    code: str, include_edge_cases: bool = True, timeout: float = 30.0
) -> List[dict]:
    """Генерация тестов для BSL кода с timeout handling"""
    # Input validation
    if not isinstance(code, str) or not code.strip():
        logger.warning(
            "Invalid code in generate_bsl_tests",
            extra={"code_type": type(code).__name__ if code else None},
        )
        return []

    if not isinstance(include_edge_cases, bool):
        logger.warning(
            "Invalid include_edge_cases type in generate_bsl_tests",
            extra={"include_edge_cases_type": type(include_edge_cases).__name__},
        )
        include_edge_cases = True

    if not isinstance(timeout, (int, float)) or timeout <= 0:
        logger.warning(
            "Invalid timeout in generate_bsl_tests",
            extra={"timeout": timeout, "timeout_type": type(timeout).__name__},
        )
        timeout = 30.0

    try:
        return await asyncio.wait_for(
            _generate_bsl_tests_internal(code, include_edge_cases), timeout=timeout
        )
    except asyncio.TimeoutError:
        logger.warning(
            "Timeout in generate_bsl_tests",
            extra={"timeout": timeout, "code_length": len(code)},
        )
        return []
    except Exception as e:
        logger.error(
            "Error in generate_bsl_tests",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "code_length": len(code),
            },
            exc_info=True,
        )
        return []


async def _generate_bsl_tests_internal(
    code: str, include_edge_cases: bool
) -> List[dict]:
    """Internal method for generating BSL tests"""
    tests = []

    # Parsing via BSLParser (Consolidated logic)
    parser = BSLParser()
    try:
        parsed_data = parser.parse_file(code)
        raw_functions = parsed_data.get("functions", [])

        # Adapter to match expected structure
        functions = []
        for f in raw_functions:
            functions.append(
                {
                    "name": f.get("name"),
                    "code": f.get("body", ""),
                    "params": [p["name"] for p in f.get("parameters", [])],
                    "params_detailed": f.get("parameters", []),
                    "exported": f.get("is_export", False),
                    "start_line": f.get("start_line"),
                    "end_line": f.get("end_line"),
                    "comments": "",  # BSLParser doesn't extract comments body yet, can be improved
                }
            )
    except Exception as e:
        logger.error(f"BSL parsing failed: {e}", exc_info=True)
        return []

    for func in functions:
        test_cases = await generate_test_cases(func, include_edge_cases)
        test_code = generate_bsl_test_code(func, test_cases)

        tests.append(
            {
                "id": f"test-{func['name']}-{datetime.now().timestamp()}",
                "functionName": func["name"],
                "testCases": test_cases,
                "code": test_code,
                "language": "bsl",
                "framework": "xUnitFor1C",
                "coverage": {
                    "lines": calculate_coverage(func["code"], test_code),
                    "branches": 0,
                    "functions": 1,
                },
            }
        )

    return tests


async def generate_test_cases(
    func: dict, include_edge_cases: bool, timeout: float = 10.0
) -> List[dict]:
    """Генерация тест-кейсов (с поддержкой AI) с timeout handling"""
    # Input validation
    if not isinstance(func, dict) or "code" not in func or "name" not in func:
        logger.warning(
            "Invalid func in generate_test_cases",
            extra={"func_type": type(func).__name__},
        )
        return []

    if not isinstance(include_edge_cases, bool):
        logger.warning(
            "Invalid include_edge_cases type in generate_test_cases",
            extra={"include_edge_cases_type": type(include_edge_cases).__name__},
        )
        include_edge_cases = True

    if not isinstance(timeout, (int, float)) or timeout <= 0:
        logger.warning(
            "Invalid timeout in generate_test_cases",
            extra={"timeout": timeout, "timeout_type": type(timeout).__name__},
        )
        timeout = 10.0

    test_cases = []

    # Попытка AI генерации тест-кейсов
    ai_test_cases = []
    try:
        openai_analyzer = get_openai_analyzer()
        ai_test_cases = await asyncio.wait_for(
            openai_analyzer.generate_test_cases(
                code=func["code"], function_name=func["name"]
            ),
            timeout=timeout,
        )

        if ai_test_cases:
            logger.info(
                "AI сгенерировано тест-кейсов",
                extra={
                    "test_cases_count": len(ai_test_cases),
                    "function_name": func["name"],
                },
            )
            # Используем AI тест-кейсы как основные
            for ai_case in ai_test_cases:
                test_cases.append(
                    {
                        "id": ai_case.get(
                            "id", f"test-{func['name']}-{len(test_cases)}"
                        ),
                        "name": ai_case.get(
                            "name", f"{func['name']}_Test{len(test_cases)+1}"
                        ),
                        "description": ai_case.get("description", ""),
                        "input": ai_case.get("input", {}),
                        "expectedOutput": ai_case.get("expectedOutput"),
                        "type": ai_case.get("type", "unit"),
                        "category": ai_case.get("category", "positive"),
                    }
                )
    except Exception as e:
        logger.warning(
            "AI генерация тест-кейсов недоступна, используем базовые",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "function_name": func["name"] if "func" in locals() else None,
            },
        )

    # Если AI не сгенерировал тесты, используем базовые
    if not test_cases:
        # Положительный тест
        test_cases.append(
            {
                "id": f"test-{func['name']}-positive",
                "name": f"{func['name']}_Positive",
                "description": f"Позитивный тест для функции {func['name']}",
                "input": generate_default_input(func["params"]),
                "expectedOutput": "OK",
                "type": "unit",
                "category": "positive",
            }
        )

        # Негативный тест
        if func["params"]:
            test_cases.append(
                {
                    "id": f"test-{func['name']}-negative",
                    "name": f"{func['name']}_Negative",
                    "description": f"Негативный тест с невалидными данными",
                    "input": generate_invalid_input(func["params"]),
                    "expectedOutput": None,
                    "type": "unit",
                    "category": "negative",
                }
            )

        # Граничные случаи
        if include_edge_cases and func["params"]:
            test_cases.append(
                {
                    "id": f"test-{func['name']}-boundary",
                    "name": f"{func['name']}_Boundary",
                    "description": f"Граничный тест с минимальными/максимальными значениями",
                    "input": generate_boundary_input(func["params"]),
                    "expectedOutput": "OK",
                    "type": "unit",
                    "category": "boundary",
                }
            )

    return test_cases


def generate_default_input(params: List[str]) -> dict:
    """Генерация дефолтных входных данных"""
    return {param: 0 for param in params}


def generate_invalid_input(params: List[str]) -> dict:
    """Генерация невалидных входных данных"""
    return {param: None for param in params}


def generate_boundary_input(params: List[str]) -> dict:
    """Генерация граничных входных данных"""
    return {param: 0 for param in params}  # TODO: улучшить


def generate_bsl_test_code(func: dict, test_cases: List[dict]) -> str:
    """Генерация кода теста для BSL"""
    test_code = f"// Автоматически сгенерированные тесты для функции {func['name']}\n\n"

    for test_case in test_cases:
        test_code += f"Процедура Тест_{func['name']}_{test_case['name']}()\n"
        test_code += f"\n"
        test_code += f"\t// {test_case['description']}\n"
        test_code += f"\t\n"

        # Подготовка входных данных
        for key, value in test_case["input"].items():
            formatted_value = format_value(value)
            test_code += f"\t{key} = {formatted_value};\n"

        test_code += f"\t\n"

        # Вызов функции
        params_str = ", ".join(func["params"])
        test_code += f"\tРезультат = {func['name']}({params_str});\n"
        test_code += f"\t\n"

        # Проверка результата
        expected = format_value(test_case["expectedOutput"])
        test_code += (
            f'\tОжидаемоИстина(Результат = {expected}, "Ожидалось: {expected}");\n'
        )
        test_code += f"\n"
        test_code += f"КонецПроцедуры\n\n"

    return test_code


def format_value(value: Any) -> str:
    """Форматирование значения для BSL"""
    if value is None:
        return "Неопределено"
    if isinstance(value, str):
        return f'"{value}"'
    if isinstance(value, bool):
        return "Истина" if value else "Ложь"
    return str(value)


def calculate_coverage(original_code: str, test_code: str) -> int:
    """Расчет покрытия кода"""
    original_lines = len(original_code.split("\n"))
    tested_lines = len(test_code.split("\n"))
    return min(100, int((tested_lines / max(original_lines, 1)) * 100))


async def generate_python_tests(
    code: str, include_edge_cases: bool = False
) -> List[Dict]:
    """
    Generate pytest tests for Python code

    Args:
        code: Python source code
        include_edge_cases: Whether to include edge cases

    Returns:
        List of generated tests
    """
    import re

    tests = []

    # Parse Python functions
    function_pattern = r"def\s+(\w+)\s*\(([^)]*)\):"
    matches = re.finditer(function_pattern, code)

    for match in matches:
        function_name = match.group(1)
        params_str = match.group(2)

        # Parse parameters
        params = []
        if params_str.strip():
            for param in params_str.split(","):
                param = param.strip()
                if "=" in param:
                    param = param.split("=")[0].strip()
                if ":" in param:
                    param = param.split(":")[0].strip()
                if param and param != "self":
                    params.append(param)

        # Generate test cases
        test_cases = []

        # Happy path
        test_cases.append(
            {
                "name": f"test_{function_name}_happy_path",
                "description": f"Test {function_name} with valid inputs",
                "code": _generate_python_test_code(function_name, params, "happy"),
                "type": "happy_path",
            }
        )

        # Edge cases
        if include_edge_cases:
            test_cases.append(
                {
                    "name": f"test_{function_name}_empty_input",
                    "description": f"Test {function_name} with empty/null inputs",
                    "code": _generate_python_test_code(function_name, params, "empty"),
                    "type": "edge_case",
                }
            )

            test_cases.append(
                {
                    "name": f"test_{function_name}_invalid_type",
                    "description": f"Test {function_name} with invalid types",
                    "code": _generate_python_test_code(
                        function_name, params, "invalid"
                    ),
                    "type": "edge_case",
                }
            )

        tests.append(
            {
                "functionName": function_name,
                "testCases": test_cases,
                "framework": "pytest",
                "coverage": {
                    "lines": 80 if include_edge_cases else 60,
                    "branches": 70 if include_edge_cases else 50,
                },
            }
        )

    return tests


def _generate_python_test_code(
    function_name: str, params: List[str], test_type: str
) -> str:
    """Generate pytest test code"""

    if test_type == "happy":
        param_values = ", ".join(
            [f"'{p}_value'" if i % 2 == 0 else str(i) for i, p in enumerate(params)]
        )
        return f"""
def test_{function_name}_happy_path():
    # Arrange
    {', '.join(params)} = {param_values if param_values else ''}
    
    # Act
    result = {function_name}({', '.join(params) if params else ''})
    
    # Assert
    assert result is not None
    # TODO: Add specific assertions
"""

    elif test_type == "empty":
        return f"""
def test_{function_name}_empty_input():
    # Test with None/empty inputs
    result = {function_name}({', '.join(['None'] * len(params)) if params else ''})
    
    # Should handle gracefully
    assert result is not None or result == expected_default
"""

    elif test_type == "invalid":
        return f"""
def test_{function_name}_invalid_type():
    # Test with wrong types
    with pytest.raises((TypeError, ValueError)):
        {function_name}({', '.join(["'invalid'"] * len(params)) if params else ''})
"""

    return ""


async def generate_javascript_tests(
    code: str, include_edge_cases: bool = False
) -> List[Dict]:
    """
    Generate Jest tests for JavaScript code

    Args:
        code: JavaScript source code
        include_edge_cases: Whether to include edge cases

    Returns:
        List of generated tests
    """
    import re

    tests = []

    # Parse JavaScript functions
    function_pattern = (
        r"(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>)\s*\("
    )
    matches = re.finditer(function_pattern, code)

    for match in matches:
        function_name = match.group(1) or match.group(2)

        # Generate test cases
        test_cases = []

        # Happy path
        test_cases.append(
            {
                "name": f"{function_name} should work with valid input",
                "description": f"Test {function_name} happy path",
                "code": _generate_javascript_test_code(function_name, "happy"),
                "type": "happy_path",
            }
        )

        # Edge cases
        if include_edge_cases:
            test_cases.append(
                {
                    "name": f"{function_name} should handle null input",
                    "description": f"Test {function_name} with null",
                    "code": _generate_javascript_test_code(function_name, "null"),
                    "type": "edge_case",
                }
            )

            test_cases.append(
                {
                    "name": f"{function_name} should throw on invalid input",
                    "description": f"Test {function_name} error handling",
                    "code": _generate_javascript_test_code(function_name, "error"),
                    "type": "edge_case",
                }
            )

        tests.append(
            {
                "functionName": function_name,
                "testCases": test_cases,
                "framework": "jest",
                "coverage": {
                    "lines": 80 if include_edge_cases else 60,
                    "branches": 70 if include_edge_cases else 50,
                },
            }
        )

    return tests


def _generate_javascript_test_code(function_name: str, test_type: str) -> str:
    """Generate Jest test code"""

    if test_type == "happy":
        return f"""
describe('{function_name}', () => {{
  it('should work with valid input', () => {{
    // Arrange
    const input = 'test_value';
    
    // Act
    const result = {function_name}(input);
    
    // Assert
    expect(result).toBeDefined();
    // TODO: Add specific assertions
  }});
}});
"""

    elif test_type == "null":
        return f"""
describe('{function_name}', () => {{
  it('should handle null input', () => {{
    // Act & Assert
    expect(() => {function_name}(null)).not.toThrow();
    // Or expect specific behavior
  }});
}});
"""

    elif test_type == "error":
        return f"""
describe('{function_name}', () => {{
  it('should throw on invalid input', () => {{
    // Arrange
    const invalidInput = {{}};
    
    // Act & Assert
    expect(() => {function_name}(invalidInput)).toThrow();
  }});
}});
"""

    return ""


# ==================== API ENDPOINTS ====================


@router.post(
    "/generate",
    response_model=TestGenerationResponse,
    tags=["Test Generation"],
    summary="Генерация тестов для кода",
    description="Автоматическая генерация тестов для указанного кода",
)
@limiter.limit("10/minute")  # Rate limit: 10 test generations per minute
async def generate_tests(request: Request, request_data: TestGenerationRequest):
    """
    Генерация тестов с валидацией входных данных

    Best practices:
    - Валидация длины кода
    - Sanitization входных данных
    - Улучшенная обработка ошибок
    - Структурированное логирование
    """

    try:
        # Input validation and sanitization (best practice)
        code = request_data.code.strip()
        if not code:
            raise HTTPException(status_code=400, detail="Code cannot be empty")

        # Limit code length (prevent DoS)
        max_code_length = 100000  # 100KB max
        if len(code) > max_code_length:
            raise HTTPException(
                status_code=400,
                detail=f"Code too long. Maximum length: {max_code_length} characters",
            )

        # Validate language
        supported_languages = ["bsl", "typescript", "python", "javascript"]
        if request_data.language not in supported_languages:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported language: {request_data.language}. Supported: {', '.join(supported_languages)}",
            )

        # Generate tests based on language with timeout
        timeout = 30.0  # 30 seconds timeout for test generation

        if request_data.language == "bsl":
            tests = await generate_bsl_tests(
                code, request_data.includeEdgeCases, timeout=timeout
            )
        elif request_data.language == "typescript":
            if generate_typescript_tests is None:
                raise HTTPException(
                    status_code=500,
                    detail="TypeScript test generation module not available",
                )
            tests = await generate_typescript_tests(code, request_data.includeEdgeCases)
        elif request_data.language == "python":
            tests = await generate_python_tests(code, request_data.includeEdgeCases)
        elif request_data.language == "javascript":
            tests = await generate_javascript_tests(code, request_data.includeEdgeCases)
        else:
            # This should never happen due to validation above, but keep for safety
            raise HTTPException(
                status_code=400,
                detail=f"Language {request_data.language} not supported",
            )

        # Формирование summary с безопасной обработкой (best practice: handle edge cases)
        total_functions = len([t for t in tests if isinstance(t, dict)])
        total_test_cases = sum(
            len(t.get("testCases", [])) if isinstance(t, dict) else 0 for t in tests
        )

        # Safe average coverage calculation
        coverage_values = [
            t.get("coverage", {}).get("lines", 0)
            for t in tests
            if isinstance(t, dict) and "coverage" in t
        ]
        avg_coverage = (
            sum(coverage_values) / len(coverage_values) if coverage_values else 0
        )

        summary = {
            "totalTests": len(tests),
            "totalTestCases": total_test_cases,
            "totalFunctions": total_functions,
            "averageCoverage": round(avg_coverage, 2),
            "language": request_data.language,
            "framework": tests[0].get("framework")
            if tests and isinstance(tests[0], dict)
            else None,
        }

        generation_id = f"gen-{datetime.now().timestamp()}"

        # Safe conversion to GeneratedTest (best practice: validate data)
        try:
            test_objects = [GeneratedTest(**t) for t in tests if isinstance(t, dict)]
        except Exception as e:
            logger.error(
                "Failed to convert tests to GeneratedTest objects",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "tests_count": len(tests) if tests else 0,
                },
                exc_info=True,
            )
            raise HTTPException(status_code=500, detail="Failed to format test results")

        return TestGenerationResponse(
            tests=test_objects, summary=summary, generationId=generation_id
        )

    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(
            "Unexpected error in test generation",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "language": request_data.language
                if hasattr(request_data, "language")
                else None,
                "code_length": len(request_data.code)
                if hasattr(request_data, "code")
                else 0,
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="An error occurred while generating tests"
        )


@router.get("/health", tags=["Test Generation"], summary="Проверка состояния сервиса")
async def health_check():
    """Проверка доступности сервиса генерации тестов"""
    return {
        "status": "healthy",
        "service": "test-generation",
        "version": "1.0.0",
        "supported_languages": ["bsl", "typescript"],
        "features": {
            "unit_tests": True,
            "integration_tests": False,  # TODO
            "e2e_tests": False,  # TODO
            "ai_generation": True,  # ✅ Интегрировано с OpenAI
        },
    }
