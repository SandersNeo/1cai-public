#!/usr/bin/env python3
"""
Анализ зависимостей между объектами
Шаг 3: Поиск зависимостей между объектами

Анализирует:
- Ссылки между справочниками и документами
- Использование API
- Вызовы методов
- Граф зависимостей
"""

import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict, Counter

def load_parse_results():
    """Загрузка результатов парсинга"""
    results_file = Path("./output/edt_parser/full_parse_with_metadata.json")
    
    print("Загрузка результатов парсинга...")
    with open(results_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Загружено успешно!")
    return data

def extract_catalog_references(code: str) -> Set[str]:
    """Извлечение ссылок на справочники из кода"""
    # Паттерны для поиска ссылок
    patterns = [
        r'Справочники\.(\w+)',
        r'Справочник\.(\w+)',
        r'CatalogRef\.(\w+)',
        r'Catalog\.(\w+)'
    ]
    
    refs = set()
    for pattern in patterns:
        matches = re.findall(pattern, code, re.IGNORECASE)
        refs.update(matches)
    
    return refs

def extract_document_references(code: str) -> Set[str]:
    """Извлечение ссылок на документы из кода"""
    patterns = [
        r'Документы\.(\w+)',
        r'Документ\.(\w+)',
        r'DocumentRef\.(\w+)',
        r'Document\.(\w+)'
    ]
    
    refs = set()
    for pattern in patterns:
        matches = re.findall(pattern, code, re.IGNORECASE)
        refs.update(matches)
    
    return refs

def extract_register_references(code: str) -> Set[str]:
    """Извлечение ссылок на регистры из кода"""
    patterns = [
        r'РегистрыСведений\.(\w+)',
        r'РегистрыНакопления\.(\w+)',
        r'InformationRegister\.(\w+)',
        r'AccumulationRegister\.(\w+)'
    ]
    
    refs = set()
    for pattern in patterns:
        matches = re.findall(pattern, code, re.IGNORECASE)
        refs.update(matches)
    
    return refs

def analyze_module_dependencies(module: Dict, module_name: str) -> Dict:
    """Анализ зависимостей одного модуля"""
    code_parts = []
    
    # Собираем код
    if 'code' in module:
        code_parts.append(module['code'])
    
    for func in module.get('functions', []):
        if 'body' in func:
            code_parts.append(func['body'])
    
    for proc in module.get('procedures', []):
        if 'body' in proc:
            code_parts.append(proc['body'])
    
    full_code = '\n'.join(code_parts)
    
    # Извлекаем зависимости
    deps = {
        'module_name': module_name,
        'catalogs': list(extract_catalog_references(full_code)),
        'documents': list(extract_document_references(full_code)),
        'registers': list(extract_register_references(full_code))
    }
    
    return deps

def analyze_object_dependencies(obj: Dict, obj_name: str, obj_type: str) -> Dict:
    """Анализ зависимостей объекта (справочника/документа)"""
    deps = {
        'object_name': obj_name,
        'object_type': obj_type,
        'metadata_refs': {
            'catalogs': [],
            'documents': []
        },
        'code_refs': {
            'catalogs': set(),
            'documents': set(),
            'registers': set()
        }
    }
    
    # Из метаданных
    metadata = obj.get('metadata', {})
    if metadata:
        # Реквизиты
        for attr in metadata.get('attributes', []):
            types = attr.get('type', {}).get('types', [])
            for type_name in types:
                if 'CatalogRef.' in type_name:
                    catalog_name = type_name.replace('CatalogRef.', '').replace('Справочник.', '')
                    deps['metadata_refs']['catalogs'].append(catalog_name)
                elif 'DocumentRef.' in type_name:
                    doc_name = type_name.replace('DocumentRef.', '').replace('Документ.', '')
                    deps['metadata_refs']['documents'].append(doc_name)
        
        # Табличные части
        for tab_section in metadata.get('tabular_sections', []):
            for col in tab_section.get('columns', []):
                types = col.get('type', {}).get('types', [])
                for type_name in types:
                    if 'CatalogRef.' in type_name:
                        catalog_name = type_name.replace('CatalogRef.', '').replace('Справочник.', '')
                        deps['metadata_refs']['catalogs'].append(catalog_name)
                    elif 'DocumentRef.' in type_name:
                        doc_name = type_name.replace('DocumentRef.', '').replace('Документ.', '')
                        deps['metadata_refs']['documents'].append(doc_name)
    
    # Из кода
    code_parts = []
    
    for module_key in ['manager_module', 'object_module']:
        module = obj.get(module_key)
        if not module:
            continue
        
        if 'code' in module:
            code_parts.append(module['code'])
        
        for func in module.get('functions', []):
            if 'body' in func:
                code_parts.append(func['body'])
    
    if code_parts:
        full_code = '\n'.join(code_parts)
        deps['code_refs']['catalogs'] = extract_catalog_references(full_code)
        deps['code_refs']['documents'] = extract_document_references(full_code)
        deps['code_refs']['registers'] = extract_register_references(full_code)
    
    # Преобразуем sets в lists
    deps['code_refs']['catalogs'] = list(deps['code_refs']['catalogs'])
    deps['code_refs']['documents'] = list(deps['code_refs']['documents'])
    deps['code_refs']['registers'] = list(deps['code_refs']['registers'])
    
    return deps

def build_dependency_graph(data: Dict) -> Dict:
    """Построение графа зависимостей"""
    print("\n" + "=" * 80)
    print("ПОСТРОЕНИЕ ГРАФА ЗАВИСИМОСТЕЙ")
    print("=" * 80)
    
    graph = {
        'nodes': [],
        'edges': []
    }
    
    all_deps = []
    
    # Общие модули
    print("\nАнализ общих модулей...")
    for module in data.get('common_modules', [])[:100]:  # Берем 100 для начала
        deps = analyze_module_dependencies(module, module['name'])
        all_deps.append(deps)
        
        graph['nodes'].append({
            'name': module['name'],
            'type': 'CommonModule'
        })
    
    # Справочники
    print("Анализ справочников...")
    for catalog in data.get('catalogs', []):
        deps = analyze_object_dependencies(catalog, catalog['name'], 'Catalog')
        all_deps.append(deps)
        
        graph['nodes'].append({
            'name': catalog['name'],
            'type': 'Catalog'
        })
        
        # Добавляем ребра из метаданных
        for ref_catalog in set(deps['metadata_refs']['catalogs']):
            graph['edges'].append({
                'from': catalog['name'],
                'to': ref_catalog,
                'type': 'metadata_ref',
                'ref_type': 'catalog'
            })
        
        for ref_doc in set(deps['metadata_refs']['documents']):
            graph['edges'].append({
                'from': catalog['name'],
                'to': ref_doc,
                'type': 'metadata_ref',
                'ref_type': 'document'
            })
    
    # Документы
    print("Анализ документов...")
    for doc in data.get('documents', []):
        deps = analyze_object_dependencies(doc, doc['name'], 'Document')
        all_deps.append(deps)
        
        graph['nodes'].append({
            'name': doc['name'],
            'type': 'Document'
        })
        
        # Добавляем ребра из метаданных
        for ref_catalog in set(deps['metadata_refs']['catalogs']):
            graph['edges'].append({
                'from': doc['name'],
                'to': ref_catalog,
                'type': 'metadata_ref',
                'ref_type': 'catalog'
            })
    
    print(f"\nУзлов в графе: {len(graph['nodes']):,}")
    print(f"Ребер в графе: {len(graph['edges']):,}")
    
    return graph, all_deps

def analyze_dependencies_stats(all_deps: List[Dict]) -> Dict:
    """Статистика зависимостей"""
    print("\n" + "=" * 80)
    print("СТАТИСТИКА ЗАВИСИМОСТЕЙ")
    print("=" * 80)
    
    # Подсчет использования справочников
    catalog_usage = Counter()
    document_usage = Counter()
    register_usage = Counter()
    
    for deps in all_deps:
        if 'metadata_refs' in deps:
            catalog_usage.update(deps['metadata_refs']['catalogs'])
            document_usage.update(deps['metadata_refs']['documents'])
        
        if 'code_refs' in deps:
            catalog_usage.update(deps['code_refs']['catalogs'])
            document_usage.update(deps['code_refs']['documents'])
            register_usage.update(deps['code_refs']['registers'])
        
        if 'catalogs' in deps:
            catalog_usage.update(deps['catalogs'])
        if 'documents' in deps:
            document_usage.update(deps['documents'])
        if 'registers' in deps:
            register_usage.update(deps['registers'])
    
    print("\nТОП-20 самых используемых справочников:")
    for i, (name, count) in enumerate(catalog_usage.most_common(20), 1):
        print(f"  {i:2d}. {name:<50} {count:>4} ссылок")
    
    print("\nТОП-20 самых используемых документов:")
    for i, (name, count) in enumerate(document_usage.most_common(20), 1):
        print(f"  {i:2d}. {name:<50} {count:>4} ссылок")
    
    print("\nТОП-20 самых используемых регистров:")
    for i, (name, count) in enumerate(register_usage.most_common(20), 1):
        print(f"  {i:2d}. {name:<50} {count:>4} ссылок")
    
    return {
        'catalog_usage': dict(catalog_usage),
        'document_usage': dict(document_usage),
        'register_usage': dict(register_usage)
    }

def main():
    """Главная функция"""
    print("=" * 80)
    print("АНАЛИЗ ЗАВИСИМОСТЕЙ")
    print("=" * 80)
    
    # Загрузка данных
    data = load_parse_results()
    
    # Построение графа
    graph, all_deps = build_dependency_graph(data)
    
    # Статистика
    stats = analyze_dependencies_stats(all_deps)
    
    # Сохранение
    output_dir = Path("./output/analysis")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Граф зависимостей
    graph_file = output_dir / "dependency_graph.json"
    with open(graph_file, 'w', encoding='utf-8') as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)
    print(f"\nГраф сохранен: {graph_file}")
    
    # Все зависимости
    deps_file = output_dir / "all_dependencies.json"
    with open(deps_file, 'w', encoding='utf-8') as f:
        json.dump(all_deps, f, ensure_ascii=False, indent=2)
    print(f"Зависимости сохранены: {deps_file}")
    
    # Статистика
    stats_file = output_dir / "dependencies_statistics.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"Статистика сохранена: {stats_file}")
    
    print("\n" + "=" * 80)
    print("АНАЛИЗ ЗАВЕРШЕН!")
    print("=" * 80)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())



