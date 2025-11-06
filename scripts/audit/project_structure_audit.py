#!/usr/bin/env python3
"""
Полный структурный аудит проекта
Этап 1: Глубокий анализ структуры проекта

Анализирует:
- Все директории и файлы
- Размеры и типы файлов
- Организацию кода
- Дублирующиеся файлы
"""

import os
import sys
from pathlib import Path
from collections import defaultdict, Counter
import hashlib
from typing import Dict, List, Tuple

class ProjectStructureAuditor:
    """Аудитор структуры проекта"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.stats = defaultdict(int)
        self.file_types = defaultdict(int)
        self.file_sizes = defaultdict(list)
        self.duplicates = defaultdict(list)
        self.large_files = []
        
        # Игнорируемые папки
        self.ignore_dirs = {
            '__pycache__', '.git', 'node_modules', '.next', 
            'dist', 'build', '.cache', '.pytest_cache',
            '1c_configurations'  # Уже проанализировано
        }
    
    def audit_full_structure(self) -> Dict:
        """Полный аудит структуры"""
        print("=" * 80)
        print("ПОЛНЫЙ СТРУКТУРНЫЙ АУДИТ ПРОЕКТА")
        print("=" * 80)
        print(f"Корень проекта: {self.project_root}")
        print()
        
        # 1. Сканирование всех файлов
        print("[*] Сканирование файлов...")
        all_files = self.scan_all_files()
        print(f"    Найдено файлов: {len(all_files):,}")
        
        # 2. Анализ типов файлов
        print("\n[*] Анализ типов файлов...")
        self.analyze_file_types(all_files)
        
        # 3. Анализ размеров
        print("\n[*] Анализ размеров...")
        self.analyze_file_sizes(all_files)
        
        # 4. Поиск дубликатов
        print("\n[*] Поиск дубликатов...")
        self.find_duplicates(all_files)
        
        # 5. Анализ структуры директорий
        print("\n[*] Анализ структуры директорий...")
        dir_stats = self.analyze_directory_structure()
        
        return {
            'total_files': len(all_files),
            'file_types': dict(self.file_types),
            'file_sizes': {k: {'count': len(v), 'total_mb': sum(v)/1024/1024} 
                          for k, v in self.file_sizes.items()},
            'large_files': self.large_files[:50],
            'duplicates': {k: len(v) for k, v in self.duplicates.items() if len(v) > 1},
            'directory_structure': dir_stats
        }
    
    def scan_all_files(self) -> List[Path]:
        """Сканирование всех файлов проекта"""
        all_files = []
        
        for root, dirs, files in os.walk(self.project_root):
            # Удаляем игнорируемые директории
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
            
            for file in files:
                file_path = Path(root) / file
                all_files.append(file_path)
                self.stats['total_files'] += 1
        
        return all_files
    
    def analyze_file_types(self, files: List[Path]):
        """Анализ типов файлов"""
        for file_path in files:
            ext = file_path.suffix.lower()
            if not ext:
                ext = '(no extension)'
            self.file_types[ext] += 1
        
        print("\n    ТОП-30 типов файлов:")
        for i, (ext, count) in enumerate(sorted(self.file_types.items(), 
                                                 key=lambda x: x[1], reverse=True)[:30], 1):
            print(f"    {i:2d}. {ext:<20} {count:>6,} файлов")
    
    def analyze_file_sizes(self, files: List[Path]):
        """Анализ размеров файлов"""
        total_size = 0
        
        for file_path in files:
            try:
                size = file_path.stat().st_size
                ext = file_path.suffix.lower() or '(no extension)'
                
                self.file_sizes[ext].append(size)
                total_size += size
                
                # Большие файлы (>1MB)
                if size > 1024 * 1024:
                    self.large_files.append({
                        'path': str(file_path.relative_to(self.project_root)),
                        'size_mb': size / 1024 / 1024,
                        'ext': ext
                    })
            except:
                pass
        
        # Сортируем большие файлы
        self.large_files.sort(key=lambda x: x['size_mb'], reverse=True)
        
        print(f"\n    Общий размер: {total_size / 1024 / 1024 / 1024:.2f} GB")
        print(f"    Файлов >1MB: {len(self.large_files):,}")
        
        if self.large_files:
            print("\n    ТОП-10 самых больших файлов:")
            for i, f in enumerate(self.large_files[:10], 1):
                print(f"    {i:2d}. {f['path']:<60} {f['size_mb']:>8.2f} MB")
    
    def find_duplicates(self, files: List[Path]):
        """Поиск дублирующихся файлов по содержимому"""
        file_hashes = defaultdict(list)
        checked = 0
        
        for file_path in files:
            # Проверяем только небольшие файлы (<10MB)
            try:
                size = file_path.stat().st_size
                if size > 10 * 1024 * 1024:
                    continue
                
                # Только код и конфиги
                ext = file_path.suffix.lower()
                if ext not in ['.py', '.js', '.ts', '.tsx', '.json', '.yml', '.yaml', '.md']:
                    continue
                
                with open(file_path, 'rb') as f:
                    content_hash = hashlib.md5(f.read()).hexdigest()
                
                file_hashes[content_hash].append(file_path)
                checked += 1
                
            except:
                pass
        
        # Найти дубликаты
        for hash_val, paths in file_hashes.items():
            if len(paths) > 1:
                self.duplicates[hash_val] = paths
        
        print(f"\n    Проверено файлов: {checked:,}")
        print(f"    Найдено групп дубликатов: {len(self.duplicates):,}")
        
        if self.duplicates:
            print("\n    Примеры дубликатов (первые 5 групп):")
            for i, (hash_val, paths) in enumerate(list(self.duplicates.items())[:5], 1):
                print(f"\n    Группа {i} ({len(paths)} файлов):")
                for path in paths[:3]:
                    print(f"      - {path.relative_to(self.project_root)}")
                if len(paths) > 3:
                    print(f"      ... и еще {len(paths) - 3} файлов")
    
    def analyze_directory_structure(self) -> Dict:
        """Анализ структуры директорий"""
        dir_stats = {}
        
        # Директории верхнего уровня
        for item in self.project_root.iterdir():
            if not item.is_dir() or item.name in self.ignore_dirs:
                continue
            
            # Подсчет файлов в директории
            file_count = 0
            py_count = 0
            ts_count = 0
            total_size = 0
            
            for root, dirs, files in os.walk(item):
                dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
                for file in files:
                    file_count += 1
                    file_path = Path(root) / file
                    try:
                        total_size += file_path.stat().st_size
                        if file.endswith('.py'):
                            py_count += 1
                        elif file.endswith(('.ts', '.tsx')):
                            ts_count += 1
                    except:
                        pass
            
            dir_stats[item.name] = {
                'files': file_count,
                'py_files': py_count,
                'ts_files': ts_count,
                'size_mb': total_size / 1024 / 1024
            }
        
        print("\n    Директории верхнего уровня (ТОП-20 по размеру):")
        sorted_dirs = sorted(dir_stats.items(), key=lambda x: x[1]['size_mb'], reverse=True)[:20]
        
        for i, (name, stats) in enumerate(sorted_dirs, 1):
            print(f"    {i:2d}. {name:<30} {stats['files']:>5} файлов, "
                  f"{stats['py_files']:>4} .py, {stats['ts_files']:>4} .ts, "
                  f"{stats['size_mb']:>8.2f} MB")
        
        return dir_stats


def main():
    """Главная функция"""
    project_root = Path(".")
    
    auditor = ProjectStructureAuditor(project_root)
    results = auditor.audit_full_structure()
    
    # Сохранение результатов
    output_dir = Path("./output/audit")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    import json
    output_file = output_dir / "structure_audit.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print("\n" + "=" * 80)
    print("СТРУКТУРНЫЙ АУДИТ ЗАВЕРШЕН")
    print("=" * 80)
    print(f"\nРезультаты: {output_file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())



