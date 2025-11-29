import ast
from typing import List, Dict, Set, Optional
from src.modules.security.domain.models import Vulnerability, VulnerabilityType, Severity

class TaintAnalyzer:
    """
    Сервис для анализа потоков данных (Taint Analysis).
    Отслеживает распространение "грязных" данных от источников (Sources) к стокам (Sinks).
    """

    def __init__(self):
        # Источники "грязных" данных (например, аргументы функций, ввод пользователя)
        self.sources = {"request", "input", "event", "data"}
        
        # Опасные стоки (функции, куда нельзя передавать грязные данные)
        self.sinks = {
            "eval": VulnerabilityType.CODE_INJECTION,
            "exec": VulnerabilityType.CODE_INJECTION,
            "os.system": VulnerabilityType.COMMAND_INJECTION,
            "subprocess.call": VulnerabilityType.COMMAND_INJECTION,
            "cursor.execute": VulnerabilityType.SQL_INJECTION,
        }

    def analyze(self, code: str) -> List[Vulnerability]:
        """
        Выполняет Taint Analysis для предоставленного кода.
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []

        visitor = TaintVisitor(self.sources, self.sinks)
        visitor.visit(tree)
        
        return visitor.vulnerabilities

class TaintVisitor(ast.NodeVisitor):
    def __init__(self, sources: Set[str], sinks: Dict[str, VulnerabilityType]):
        self.sources = sources
        self.sinks = sinks
        self.vulnerabilities: List[Vulnerability] = []
        
        # Карта переменных, которые "заражены" (tainted)
        # Имя переменной -> Источник заражения
        self.tainted_vars: Dict[str, str] = {}

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Аргументы функции считаем потенциально грязными, если они похожи на sources
        # Или для строгости - все аргументы публичных методов API
        for arg in node.args.args:
            if arg.arg in self.sources:
                self.tainted_vars[arg.arg] = f"Argument '{arg.arg}'"
        
        self.generic_visit(node)
        
        # Очистка контекста после выхода из функции (упрощенно, без учета глобальных)
        # В реальном Taint Analysis нужен Control Flow Graph (CFG)
        self.tainted_vars.clear()

    def visit_Assign(self, node: ast.Assign):
        """
        Отслеживает распространение заражения при присваивании.
        x = y (если y tainted, то x становится tainted)
        """
        # Проверяем правую часть (value)
        is_tainted = False
        source = None
        
        # Если справа вызов функции, которая возвращает tainted (упрощенно)
        # Или просто использование tainted переменной
        for child in ast.walk(node.value):
            if isinstance(child, ast.Name) and child.id in self.tainted_vars:
                is_tainted = True
                source = self.tainted_vars[child.id]
                break
            # Если прямой ввод
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name) and child.func.id == "input":
                is_tainted = True
                source = "input()"
                break

        if is_tainted:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.tainted_vars[target.id] = source
        
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        """
        Проверяет попадание tainted данных в sinks.
        """
        func_name = None
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            # Попытка получить полное имя, например os.system
            if isinstance(node.func.value, ast.Name):
                func_name = f"{node.func.value.id}.{node.func.attr}"

        if func_name and func_name in self.sinks:
            # Проверяем аргументы
            for arg in node.args:
                if isinstance(arg, ast.Name) and arg.id in self.tainted_vars:
                    self.vulnerabilities.append(
                        Vulnerability(
                            type=self.sinks[func_name],
                            severity=Severity.CRITICAL,
                            location=f"Строка {node.lineno}",
                            line_number=node.lineno,
                            description=f"Taint Analysis: Попадание непроверенных данных из {self.tainted_vars[arg.id]} в опасную функцию {func_name}",
                            recommendation="Санитизируйте входные данные перед использованием.",
                            cwe_id="CWE-20"
                        )
                    )
        
        self.generic_visit(node)
