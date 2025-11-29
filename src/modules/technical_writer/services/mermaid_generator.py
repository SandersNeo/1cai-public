import ast
from typing import List, Dict, Optional

class MermaidGenerator:
    """
    Сервис для генерации диаграмм классов в формате Mermaid из исходного кода Python.
    Визуализирует классы, методы и наследование.
    """

    def generate_class_diagram(self, code: str) -> str:
        """
        Генерирует Mermaid Class Diagram.
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return "graph TD\n    Error[Ошибка парсинга кода]"

        visitor = ClassVisitor()
        visitor.visit(tree)
        
        diagram = "classDiagram\n"
        
        # Отношения наследования
        for cls in visitor.classes:
            for base in cls["bases"]:
                diagram += f"    {base} <|-- {cls['name']}\n"
                
        # Определения классов
        for cls in visitor.classes:
            diagram += f"    class {cls['name']} {{\n"
            
            # Поля (упрощенно, из аннотаций __init__ или класса)
            # В MVP пока пропускаем поля, фокусируемся на методах
            
            # Методы
            for method in cls["methods"]:
                diagram += f"        +{method['name']}{method['args']}\n"
                
            diagram += "    }\n"
            
        return diagram

class ClassVisitor(ast.NodeVisitor):
    def __init__(self):
        self.classes = []

    def visit_ClassDef(self, node: ast.ClassDef):
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(base.attr)
                
        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                if item.name.startswith("_") and item.name != "__init__":
                    continue
                
                # Аргументы для сигнатуры
                args_list = [a.arg for a in item.args.args if a.arg != 'self']
                args_str = "(" + ", ".join(args_list) + ")"
                
                methods.append({
                    "name": item.name,
                    "args": args_str
                })
        
        self.classes.append({
            "name": node.name,
            "bases": bases,
            "methods": methods
        })
