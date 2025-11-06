#!/usr/bin/env python3
"""
Анализ архитектуры конфигурации 1С
Шаг 1: Анализ архитектуры конфигурации

Анализирует:
- Структуру конфигурации
- Связи между объектами
- Распределение кода
- Сложность модулей
"""

import json
import sys
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Any

def load_parse_results():
    """Загрузка результатов парсинга"""
    results_file = Path("./output/edt_parser/full_parse_with_metadata.json")
    
    print("Загрузка результатов парсинга...")
    print(f"Файл: {results_file}")
    print(f"Размер: {results_file.stat().st_size / 1024 / 1024:.2f} MB")
    
    with open(results_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Загружено успешно!")
    return data

def analyze_module_distribution(data: Dict) -> Dict:
    """Анализ распределения модулей"""
    print("\n" + "=" * 80)
    print("1. РАСПРЕДЕЛЕНИЕ МОДУЛЕЙ ПО ТИПАМ")
    print("=" * 80)
    
    stats = {
        'common_modules': len(data.get('common_modules', [])),
        'catalogs': len(data.get('catalogs', [])),
        'documents': len(data.get('documents', [])),
        'catalog_managers': 0,
        'catalog_objects': 0,
        'document_managers': 0,
        'document_objects': 0
    }
    
    # Подсчет модулей в справочниках
    for catalog in data.get('catalogs', []):
        if catalog.get('manager_module'):
            stats['catalog_managers'] += 1
        if catalog.get('object_module'):
            stats['catalog_objects'] += 1
    
    # Подсчет модулей в документах
    for doc in data.get('documents', []):
        if doc.get('manager_module'):
            stats['document_managers'] += 1
        if doc.get('object_module'):
            stats['document_objects'] += 1
    
    total_modules = (stats['common_modules'] + stats['catalog_managers'] + 
                     stats['catalog_objects'] + stats['document_managers'] + 
                     stats['document_objects'])
    
    print(f"\nОбщих модулей: {stats['common_modules']:,}")
    print(f"\nСправочников: {stats['catalogs']:,}")
    print(f"  - С модулем менеджера: {stats['catalog_managers']:,}")
    print(f"  - С модулем объекта: {stats['catalog_objects']:,}")
    print(f"\nДокументов: {stats['documents']:,}")
    print(f"  - С модулем менеджера: {stats['document_managers']:,}")
    print(f"  - С модулем объекта: {stats['document_objects']:,}")
    print(f"\nВСЕГО МОДУЛЕЙ С КОДОМ: {total_modules:,}")
    
    return stats

def analyze_code_volume(data: Dict) -> Dict:
    """Анализ объема кода"""
    print("\n" + "=" * 80)
    print("2. ОБЪЕМ КОДА")
    print("=" * 80)
    
    volumes = {
        'common_modules': {'total': 0, 'avg': 0, 'max': 0, 'max_name': ''},
        'catalogs': {'total': 0, 'avg': 0, 'max': 0, 'max_name': ''},
        'documents': {'total': 0, 'avg': 0, 'max': 0, 'max_name': ''}
    }
    
    # Общие модули
    for module in data.get('common_modules', []):
        size = module.get('code_length', 0)
        volumes['common_modules']['total'] += size
        if size > volumes['common_modules']['max']:
            volumes['common_modules']['max'] = size
            volumes['common_modules']['max_name'] = module['name']
    
    if data.get('common_modules'):
        volumes['common_modules']['avg'] = volumes['common_modules']['total'] / len(data['common_modules'])
    
    # Справочники
    for catalog in data.get('catalogs', []):
        size = 0
        if catalog.get('manager_module'):
            size += catalog['manager_module'].get('code_length', 0)
        if catalog.get('object_module'):
            size += catalog['object_module'].get('code_length', 0)
        
        volumes['catalogs']['total'] += size
        if size > volumes['catalogs']['max']:
            volumes['catalogs']['max'] = size
            volumes['catalogs']['max_name'] = catalog['name']
    
    if data.get('catalogs'):
        volumes['catalogs']['avg'] = volumes['catalogs']['total'] / len(data['catalogs'])
    
    # Документы
    for doc in data.get('documents', []):
        size = 0
        if doc.get('manager_module'):
            size += doc['manager_module'].get('code_length', 0)
        if doc.get('object_module'):
            size += doc['object_module'].get('code_length', 0)
        
        volumes['documents']['total'] += size
        if size > volumes['documents']['max']:
            volumes['documents']['max'] = size
            volumes['documents']['max_name'] = doc['name']
    
    if data.get('documents'):
        volumes['documents']['avg'] = volumes['documents']['total'] / len(data['documents'])
    
    total_code = (volumes['common_modules']['total'] + 
                  volumes['catalogs']['total'] + 
                  volumes['documents']['total'])
    
    print(f"\nОбщие модули:")
    print(f"  Всего символов: {volumes['common_modules']['total']:,}")
    print(f"  Средний размер: {volumes['common_modules']['avg']:,.0f} символов")
    print(f"  Самый большой: {volumes['common_modules']['max_name']} ({volumes['common_modules']['max']:,} символов)")
    
    print(f"\nСправочники:")
    print(f"  Всего символов: {volumes['catalogs']['total']:,}")
    print(f"  Средний размер: {volumes['catalogs']['avg']:,.0f} символов")
    print(f"  Самый большой: {volumes['catalogs']['max_name']} ({volumes['catalogs']['max']:,} символов)")
    
    print(f"\nДокументы:")
    print(f"  Всего символов: {volumes['documents']['total']:,}")
    print(f"  Средний размер: {volumes['documents']['avg']:,.0f} символов")
    print(f"  Самый большой: {volumes['documents']['max_name']} ({volumes['documents']['max']:,} символов)")
    
    print(f"\nВСЕГО СИМВОЛОВ КОДА: {total_code:,}")
    print(f"Примерно страниц текста: {total_code / 4000:,.0f}")
    print(f"Примерно книг по 300 страниц: {total_code / 4000 / 300:,.0f}")
    
    return volumes

def analyze_complexity(data: Dict) -> Dict:
    """Анализ сложности кода"""
    print("\n" + "=" * 80)
    print("3. СЛОЖНОСТЬ КОДА")
    print("=" * 80)
    
    total_functions = 0
    total_procedures = 0
    total_params = 0
    export_functions = 0
    
    # Из общих модулей
    for module in data.get('common_modules', []):
        functions = module.get('functions', [])
        procedures = module.get('procedures', [])
        
        total_functions += len(functions)
        total_procedures += len(procedures)
        
        for func in functions:
            total_params += len(func.get('parameters', []))
            if func.get('is_export'):
                export_functions += 1
        
        for proc in procedures:
            total_params += len(proc.get('parameters', []))
    
    # Из справочников
    for catalog in data.get('catalogs', []):
        for module_key in ['manager_module', 'object_module']:
            module = catalog.get(module_key)
            if not module:
                continue
            
            total_functions += module.get('functions_count', 0)
            total_procedures += module.get('procedures_count', 0)
    
    # Из документов
    for doc in data.get('documents', []):
        for module_key in ['manager_module', 'object_module']:
            module = doc.get(module_key)
            if not module:
                continue
            
            total_functions += module.get('functions_count', 0)
            total_procedures += module.get('procedures_count', 0)
    
    total_methods = total_functions + total_procedures
    avg_params = total_params / total_methods if total_methods > 0 else 0
    
    print(f"\nВсего методов: {total_methods:,}")
    print(f"  Функций: {total_functions:,}")
    print(f"  Процедур: {total_procedures:,}")
    print(f"\nЭкспортных функций: {export_functions:,} ({export_functions/total_functions*100:.1f}%)")
    print(f"\nСредне параметров на метод: {avg_params:.2f}")
    
    return {
        'total_methods': total_methods,
        'functions': total_functions,
        'procedures': total_procedures,
        'export_functions': export_functions,
        'avg_params': avg_params
    }

def analyze_metadata_structure(data: Dict) -> Dict:
    """Анализ структуры метаданных"""
    print("\n" + "=" * 80)
    print("4. СТРУКТУРА МЕТАДАННЫХ")
    print("=" * 80)
    
    # Справочники
    catalog_stats = {
        'total': len(data.get('catalogs', [])),
        'with_metadata': 0,
        'hierarchical': 0,
        'total_attributes': 0,
        'total_tabular_sections': 0,
        'avg_attributes': 0,
        'avg_tabular_sections': 0
    }
    
    for catalog in data.get('catalogs', []):
        metadata = catalog.get('metadata')
        if metadata:
            catalog_stats['with_metadata'] += 1
            if metadata.get('hierarchical'):
                catalog_stats['hierarchical'] += 1
            catalog_stats['total_attributes'] += len(metadata.get('attributes', []))
            catalog_stats['total_tabular_sections'] += len(metadata.get('tabular_sections', []))
    
    if catalog_stats['with_metadata'] > 0:
        catalog_stats['avg_attributes'] = catalog_stats['total_attributes'] / catalog_stats['with_metadata']
        catalog_stats['avg_tabular_sections'] = catalog_stats['total_tabular_sections'] / catalog_stats['with_metadata']
    
    # Документы
    doc_stats = {
        'total': len(data.get('documents', [])),
        'with_metadata': 0,
        'with_posting': 0,
        'total_attributes': 0,
        'total_tabular_sections': 0,
        'avg_attributes': 0,
        'avg_tabular_sections': 0
    }
    
    for doc in data.get('documents', []):
        metadata = doc.get('metadata')
        if metadata:
            doc_stats['with_metadata'] += 1
            if metadata.get('posting'):
                doc_stats['with_posting'] += 1
            doc_stats['total_attributes'] += len(metadata.get('attributes', []))
            doc_stats['total_tabular_sections'] += len(metadata.get('tabular_sections', []))
    
    if doc_stats['with_metadata'] > 0:
        doc_stats['avg_attributes'] = doc_stats['total_attributes'] / doc_stats['with_metadata']
        doc_stats['avg_tabular_sections'] = doc_stats['total_tabular_sections'] / doc_stats['with_metadata']
    
    print(f"\nСПРАВОЧНИКИ:")
    print(f"  Всего: {catalog_stats['total']:,}")
    print(f"  С метаданными: {catalog_stats['with_metadata']:,}")
    print(f"  Иерархических: {catalog_stats['hierarchical']:,}")
    print(f"  Всего реквизитов: {catalog_stats['total_attributes']:,}")
    print(f"  Средне реквизитов: {catalog_stats['avg_attributes']:.1f}")
    print(f"  Всего табл. частей: {catalog_stats['total_tabular_sections']:,}")
    print(f"  Средне табл. частей: {catalog_stats['avg_tabular_sections']:.2f}")
    
    print(f"\nДОКУМЕНТЫ:")
    print(f"  Всего: {doc_stats['total']:,}")
    print(f"  С метаданными: {doc_stats['with_metadata']:,}")
    print(f"  С проведением: {doc_stats['with_posting']:,}")
    print(f"  Всего реквизитов: {doc_stats['total_attributes']:,}")
    print(f"  Средне реквизитов: {doc_stats['avg_attributes']:.1f}")
    print(f"  Всего табл. частей: {doc_stats['total_tabular_sections']:,}")
    print(f"  Средне табл. частей: {doc_stats['avg_tabular_sections']:.2f}")
    
    return {'catalogs': catalog_stats, 'documents': doc_stats}

def analyze_top_modules(data: Dict) -> List[Dict]:
    """Топ модулей по различным метрикам"""
    print("\n" + "=" * 80)
    print("5. ТОП МОДУЛЕЙ")
    print("=" * 80)
    
    modules_info = []
    
    for module in data.get('common_modules', []):
        modules_info.append({
            'name': module['name'],
            'type': 'CommonModule',
            'code_length': module.get('code_length', 0),
            'functions': module.get('functions_count', 0),
            'procedures': module.get('procedures_count', 0),
            'total_methods': module.get('functions_count', 0) + module.get('procedures_count', 0)
        })
    
    # ТОП по размеру кода
    print("\nТОП-10 по размеру кода:")
    top_by_size = sorted(modules_info, key=lambda x: x['code_length'], reverse=True)[:10]
    for i, mod in enumerate(top_by_size, 1):
        print(f"  {i:2d}. {mod['name']:<50} {mod['code_length']:>8,} символов")
    
    # ТОП по количеству методов
    print("\nТОП-10 по количеству методов:")
    top_by_methods = sorted(modules_info, key=lambda x: x['total_methods'], reverse=True)[:10]
    for i, mod in enumerate(top_by_methods, 1):
        print(f"  {i:2d}. {mod['name']:<50} {mod['total_methods']:>4} методов")
    
    # ТОП по количеству функций
    print("\nТОП-10 по количеству функций:")
    top_by_funcs = sorted(modules_info, key=lambda x: x['functions'], reverse=True)[:10]
    for i, mod in enumerate(top_by_funcs, 1):
        print(f"  {i:2d}. {mod['name']:<50} {mod['functions']:>4} функций")
    
    return modules_info

def main():
    """Главная функция"""
    print("=" * 80)
    print("АНАЛИЗ АРХИТЕКТУРЫ КОНФИГУРАЦИИ ERPCPM")
    print("=" * 80)
    
    # Загрузка данных
    data = load_parse_results()
    
    # Анализ
    results = {}
    
    results['distribution'] = analyze_module_distribution(data)
    results['volume'] = analyze_code_volume(data)
    results['complexity'] = analyze_complexity(data)
    results['metadata'] = analyze_metadata_structure(data)
    results['top_modules'] = analyze_top_modules(data)
    
    # Сохранение результатов
    output_file = Path("./output/analysis/architecture_analysis.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 80)
    print("АНАЛИЗ ЗАВЕРШЕН")
    print("=" * 80)
    print(f"\nРезультаты сохранены: {output_file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())



