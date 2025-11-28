"""Test generation utilities for TypeScript."""

import re
from datetime import datetime
from typing import Any, Dict, List

from src.services.openai_code_analyzer import get_openai_analyzer
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


def extract_typescript_functions(code: str) -> List[Dict[str, Any]]:
    """Extract functions from TypeScript code."""
    functions = []

    patterns = [
        r"function\s+(\w+)\s*\(([^)]*)\)\s*(?::\s*([^{]+))?\s*{",
        r"const\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*(?::\s*([^{]+))?\s*=>\s*{",
        r"(\w+)\s*:\s*(?:async\s+)?\(([^)]*)\)\s*(?::\s*([^{]+))?\s*=>\s*{",
    ]

    for pattern in patterns:
        matches = re.finditer(pattern, code, re.MULTILINE)
        for match in matches:
            func_name = match.group(1)
            params_str = match.group(2) if match.group(2) else ""
            return_type = match.group(3) if match.group(3) else "void"

            start_pos = match.end()
            brace_count = 1
            end_pos = start_pos

            for i, char in enumerate(code[start_pos:], start_pos):
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        end_pos = i + 1
                        break

            func_code = code[match.start(): end_pos]

            functions.append(
                {
                    "name": func_name,
                    "params": _parse_ts_params(params_str),
                    "return_type": return_type.strip(),
                    "code": func_code,
                }
            )

    return functions


def _parse_ts_params(params_str: str) -> List[str]:
    """Parse TypeScript parameters."""
    if not params_str.strip():
        return []

    params = []
    current_param = ""
    depth = 0

    for char in params_str:
        if char in ["(", "[", "{"]:
            depth += 1
            current_param += char
        elif char in [")", "]", "}"]:
            depth -= 1
            current_param += char
        elif char == "," and depth == 0:
            param_name = current_param.strip().split(":")[0].strip()
            if param_name:
                params.append(param_name)
            current_param = ""
        else:
            current_param += char

    if current_param.strip():
        param_name = current_param.strip().split(":")[0].strip()
        if param_name:
            params.append(param_name)

    return params


def generate_jest_test_code(
        func: Dict[str, Any], test_cases: List[Dict[str, Any]]) -> str:
    """Generate Jest tests for TypeScript function."""
    test_code = f"// Auto-generated tests for {func['name']}\n\n"
    test_code += "import { " + func["name"] + " } from './module';\n\n"

    test_code += f"describe('{func['name']}', () => {{\n"

    for test_case in test_cases:
        test_code += f"  it('{test_case['name']}', () => {{\n"
        test_code += f"    // {test_case['description']}\n"

        for key, value in test_case["input"].items():
            formatted_value = _format_ts_value(value)
            test_code += f"    const {key} = {formatted_value};\n"

        test_code += "\n"

        params_str = ", ".join(test_case["input"].keys())
        test_code += f"    const result = {func['name']}({params_str});\n"
        test_code += "\n"

        expected = _format_ts_value(test_case["expectedOutput"])
        test_code += f"    expect(result).toBe({expected});\n"
        test_code += "  });\n\n"

    test_code += "});\n"

    return test_code


def _format_ts_value(value: Any) -> str:
    """Format value for TypeScript."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return f'"{value}"'
    if isinstance(value, (list, dict)):
        return str(value).replace("'", '"')
    return str(value)


async def generate_typescript_tests(
        code: str, include_edge_cases: bool = True) -> List[Dict[str, Any]]:
    """Generate tests for TypeScript code."""
    tests = []

    functions = extract_typescript_functions(code)

    for func in functions:
        test_cases = []

        try:
