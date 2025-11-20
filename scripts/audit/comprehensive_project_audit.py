# [NEXUS IDENTITY] ID: -5753451079017531887 | DATE: 2025-11-19

#!/usr/bin/env python3
"""
Комплексный аудит всего проекта
Этапы 4-9: Быстрый комплексный аудит

Проверяет:
- Зависимости (requirements)
- Тесты
- Документацию
- Конфигурацию
- Безопасность
- Технический долг
"""

import os
import sys
import re
import json
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List

class ComprehensiveProjectAuditor:
    """Комплексный аудитор проекта"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.findings = defaultdict(list)
        self.stats = defaultdict(int)
    
    def run_full_audit(self) -> Dict:
        """Полный аудит проекта"""
        print("=" * 80)
        print("КОМПЛЕКСНЫЙ АУДИТ ПРОЕКТА")
        print("=" * 80)
        print()
        
        results = {}
        
        # Этап 4: Зависимости
        print("[ЭТАП 4] Анализ зависимостей...")
        results['dependencies'] = self.audit_dependencies()
        
        # Этап 5: Тесты
        print("\n[ЭТАП 5] Проверка тестов...")
        results['tests'] = self.audit_tests()
        
        # Этап 6: Документация
        print("\n[ЭТАП 6] Аудит документации...")
        results['documentation'] = self.audit_documentation()
        
        # Этап 7: Конфигурация
        print("\n[ЭТАП 7] Анализ конфигурации...")
        results['configuration'] = self.audit_configuration()
        
        # Этап 8: Безопасность
        print("\n[ЭТАП 8] Проверка безопасности...")
        results['security'] = self.audit_security()
        
        # Этап 9: Технический долг
        print("\n[ЭТАП 9] Поиск технического долга...")
        results['technical_debt'] = self.audit_technical_debt()
        
        return results
    
    def audit_dependencies(self) -> Dict:
        """Аудит зависимостей"""
        results = {
            'requirements_files': [],
            'total_dependencies': 0,
            'unique_packages': set()
        }
        
        # Ищем requirements файлы
        for file in self.project_root.glob('requirements*.txt'):
            with open(file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            deps = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Извлекаем имя пакета
                    pkg_name = re.split(r'[=<>~!]', line)[0].strip()
                    deps.append(line)
                    results['unique_packages'].add(pkg_name)
            
            results['requirements_files'].append({
                'file': file.name,
                'dependencies': len(deps),
                'examples': deps[:5]
            })
            results['total_dependencies'] += len(deps)
        
        print(f"  Requirements файлов: {len(results['requirements_files'])}")
        print(f"  Всего зависимостей: {results['total_dependencies']}")
        print(f"  Уникальных пакетов: {len(results['unique_packages'])}")
        
        if results['requirements_files']:
            print("\n  Найденные файлы:")
            for rf in results['requirements_files']:
                print(f"    - {rf['file']}: {rf['dependencies']} зависимостей")
        
        results['unique_packages'] = list(results['unique_packages'])
        return results
    
    def audit_tests(self) -> Dict:
        """Аудит тестов"""
        test_files = list(self.project_root.glob('**/test_*.py'))
        test_dirs = list(self.project_root.glob('**/tests'))
        
        # Подсчет тестов
        total_test_functions = 0
        
        for test_file in test_files[:50]:  # Ограничиваем для скорости
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Подсчет тестовых функций
                test_funcs = len(re.findall(r'def test_', content))
                total_test_functions += test_funcs
            except:
                pass
        
        results = {
            'test_files': len(test_files),
            'test_directories': len(test_dirs),
            'estimated_test_functions': total_test_functions,
            'coverage': 'unknown'
        }
        
        print(f"  Тестовых файлов: {len(test_files)}")
        print(f"  Тестовых директорий: {len(test_dirs)}")
        print(f"  Тестовых функций (оценка): {total_test_functions}")
        
        return results
    
    def audit_documentation(self) -> Dict:
        """Аудит документации"""
        # README файлы
        readme_files = list(self.project_root.glob('**/README.md'))
        
        # Markdown файлы
        md_files = []
        for root, dirs, files in os.walk(self.project_root):
            if '1c_configurations' in root or '__pycache__' in root:
                continue
            for file in files:
                if file.endswith('.md'):
                    md_files.append(Path(root) / file)
        
        # Анализ размера документации
        total_doc_size = 0
        for md_file in md_files:
            try:
                total_doc_size += md_file.stat().st_size
            except:
                pass
        
        results = {
            'readme_files': len(readme_files),
            'total_md_files': len(md_files),
            'total_doc_size_mb': total_doc_size / 1024 / 1024
        }
        
        print(f"  README файлов: {len(readme_files)}")
        print(f"  Всего .md файлов: {len(md_files)}")
        print(f"  Размер документации: {total_doc_size / 1024 / 1024:.2f} MB")
        
        return results
    
    def audit_configuration(self) -> Dict:
        """Аудит конфигурационных файлов"""
        results = {
            'docker_compose_files': [],
            'dockerfiles': [],
            'config_files': []
        }
        
        # Docker compose файлы
        for file in self.project_root.glob('docker-compose*.yml'):
            results['docker_compose_files'].append(file.name)
        
        # Dockerfiles
        for file in self.project_root.glob('**/Dockerfile*'):
            if '1c_configurations' not in str(file):
                results['dockerfiles'].append(str(file.relative_to(self.project_root)))
        
        # Config файлы
        for file in self.project_root.glob('*.ini'):
            results['config_files'].append(file.name)
        
        print(f"  Docker compose файлов: {len(results['docker_compose_files'])}")
        print(f"  Dockerfiles: {len(results['dockerfiles'])}")
        print(f"  Config файлов (.ini): {len(results['config_files'])}")
        
        return results
    
    def audit_security(self) -> Dict:
        """Аудит безопасности"""
        results = {
            'potential_secrets': [],
            'sql_injection_risks': [],
            'hardcoded_ips': []
        }
        
        # Паттерны для поиска
        secret_patterns = [
            (r'password\s*=\s*["\'](?!.*\{)[^"\']+["\']', 'hardcoded_password'),
            (r'api[_-]?key\s*=\s*["\'](?!.*\{)[^"\']+["\']', 'hardcoded_api_key'),
            (r'secret\s*=\s*["\'](?!.*\{)[^"\']+["\']', 'hardcoded_secret'),
        ]
        
        # Проверяем Python файлы
        py_files = list(self.project_root.glob('**/*.py'))
        
        for py_file in py_files[:200]:  # Ограничиваем для скорости
            if '1c_configurations' in str(py_file) or '__pycache__' in str(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern, issue_type in secret_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        results['potential_secrets'].append({
                            'file': str(py_file.relative_to(self.project_root)),
                            'type': issue_type,
                            'count': len(matches)
                        })
                
                # Проверка SQL injection
                if re.search(r'execute\s*\([^)]*%|execute\s*\([^)]*\+', content):
                    results['sql_injection_risks'].append(str(py_file.relative_to(self.project_root)))
                
                # Hardcoded IPs
                ip_matches = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', content)
                if ip_matches:
                    # Исключаем localhost и 0.0.0.0
                    filtered_ips = [ip for ip in ip_matches if ip not in ['127.0.0.1', '0.0.0.0']]
                    if filtered_ips:
                        results['hardcoded_ips'].append({
                            'file': str(py_file.relative_to(self.project_root)),
                            'ips': list(set(filtered_ips))
                        })
            except:
                pass
        
        print(f"  Потенциальных секретов: {len(results['potential_secrets'])}")
        print(f"  SQL injection рисков: {len(results['sql_injection_risks'])}")
        print(f"  Hardcoded IPs: {len(results['hardcoded_ips'])}")
        
        return results
    
    def audit_technical_debt(self) -> Dict:
        """Аудит технического долга"""
        results = {
            'todo_count': 0,
            'fixme_count': 0,
            'hack_count': 0,
            'xxx_count': 0,
            'deprecated_count': 0,
            'examples': []
        }
        
        # Поиск TODO, FIXME, и т.д.
        py_files = list(self.project_root.glob('**/*.py'))
        
        for py_file in py_files[:300]:  # Ограничиваем
            if '1c_configurations' in str(py_file) or '__pycache__' in str(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # TODO
                todos = len(re.findall(r'#\s*TODO', content, re.IGNORECASE))
                if todos > 0:
                    results['todo_count'] += todos
                    if len(results['examples']) < 10:
                        results['examples'].append({
                            'file': str(py_file.relative_to(self.project_root)),
                            'type': 'TODO',
                            'count': todos
                        })
                
                # FIXME
                fixmes = len(re.findall(r'#\s*FIXME', content, re.IGNORECASE))
                results['fixme_count'] += fixmes
                
                # HACK
                hacks = len(re.findall(r'#\s*HACK', content, re.IGNORECASE))
                results['hack_count'] += hacks
                
                # XXX
                xxxs = len(re.findall(r'#\s*XXX', content, re.IGNORECASE))
                results['xxx_count'] += xxxs
                
                # Deprecated
                deprecated = len(re.findall(r'@deprecated|# deprecated', content, re.IGNORECASE))
                results['deprecated_count'] += deprecated
                
            except:
                pass
        
        total_debt = (results['todo_count'] + results['fixme_count'] + 
                      results['hack_count'] + results['xxx_count'])
        
        print(f"  TODO: {results['todo_count']}")
        print(f"  FIXME: {results['fixme_count']}")
        print(f"  HACK: {results['hack_count']}")
        print(f"  XXX: {results['xxx_count']}")
        print(f"  Deprecated: {results['deprecated_count']}")
        print(f"  ИТОГО маркеров: {total_debt}")
        
        return results


def main():
    """Главная функция"""
    project_root = Path(".")
    
    auditor = ComprehensiveProjectAuditor(project_root)
    results = auditor.run_full_audit()
    
    # Сохранение
    output_dir = Path("./output/audit")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "comprehensive_audit.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print("\n" + "=" * 80)
    print("КОМПЛЕКСНЫЙ АУДИТ ЗАВЕРШЕН")
    print("=" * 80)
    print(f"\nРезультаты: {output_file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

