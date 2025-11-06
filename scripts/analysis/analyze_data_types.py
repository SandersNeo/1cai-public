#!/usr/bin/env python3
"""
Статистика использования типов данных
Шаг 4: Статистика использования типов данных

Анализирует:
- Распределение типов данных
- Квалификаторы типов
- Составные типы
- Рекомендации по типизации
"""

import json
import sys
from pathlib import Path
from typing import Dict, List
from collections import Counter, defaultdict

def load_parse_results():
    """Загрузка результатов парсинга"""
    results_file = Path("./output/edt_parser/full_parse_with_metadata.json")
    
    print("Загрузка результатов парсинга...")
    with open(results_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Загружено успешно!")
    return data

def analyze_types_in_catalogs(data: Dict) -> Dict:
    """Анализ типов в справочниках"""
    print("\n" + "=" * 80)
    print("1. ТИПЫ ДАННЫХ В СПРАВОЧНИКАХ")
    print("=" * 80)
    
    type_usage = Counter()
    string_lengths = []
    number_precisions = []
    composite_types = defaultdict(int)
    
    catalogs_with_metadata = 0
    total_attributes = 0
    
    for catalog in data.get('catalogs', []):
        metadata = catalog.get('metadata', {})
        if not metadata:
            continue
        
        catalogs_with_metadata += 1
        
        # Реквизиты
        for attr in metadata.get('attributes', []):
            total_attributes += 1
            type_info = attr.get('type', {})
            types = type_info.get('types', [])
            
            # Подсчет типов
            for type_name in types:
                type_usage[type_name] += 1
            
            # Составные типы
            if len(types) > 1:
                composite_types[len(types)] += 1
            
            # Строковые квалификаторы
            string_qual = type_info.get('string_qualifiers')
            if string_qual and string_qual.get('length'):
                try:
                    length = int(string_qual['length'])
                    string_lengths.append(length)
                except:
                    pass
            
            # Числовые квалификаторы
            number_qual = type_info.get('number_qualifiers')
            if number_qual and number_qual.get('precision'):
                try:
                    precision = int(number_qual['precision'])
                    number_precisions.append(precision)
                except:
                    pass
        
        # Табличные части
        for tab_section in metadata.get('tabular_sections', []):
            for col in tab_section.get('columns', []):
                total_attributes += 1
                type_info = col.get('type', {})
                types = type_info.get('types', [])
                
                for type_name in types:
                    type_usage[type_name] += 1
                
                if len(types) > 1:
                    composite_types[len(types)] += 1
    
    print(f"\nСправочников с метаданными: {catalogs_with_metadata:,}")
    print(f"Всего реквизитов проанализировано: {total_attributes:,}")
    
    print(f"\nТОП-30 используемых типов:")
    for i, (type_name, count) in enumerate(type_usage.most_common(30), 1):
        pct = count / total_attributes * 100 if total_attributes > 0 else 0
        print(f"  {i:2d}. {type_name:<50} {count:>5} ({pct:>5.1f}%)")
    
    if string_lengths:
        avg_str_len = sum(string_lengths) / len(string_lengths)
        max_str_len = max(string_lengths)
        print(f"\nСтроковые типы:")
        print(f"  Средняя длина: {avg_str_len:.0f}")
        print(f"  Максимальная длина: {max_str_len}")
    
    if number_precisions:
        avg_precision = sum(number_precisions) / len(number_precisions)
        max_precision = max(number_precisions)
        print(f"\nЧисловые типы:")
        print(f"  Средняя точность: {avg_precision:.1f}")
        print(f"  Максимальная точность: {max_precision}")
    
    if composite_types:
        print(f"\nСоставные типы:")
        for type_count, usage in sorted(composite_types.items()):
            print(f"  {type_count} типов: {usage:,} реквизитов")
    
    return {
        'catalogs_analyzed': catalogs_with_metadata,
        'total_attributes': total_attributes,
        'type_usage': dict(type_usage),
        'composite_types': dict(composite_types),
        'avg_string_length': sum(string_lengths) / len(string_lengths) if string_lengths else 0,
        'avg_number_precision': sum(number_precisions) / len(number_precisions) if number_precisions else 0
    }

def analyze_types_in_documents(data: Dict) -> Dict:
    """Анализ типов в документах"""
    print("\n" + "=" * 80)
    print("2. ТИПЫ ДАННЫХ В ДОКУМЕНТАХ")
    print("=" * 80)
    
    type_usage = Counter()
    composite_types = defaultdict(int)
    
    docs_with_metadata = 0
    total_attributes = 0
    
    for doc in data.get('documents', []):
        metadata = doc.get('metadata', {})
        if not metadata:
            continue
        
        docs_with_metadata += 1
        
        # Реквизиты
        for attr in metadata.get('attributes', []):
            total_attributes += 1
            type_info = attr.get('type', {})
            types = type_info.get('types', [])
            
            for type_name in types:
                type_usage[type_name] += 1
            
            if len(types) > 1:
                composite_types[len(types)] += 1
        
        # Табличные части
        for tab_section in metadata.get('tabular_sections', []):
            for col in tab_section.get('columns', []):
                total_attributes += 1
                type_info = col.get('type', {})
                types = type_info.get('types', [])
                
                for type_name in types:
                    type_usage[type_name] += 1
                
                if len(types) > 1:
                    composite_types[len(types)] += 1
    
    print(f"\nДокументов с метаданными: {docs_with_metadata:,}")
    print(f"Всего реквизитов проанализировано: {total_attributes:,}")
    
    print(f"\nТОП-30 используемых типов:")
    for i, (type_name, count) in enumerate(type_usage.most_common(30), 1):
        pct = count / total_attributes * 100 if total_attributes > 0 else 0
        print(f"  {i:2d}. {type_name:<50} {count:>5} ({pct:>5.1f}%)")
    
    if composite_types:
        print(f"\nСоставные типы:")
        for type_count, usage in sorted(composite_types.items()):
            print(f"  {type_count} типов: {usage:,} реквизитов")
    
    return {
        'documents_analyzed': docs_with_metadata,
        'total_attributes': total_attributes,
        'type_usage': dict(type_usage),
        'composite_types': dict(composite_types)
    }

def analyze_reference_types(data: Dict) -> Dict:
    """Анализ ссылочных типов"""
    print("\n" + "=" * 80)
    print("3. ССЫЛОЧНЫЕ ТИПЫ")
    print("=" * 80)
    
    catalog_refs = Counter()
    document_refs = Counter()
    
    # Из справочников
    for catalog in data.get('catalogs', []):
        metadata = catalog.get('metadata', {})
        if not metadata:
            continue
        
        for attr in metadata.get('attributes', []):
            types = attr.get('type', {}).get('types', [])
            for type_name in types:
                if 'CatalogRef' in type_name or 'Справочник' in type_name:
                    catalog_refs[type_name] += 1
                elif 'DocumentRef' in type_name or 'Документ' in type_name:
                    document_refs[type_name] += 1
        
        for tab_section in metadata.get('tabular_sections', []):
            for col in tab_section.get('columns', []):
                types = col.get('type', {}).get('types', [])
                for type_name in types:
                    if 'CatalogRef' in type_name or 'Справочник' in type_name:
                        catalog_refs[type_name] += 1
                    elif 'DocumentRef' in type_name or 'Документ' in type_name:
                        document_refs[type_name] += 1
    
    # Из документов
    for doc in data.get('documents', []):
        metadata = doc.get('metadata', {})
        if not metadata:
            continue
        
        for attr in metadata.get('attributes', []):
            types = attr.get('type', {}).get('types', [])
            for type_name in types:
                if 'CatalogRef' in type_name or 'Справочник' in type_name:
                    catalog_refs[type_name] += 1
                elif 'DocumentRef' in type_name or 'Документ' in type_name:
                    document_refs[type_name] += 1
        
        for tab_section in metadata.get('tabular_sections', []):
            for col in tab_section.get('columns', []):
                types = col.get('type', {}).get('types', [])
                for type_name in types:
                    if 'CatalogRef' in type_name or 'Справочник' in type_name:
                        catalog_refs[type_name] += 1
                    elif 'DocumentRef' in type_name or 'Документ' in type_name:
                        document_refs[type_name] += 1
    
    print(f"\nТОП-20 ссылок на справочники:")
    for i, (type_name, count) in enumerate(catalog_refs.most_common(20), 1):
        print(f"  {i:2d}. {type_name:<50} {count:>4} использований")
    
    print(f"\nТОП-20 ссылок на документы:")
    for i, (type_name, count) in enumerate(document_refs.most_common(20), 1):
        print(f"  {i:2d}. {type_name:<50} {count:>4} использований")
    
    return {
        'catalog_refs': dict(catalog_refs),
        'document_refs': dict(document_refs)
    }

def generate_recommendations(catalog_stats: Dict, document_stats: Dict) -> List[str]:
    """Генерация рекомендаций по типизации"""
    print("\n" + "=" * 80)
    print("4. РЕКОМЕНДАЦИИ ПО ТИПИЗАЦИИ")
    print("=" * 80)
    
    recommendations = []
    
    # Анализ составных типов
    catalog_composite = catalog_stats.get('composite_types', {})
    if catalog_composite:
        total_composite = sum(catalog_composite.values())
        total_attrs = catalog_stats.get('total_attributes', 1)
        pct = total_composite / total_attrs * 100
        
        rec = f"Составные типы используются в {total_composite} ({pct:.1f}%) реквизитах справочников"
        recommendations.append(rec)
        print(f"\n• {rec}")
        
        if pct > 30:
            rec = "  [!] Высокий процент составных типов может усложнить поддержку"
            recommendations.append(rec)
            print(rec)
    
    # Проверка типов
    catalog_types = catalog_stats.get('type_usage', {})
    if 'String' in catalog_types or 'Строка' in catalog_types:
        string_count = catalog_types.get('String', 0) + catalog_types.get('Строка', 0)
        total_attrs = catalog_stats.get('total_attributes', 1)
        pct = string_count / total_attrs * 100
        
        rec = f"Строковые типы используются в {pct:.1f}% реквизитов справочников"
        recommendations.append(rec)
        print(f"\n• {rec}")
        
        avg_len = catalog_stats.get('avg_string_length', 0)
        if avg_len > 0:
            rec = f"  Средняя длина строк: {avg_len:.0f} символов"
            recommendations.append(rec)
            print(f"  {rec}")
    
    print(f"\nВсего рекомендаций: {len(recommendations)}")
    
    return recommendations

def main():
    """Главная функция"""
    print("=" * 80)
    print("АНАЛИЗ ТИПОВ ДАННЫХ")
    print("=" * 80)
    
    # Загрузка данных
    data = load_parse_results()
    
    # Анализ
    catalog_stats = analyze_types_in_catalogs(data)
    document_stats = analyze_types_in_documents(data)
    ref_stats = analyze_reference_types(data)
    recommendations = generate_recommendations(catalog_stats, document_stats)
    
    # Сохранение
    output_dir = Path("./output/analysis")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        'catalog_types': catalog_stats,
        'document_types': document_stats,
        'reference_types': ref_stats,
        'recommendations': recommendations
    }
    
    output_file = output_dir / "data_types_analysis.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 80)
    print("АНАЛИЗ ЗАВЕРШЕН!")
    print("=" * 80)
    print(f"\nРезультаты сохранены: {output_file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())



