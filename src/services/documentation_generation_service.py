# [NEXUS IDENTITY] ID: -5408853119765682696 | DATE: 2025-11-19

"""
Documentation Generation Service
Автоматическая генерация документации из кода
Версия: 1.0.0
"""

import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DocumentationGenerator:
    """Генератор документации из кода"""

    def __init__(self):
        self.supported_languages = ["bsl", "typescript", "python", "javascript"]

    def generate_documentation(
        self,
        code: str,
        language: str = "bsl",
        function_name: Optional[str] = None,
        format: str = "markdown",
    ) -> Dict[str, Any]:
        """
        Генерация документации из кода

        Args:
            code: Исходный код
            language: Язык программирования
            function_name: Имя функции (опционально)
            format: Формат документации (markdown, html, plain)

        Returns:
            Словарь с документацией
        """
        if language == "bsl":
            return self._generate_bsl_documentation(code, function_name, format)
        elif language in ["typescript", "javascript"]:
            return self._generate_ts_documentation(code, function_name, format)
        elif language == "python":
            return self._generate_python_documentation(code, function_name, format)
        else:
            raise ValueError(f"Неподдерживаемый язык: {language}")

    def _generate_bsl_documentation(
        self, code: str, function_name: Optional[str], format: str
    ) -> Dict[str, Any]:
        """Генерация документации для BSL"""

        doc = {
            "title": f"Документация для {function_name or 'кода'}",
            "language": "bsl",
            "generated_at": datetime.now().isoformat(),
            "sections": [],
        }

        # Извлечение функций
        functions = self._extract_bsl_functions(code)

        for func in functions:
            section = {
                "name": func["name"],
                "type": func["type"],  # Процедура или Функция
                "signature": func["signature"],
                "parameters": func["params"],
                "description": func["description"],
                "examples": func.get("examples", []),
                "return_value": func.get("return_value"),
                "notes": func.get("notes", []),
            }

            doc["sections"].append(section)

        # Генерация текста документации
        if format == "markdown":
            doc["content"] = self._format_markdown_bsl(doc)
        elif format == "html":
            doc["content"] = self._format_html_bsl(doc)
        else:
            doc["content"] = self._format_plain_bsl(doc)

        return doc

    def _extract_bsl_functions(self, code: str) -> List[Dict[str, Any]]:
        """Извлечение функций из BSL кода с комментариями"""
        functions = []
        lines = code.split("\n")

        current_function = None
        in_function = False
        function_lines = []
        comment_buffer = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Сохранение комментариев перед функцией
            if stripped.startswith("//") or (
                stripped.startswith("'") and not in_function
            ):
                comment_buffer.append(stripped.lstrip("/'").strip())
                continue

            # Начало функции
            func_match = re.search(
                r"^\s*(Функция|Процедура)\s+(\w+)\s*(?:\(([^)]*)\))?",
                stripped,
                re.IGNORECASE,
            )
            if func_match:
                # Сохраняем предыдущую функцию
                if current_function and function_lines:
                    current_function["code"] = "\n".join(function_lines)
                    functions.append(current_function)

                # Начинаем новую функцию
                func_type = func_match.group(1)
                func_name = func_match.group(2)
                params_str = func_match.group(3) or ""

                current_function = {
                    "name": func_name,
                    "type": "Функция" if "Функция" in func_type else "Процедура",
                    "signature": line.strip(),
                    "params": self._parse_bsl_params(params_str),
                    "description": "\n".join(comment_buffer).strip()
                    or f"{func_type} {func_name}",
                    "code": "",
                    "examples": [],
                    "notes": [],
                }

                function_lines = [line]
                comment_buffer = []
                in_function = True
                continue

            # Если внутри функции
            if in_function and current_function:
                function_lines.append(line)

                # Конец функции
                if re.search(
                    r"\s*Конец(?:Функции|Процедуры)\s*$", stripped, re.IGNORECASE
                ):
                    current_function["code"] = "\n".join(function_lines)

                    # Извлечение return значения (для функций)
                    if current_function["type"] == "Функция":
                        return_match = re.search(
                            r"Возврат\s+([^;]+)",
                            current_function["code"],
                            re.IGNORECASE,
                        )
                        if return_match:
                            current_function["return_value"] = return_match.group(
                                1
                            ).strip()

                    functions.append(current_function)
                    current_function = None
                    in_function = False
                    function_lines = []

        # Сохраняем последнюю функцию
        if current_function and function_lines:
            current_function["code"] = "\n".join(function_lines)
            functions.append(current_function)

        return functions

    def _parse_bsl_params(self, params_str: str) -> List[Dict[str, str]]:
        """Парсинг параметров BSL функции"""
        if not params_str.strip():
            return []

        params = []
        for param in params_str.split(","):
            param = param.strip()
            if not param:
                continue

            # Формат: ИмяПараметра, ИмяПараметра = ЗначениеПоУмолчанию, ИмяПараметра ПередачаПоЗначению
            parts = param.split("=")
            param_name = parts[0].strip().split()[0]
            default_value = parts[1].strip() if len(parts) > 1 else None

            params.append(
                {
                    "name": param_name,
                    "type": "Any",  # BSL динамическая типизация
                    "default": default_value,
                    "description": "",
                }
            )

        return params

    def _format_markdown_bsl(self, doc: Dict[str, Any]) -> str:
        """Форматирование в Markdown"""
        lines = [f"# {doc['title']}\n"]
        lines.append(f"**Язык:** {doc['language'].upper()}  \n")
        lines.append(f"**Дата генерации:** {doc['generated_at']}  \n\n")
        lines.append("---\n\n")

        for section in doc["sections"]:
            lines.append(f"## {section['type']} {section['name']}\n\n")

            # Описание
            if section["description"]:
                lines.append(f"{section['description']}\n\n")

            # Сигнатура
            lines.append("```bsl\n")
            lines.append(f"{section['signature']}\n")
            lines.append("```\n\n")

            # Параметры
            if section["parameters"]:
                lines.append("### Параметры\n\n")
                lines.append("| Имя | Тип | Описание |\n")
                lines.append("|-----|-----|----------|\n")
                for param in section["parameters"]:
                    lines.append(
                        f"| `{param['name']}` | {param.get('type', 'Any')} | {param.get('description', '')} |\n"
                    )
                lines.append("\n")

            # Возвращаемое значение
            if section.get("return_value"):
                lines.append(f"### Возвращаемое значение\n\n")
                lines.append(f"`{section['return_value']}`\n\n")

            # Примеры
            if section.get("examples"):
                lines.append("### Примеры\n\n")
                for example in section["examples"]:
                    lines.append("```bsl\n")
                    lines.append(f"{example}\n")
                    lines.append("```\n\n")

            lines.append("---\n\n")

        return "".join(lines)

    def _format_html_bsl(self, doc: Dict[str, Any]) -> str:
        """Форматирование в HTML"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{doc['title']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #555; margin-top: 30px; }}
        code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }}
        pre {{ background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
    </style>
</head>
<body>
    <h1>{doc['title']}</h1>
    <p><strong>Язык:</strong> {doc['language'].upper()}</p>
    <p><strong>Дата генерации:</strong> {doc['generated_at']}</p>
    <hr>
"""

        for section in doc["sections"]:
            html += f"    <h2>{section['type']} {section['name']}</h2>\n"

            if section["description"]:
                html += f"    <p>{section['description']}</p>\n"

            html += f"    <pre><code>{section['signature']}</code></pre>\n"

            if section["parameters"]:
                html += "    <h3>Параметры</h3>\n"
                html += "    <table>\n"
                html += "        <tr><th>Имя</th><th>Тип</th><th>Описание</th></tr>\n"
                for param in section["parameters"]:
                    html += f"        <tr><td><code>{param['name']}</code></td><td>{param.get('type', 'Any')}</td><td>{param.get('description', '')}</td></tr>\n"
                html += "    </table>\n"

            if section.get("return_value"):
                html += f"    <h3>Возвращаемое значение</h3>\n"
                html += f"    <p><code>{section['return_value']}</code></p>\n"

            html += "    <hr>\n"

        html += """</body>
</html>"""

        return html

    def _format_plain_bsl(self, doc: Dict[str, Any]) -> str:
        """Форматирование в plain text"""
        lines = [f"{doc['title']}\n"]
        lines.append(f"Язык: {doc['language'].upper()}\n")
        lines.append(f"Дата генерации: {doc['generated_at']}\n")
        lines.append("=" * 80 + "\n\n")

        for section in doc["sections"]:
            lines.append(f"{section['type']} {section['name']}\n")
            lines.append("-" * 80 + "\n")

            if section["description"]:
                lines.append(f"{section['description']}\n\n")

            lines.append(f"Сигнатура: {section['signature']}\n\n")

            if section["parameters"]:
                lines.append("Параметры:\n")
                for param in section["parameters"]:
                    lines.append(f"  - {param['name']}: {param.get('type', 'Any')}\n")
                lines.append("\n")

            if section.get("return_value"):
                lines.append(f"Возвращает: {section['return_value']}\n\n")

            lines.append("\n")

        return "".join(lines)

    def _generate_ts_documentation(
        self, code: str, function_name: Optional[str], format: str
    ) -> Dict[str, Any]:
        """Генерация документации для TypeScript/JavaScript"""
        # TODO: Реализовать для TypeScript
        return {
            "title": "TypeScript Documentation",
            "language": "typescript",
            "content": "TypeScript documentation generation - TODO",
            "sections": [],
        }

    def _generate_python_documentation(
        self, code: str, function_name: Optional[str], format: str
    ) -> Dict[str, Any]:
        """Генерация документации для Python"""
        # TODO: Реализовать для Python
        return {
            "title": "Python Documentation",
            "language": "python",
            "content": "Python documentation generation - TODO",
            "sections": [],
        }


# Глобальный экземпляр
_doc_generator: Optional[DocumentationGenerator] = None


def get_documentation_generator() -> DocumentationGenerator:
    """Получение экземпляра генератора документации"""
    global _doc_generator
    if _doc_generator is None:
        _doc_generator = DocumentationGenerator()
    return _doc_generator
