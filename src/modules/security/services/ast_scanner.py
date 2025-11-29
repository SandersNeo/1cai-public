import ast
from typing import List, Dict, Any
from src.modules.security.domain.models import Vulnerability, VulnerabilityType, Severity


class ASTVulnerabilityScanner:
    """
    Продвинутый сканер уязвимостей, использующий Abstract Syntax Tree (AST) Python.
    Обнаруживает небезопасные вызовы функций и паттерны, которые могут быть пропущены регулярными выражениями.
    """

    def scan(self, code: str) -> List[Vulnerability]:
        """
        Парсит код в AST и обходит его для поиска уязвимостей.
        """
        vulnerabilities = []
        try:
            tree = ast.parse(code)
        except SyntaxError:
            # Если код не является валидным Python, мы не можем сканировать его с помощью AST.
            # Возвращаем пустой список (regex сканер может что-то поймать).
            return []

        visitor = SecurityVisitor()
        visitor.visit(tree)

        return visitor.vulnerabilities


class SecurityVisitor(ast.NodeVisitor):
    def __init__(self):
        self.vulnerabilities: List[Vulnerability] = []

    def visit_Call(self, node: ast.Call):
        """
        Посещает вызовы функций.
        """
        # Проверка на опасные вызовы функций
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            self._check_dangerous_call(func_name, node)
        elif isinstance(node.func, ast.Attribute):
            # например, os.system, subprocess.call
            func_name = node.func.attr
            # Мы могли бы проверять и модуль, но пока проверка имени атрибута - хорошее начало
            self._check_dangerous_call(func_name, node)

        self.generic_visit(node)

    def _check_dangerous_call(self, func_name: str, node: ast.Call):
        """
        Проверяет, находится ли вызов функции в списке опасных.
        """
        dangerous_funcs = {
            "eval": (VulnerabilityType.CODE_INJECTION, Severity.CRITICAL, "Избегайте использования eval()"),
            "exec": (VulnerabilityType.CODE_INJECTION, Severity.CRITICAL, "Избегайте использования exec()"),
            "system": (VulnerabilityType.COMMAND_INJECTION, Severity.CRITICAL, "Избегайте использования os.system()"),
            "popen": (VulnerabilityType.COMMAND_INJECTION, Severity.HIGH, "Используйте subprocess.run с shell=False"),
            "loads": (
                VulnerabilityType.DESERIALIZATION,
                Severity.MEDIUM,
                "Убедитесь, что источник pickle/yaml надежен",
            ),  # pickle.loads
        }

        if func_name in dangerous_funcs:
            vuln_type, severity, recommendation = dangerous_funcs[func_name]

            # Базовая проверка: если есть аргументы, это потенциально опасно
            if node.args or node.keywords:
                self.vulnerabilities.append(
                    Vulnerability(
                        type=vuln_type,
                        severity=severity,
                        location=f"Строка {node.lineno}",
                        line_number=node.lineno,
                        description=f"Обнаружен опасный вызов функции: {func_name}",
                        recommendation=recommendation,
                        cwe_id="CWE-78" if "INJECTION" in str(vuln_type) else "CWE-502",
                    )
                )

    def visit_Import(self, node: ast.Import):
        """
        Проверяет опасные импорты.
        """
        for alias in node.names:
            if alias.name == "telnetlib":
                self.vulnerabilities.append(
                    Vulnerability(
                        type=VulnerabilityType.INSECURE_PROTOCOL,
                        severity=Severity.HIGH,
                        location=f"Строка {node.lineno}",
                        line_number=node.lineno,
                        description="Обнаружено использование небезопасного telnetlib",
                        recommendation="Используйте SSH или другие зашифрованные протоколы",
                        cwe_id="CWE-319",
                    )
                )
        self.generic_visit(node)
