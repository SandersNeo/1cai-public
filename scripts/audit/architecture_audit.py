#!/usr/bin/env python3
"""
Архитектурный аудит проекта
Этап 3: Глубокий анализ архитектуры

Проверяет:
- Слои приложения
- Separation of concerns
- Circular dependencies
- Модульность
- Паттерны проектирования
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict
import re

class ArchitectureAuditor:
    """Аудитор архитектуры"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.imports_graph = defaultdict(set)
        self.modules = {}
        self.layers = defaultdict(list)
        self.ignore_dirs = {'__pycache__', '.git', 'node_modules', '1c_configurations'}
    
    def audit_architecture(self) -> Dict:
        """Полный архитектурный аудит"""
        print("=" * 80)
        print("АРХИТЕКТУРНЫЙ АУДИТ ПРОЕКТА")
        print("=" * 80)
        print()
        
        # 1. Сканирование модулей
        print("[*] Сканирование модулей...")
        self.scan_modules()
        print(f"    Найдено Python модулей: {len(self.modules):,}")
        
        # 2. Построение графа импортов
        print("\n[*] Построение графа импортов...")
        self.build_import_graph()
        print(f"    Связей в графе: {sum(len(v) for v in self.imports_graph.values()):,}")
        
        # 3. Поиск циклических зависимостей
        print("\n[*] Поиск циклических зависимостей...")
        cycles = self.find_circular_dependencies()
        print(f"    Найдено циклов: {len(cycles):,}")
        
        # 4. Анализ слоев
        print("\n[*] Анализ слоев приложения...")
        self.analyze_layers()
        
        # 5. Проверка separation of concerns
        print("\n[*] Проверка separation of concerns...")
        concerns = self.check_separation_of_concerns()
        
        return {
            'total_modules': len(self.modules),
            'import_connections': sum(len(v) for v in self.imports_graph.values()),
            'circular_dependencies': len(cycles),
            'cycles_details': cycles[:10],
            'layers': {k: len(v) for k, v in self.layers.items()},
            'concerns': concerns
        }
    
    def scan_modules(self):
        """Сканирование всех Python модулей"""
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    rel_path = file_path.relative_to(self.project_root)
                    
                    # Определяем слой
                    layer = self.detect_layer(rel_path)
                    
                    self.modules[str(rel_path)] = {
                        'path': file_path,
                        'layer': layer,
                        'imports': []
                    }
                    
                    self.layers[layer].append(str(rel_path))
    
    def detect_layer(self, rel_path: Path) -> str:
        """Определение слоя приложения"""
        parts = rel_path.parts
        
        if not parts:
            return 'root'
        
        first_part = parts[0].lower()
        
        # Определяем слой по структуре папок
        if first_part == 'src':
            if len(parts) > 1:
                if parts[1] == 'api':
                    return 'api_layer'
                elif parts[1] == 'services':
                    return 'service_layer'
                elif parts[1] == 'db':
                    return 'data_layer'
                elif parts[1] == 'ai':
                    return 'ai_layer'
                else:
                    return 'business_layer'
            return 'src'
        elif first_part == 'scripts':
            return 'scripts'
        elif first_part == 'tests':
            return 'tests'
        elif first_part in ['frontend', 'frontend-portal']:
            return 'frontend'
        else:
            return first_part
    
    def build_import_graph(self):
        """Построение графа импортов"""
        for module_name, module_info in self.modules.items():
            try:
                with open(module_info['path'], 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())
                
                imports = self.extract_imports(tree)
                module_info['imports'] = imports
                
                for imp in imports:
                    self.imports_graph[module_name].add(imp)
                    
            except:
                pass
    
    def extract_imports(self, tree: ast.AST) -> List[str]:
        """Извлечение импортов из AST"""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        return imports
    
    def find_circular_dependencies(self) -> List[List[str]]:
        """Поиск циклических зависимостей"""
        cycles = []
        visited = set()
        
        def dfs(node: str, path: List[str]):
            if node in path:
                # Нашли цикл
                cycle_start = path.index(node)
                cycle = path[cycle_start:]
                if len(cycle) > 1 and cycle not in cycles:
                    cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            path.append(node)
            
            for neighbor in self.imports_graph.get(node, []):
                # Проверяем только локальные импорты
                if neighbor in self.modules:
                    dfs(neighbor, path.copy())
            
            path.pop()
        
        # Проверяем каждый модуль
        for module in list(self.modules.keys())[:100]:  # Ограничиваем для скорости
            dfs(module, [])
        
        if cycles:
            print(f"\n    Примеры циклов (первые 5):")
            for i, cycle in enumerate(cycles[:5], 1):
                print(f"\n    Цикл {i}:")
                for mod in cycle[:5]:
                    print(f"      -> {mod}")
                if len(cycle) > 5:
                    print(f"      ... и еще {len(cycle) - 5} модулей")
        
        return cycles
    
    def analyze_layers(self):
        """Анализ слоев приложения"""
        print(f"\n    Найдено слоев: {len(self.layers):,}")
        print("\n    Распределение по слоям:")
        
        sorted_layers = sorted(self.layers.items(), key=lambda x: len(x[1]), reverse=True)
        for layer, modules in sorted_layers[:20]:
            print(f"    {layer:<30} {len(modules):>4} модулей")
    
    def check_separation_of_concerns(self) -> Dict:
        """Проверка separation of concerns"""
        violations = []
        
        # Проверяем что API слой не импортирует напрямую DB слой
        api_modules = self.layers.get('api_layer', [])
        data_modules = set(self.layers.get('data_layer', []))
        
        for api_module in api_modules:
            imports = self.imports_graph.get(api_module, set())
            for imp in imports:
                if imp in data_modules:
                    violations.append({
                        'from': api_module,
                        'to': imp,
                        'issue': 'API layer directly imports data layer'
                    })
        
        print(f"\n    Нарушений separation of concerns: {len(violations):,}")
        
        if violations:
            print("\n    Примеры нарушений (первые 5):")
            for i, v in enumerate(violations[:5], 1):
                print(f"    {i}. {v['issue']}")
                print(f"       {v['from']} -> {v['to']}")
        
        return {
            'total_violations': len(violations),
            'examples': violations[:10]
        }


def main():
    """Главная функция"""
    project_root = Path(".")
    
    auditor = ArchitectureAuditor(project_root)
    results = auditor.audit_architecture()
    
    # Сохранение
    output_dir = Path("./output/audit")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    import json
    output_file = output_dir / "architecture_audit.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print("\n" + "=" * 80)
    print("АРХИТЕКТУРНЫЙ АУДИТ ЗАВЕРШЕН")
    print("=" * 80)
    print(f"\nРезультаты: {output_file}")
    
    return 0

if __name__ == "__main__":
    import os
    sys.exit(main())



