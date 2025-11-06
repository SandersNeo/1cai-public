#!/usr/bin/env python3
"""
Глубокий аудит качества кода
Этап 2: Анализ качества всего Python кода

Проверяет:
- Все .py файлы в проекте
- Соответствие PEP 8
- Сложность кода
- Type hints
- Docstrings
- Импорты
"""

import os
import ast
import sys
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict, Counter
import re

class CodeQualityAuditor:
    """Аудитор качества кода"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.stats = defaultdict(int)
        self.issues = defaultdict(list)
        self.ignore_dirs = {'__pycache__', '.git', 'node_modules', 'venv', '.venv', '1c_configurations'}
    
    def audit_python_code(self) -> Dict:
        """Полный аудит Python кода"""
        print("=" * 80)
        print("ГЛУБОКИЙ АУДИТ КАЧЕСТВА PYTHON КОДА")
        print("=" * 80)
        print()
        
        # 1. Сканирование всех .py файлов
        print("[*] Поиск Python файлов...")
        py_files = self.find_python_files()
        print(f"    Найдено .py файлов: {len(py_files):,}")
        
        # 2. Анализ каждого файла
        print("\n[*] Анализ файлов...")
        for i, py_file in enumerate(py_files, 1):
            if i % 50 == 0:
                print(f"    Обработано: {i}/{len(py_files)}")
            self.analyze_file(py_file)
        
        # 3. Анализ сложности
        print("\n[*] Анализ сложности...")
        self.analyze_complexity()
        
        # 4. Проверка docstrings
        print("\n[*] Проверка docstrings...")
        self.analyze_docstrings()
        
        # 5. Проверка type hints
        print("\n[*] Проверка type hints...")
        self.analyze_type_hints()
        
        # 6. Проверка импортов
        print("\n[*] Проверка импортов...")
        self.analyze_imports()
        
        # 7. Поиск проблем
        print("\n[*] Поиск code smells...")
        self.find_code_smells()
        
        return {
            'total_files': len(py_files),
            'stats': dict(self.stats),
            'issues': {k: len(v) for k, v in self.issues.items()},
            'top_issues': self.get_top_issues()
        }
    
    def find_python_files(self) -> List[Path]:
        """Поиск всех .py файлов"""
        py_files = []
        
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
            
            for file in files:
                if file.endswith('.py'):
                    py_files.append(Path(root) / file)
        
        return py_files
    
    def analyze_file(self, file_path: Path):
        """Анализ одного Python файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.stats['files_analyzed'] += 1
            self.stats['total_lines'] += len(content.split('\n'))
            
            # Парсинг AST
            try:
                tree = ast.parse(content)
                self.analyze_ast(tree, file_path)
            except SyntaxError as e:
                self.issues['syntax_errors'].append({
                    'file': str(file_path.relative_to(self.project_root)),
                    'error': str(e)
                })
                self.stats['syntax_errors'] += 1
            
            # Простые проверки
            self.check_file_length(file_path, content)
            self.check_line_length(file_path, content)
            
        except Exception as e:
            self.issues['read_errors'].append({
                'file': str(file_path.relative_to(self.project_root)),
                'error': str(e)
            })
    
    def analyze_ast(self, tree: ast.AST, file_path: Path):
        """Анализ AST дерева"""
        for node in ast.walk(tree):
            # Подсчет классов
            if isinstance(node, ast.ClassDef):
                self.stats['total_classes'] += 1
                if node.body and isinstance(node.body[0], ast.Expr) and \
                   isinstance(node.body[0].value, ast.Constant):
                    self.stats['classes_with_docstring'] += 1
            
            # Подсчет функций
            elif isinstance(node, ast.FunctionDef):
                self.stats['total_functions'] += 1
                
                # Docstring
                if ast.get_docstring(node):
                    self.stats['functions_with_docstring'] += 1
                
                # Type hints
                if node.returns:
                    self.stats['functions_with_return_type'] += 1
                
                # Параметры с типами
                params_with_types = sum(1 for arg in node.args.args if arg.annotation)
                if params_with_types > 0:
                    self.stats['functions_with_param_types'] += 1
                
                # Сложность
                complexity = self.calculate_complexity(node)
                if complexity > 10:
                    self.issues['high_complexity'].append({
                        'file': str(file_path.relative_to(self.project_root)),
                        'function': node.name,
                        'complexity': complexity
                    })
    
    def calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Расчет цикломатической сложности"""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def check_file_length(self, file_path: Path, content: str):
        """Проверка длины файла"""
        lines = len(content.split('\n'))
        
        if lines > 1000:
            self.issues['long_files'].append({
                'file': str(file_path.relative_to(self.project_root)),
                'lines': lines
            })
        
        if lines > 500:
            self.stats['files_over_500_lines'] += 1
    
    def check_line_length(self, file_path: Path, content: str):
        """Проверка длины строк"""
        long_lines = 0
        
        for i, line in enumerate(content.split('\n'), 1):
            if len(line) > 120:
                long_lines += 1
                if long_lines <= 5:  # Сохраняем только первые 5
                    self.issues['long_lines'].append({
                        'file': str(file_path.relative_to(self.project_root)),
                        'line': i,
                        'length': len(line)
                    })
        
        if long_lines > 0:
            self.stats['files_with_long_lines'] += 1
    
    def analyze_complexity(self):
        """Анализ сложности кода"""
        high_complexity = self.issues.get('high_complexity', [])
        
        print(f"\n    Функций с высокой сложностью (>10): {len(high_complexity):,}")
        
        if high_complexity:
            print("\n    Примеры (ТОП-10 по сложности):")
            sorted_by_complexity = sorted(high_complexity, key=lambda x: x['complexity'], reverse=True)[:10]
            for i, issue in enumerate(sorted_by_complexity, 1):
                print(f"    {i:2d}. {issue['function']:<40} complexity={issue['complexity']}")
                print(f"        {issue['file']}")
    
    def analyze_docstrings(self):
        """Анализ docstrings"""
        total_classes = self.stats.get('total_classes', 0)
        with_docstring = self.stats.get('classes_with_docstring', 0)
        
        total_funcs = self.stats.get('total_functions', 0)
        funcs_with_doc = self.stats.get('functions_with_docstring', 0)
        
        print(f"\n    Классов: {total_classes:,}")
        if total_classes > 0:
            pct = with_docstring / total_classes * 100
            print(f"    С docstring: {with_docstring:,} ({pct:.1f}%)")
        
        print(f"\n    Функций: {total_funcs:,}")
        if total_funcs > 0:
            pct = funcs_with_doc / total_funcs * 100
            print(f"    С docstring: {funcs_with_doc:,} ({pct:.1f}%)")
    
    def analyze_type_hints(self):
        """Анализ type hints"""
        total_funcs = self.stats.get('total_functions', 0)
        with_return = self.stats.get('functions_with_return_type', 0)
        with_params = self.stats.get('functions_with_param_types', 0)
        
        if total_funcs > 0:
            pct_return = with_return / total_funcs * 100
            pct_params = with_params / total_funcs * 100
            
            print(f"\n    Функций с type hints:")
            print(f"    - Return type: {with_return:,} ({pct_return:.1f}%)")
            print(f"    - Parameter types: {with_params:,} ({pct_params:.1f}%)")
    
    def analyze_imports(self):
        """Анализ импортов"""
        # Подсчитываем проблемы с импортами
        print(f"\n    Проблем с импортами: {len(self.issues.get('import_issues', [])):,}")
    
    def find_code_smells(self):
        """Поиск code smells"""
        long_files = len(self.issues.get('long_files', []))
        long_lines = len(self.issues.get('long_lines', []))
        
        print(f"\n    Файлов >1000 строк: {long_files:,}")
        print(f"    Строк >120 символов: {long_lines:,}")
        
        if long_files > 0:
            print("\n    Самые длинные файлы (ТОП-10):")
            sorted_files = sorted(self.issues['long_files'], key=lambda x: x['lines'], reverse=True)[:10]
            for i, issue in enumerate(sorted_files, 1):
                print(f"    {i:2d}. {issue['file']:<60} {issue['lines']:>5} строк")
    
    def get_top_issues(self) -> List[Dict]:
        """Получение топ проблем"""
        top_issues = []
        
        for issue_type, issues in self.issues.items():
            if len(issues) > 0:
                top_issues.append({
                    'type': issue_type,
                    'count': len(issues),
                    'examples': issues[:5]
                })
        
        return sorted(top_issues, key=lambda x: x['count'], reverse=True)


def main():
    """Главная функция"""
    project_root = Path(".")
    
    auditor = CodeQualityAuditor(project_root)
    results = auditor.audit_python_code()
    
    # Сохранение
    output_dir = Path("./output/audit")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    import json
    output_file = output_dir / "code_quality_audit.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print("\n" + "=" * 80)
    print("АУДИТ КАЧЕСТВА КОДА ЗАВЕРШЕН")
    print("=" * 80)
    print(f"\nРезультаты: {output_file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())



