#!/usr/bin/env python3
"""
Проверка безопасности перед git push
Финальная проверка что нет проприетарных данных
"""

import subprocess
import sys
from pathlib import Path

def check_git_status():
    """Проверка git status"""
    print("=" * 80)
    print("ПРОВЕРКА БЕЗОПАСНОСТИ GIT")
    print("=" * 80)
    print()
    
    try:
        # Git status
        result = subprocess.run(['git', 'status', '--short'], 
                              capture_output=True, text=True, cwd='.')
        
        if result.returncode != 0:
            print("[INFO] Git repository не инициализирован")
            print("[INFO] Это нормально - будет создан при первом commit")
            return True
        
        files = result.stdout.strip().split('\n') if result.stdout.strip() else []
        
        print(f"[*] Файлов в git status: {len(files)}")
        
        # Проверяем на проблемные паттерны
        dangerous_files = []
        
        for file_line in files:
            if not file_line.strip():
                continue
            
            # Извлекаем имя файла
            parts = file_line.strip().split()
            if len(parts) < 2:
                continue
            
            filename = parts[-1]
            
            # Проверяем паттерны
            if any(pattern in filename.lower() for pattern in [
                'knowledge_base', 
                'full_parse',
                'ml_training_dataset',
                'edt_parse_results',
                '.env'
            ]):
                dangerous_files.append(filename)
        
        if dangerous_files:
            print("\n" + "!" * 80)
            print("ОПАСНЫЕ ФАЙЛЫ НАЙДЕНЫ!")
            print("!" * 80)
            print("\nСледующие файлы НЕ должны быть в git:")
            for f in dangerous_files:
                print(f"  ❌ {f}")
            
            print("\n[ДЕЙСТВИЕ] Добавьте эти файлы в .gitignore!")
            return False
        else:
            print("\n[OK] Опасных файлов не найдено в git status")
            return True
            
    except FileNotFoundError:
        print("[INFO] Git не установлен или не в PATH")
        return True
    except Exception as e:
        print(f"[ERROR] Ошибка проверки: {e}")
        return False

def check_large_files():
    """Проверка больших файлов"""
    print("\n[*] Проверка больших файлов в проекте...")
    
    large_files = []
    
    # Проверяем ключевые директории
    dirs_to_check = ['knowledge_base', 'output']
    
    for dir_name in dirs_to_check:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            continue
        
        for file in dir_path.rglob('*.json'):
            size_mb = file.stat().st_size / 1024 / 1024
            if size_mb > 10:
                large_files.append((str(file), size_mb))
    
    if large_files:
        total_size = sum(s for _, s in large_files)
        print(f"\n  [ПРЕДУПРЕЖДЕНИЕ] Найдено больших файлов: {len(large_files)}")
        print(f"  [INFO] Общий размер: {total_size:.2f} MB")
        print("\n  Убедитесь что они в .gitignore:")
        for path, size in large_files[:10]:
            print(f"    - {path} ({size:.2f} MB)")
        
        if len(large_files) > 10:
            print(f"    ... и еще {len(large_files) - 10} файлов")
    else:
        print("  [OK] Больших проблемных файлов не найдено")
    
    return large_files

def check_env_files():
    """Проверка .env файлов"""
    print("\n[*] Проверка .env файлов...")
    
    env_files = list(Path('.').rglob('.env'))
    env_files = [f for f in env_files if 'archive_package_OLD' not in str(f) and '.example' not in f.name]
    
    if env_files:
        print(f"\n  [ПРЕДУПРЕЖДЕНИЕ] Найдены .env файлы: {len(env_files)}")
        for env_file in env_files:
            print(f"    - {env_file}")
        print("\n  [ДЕЙСТВИЕ] Переименуйте в .env.example и удалите реальные значения!")
        return False
    else:
        print("  [OK] .env файлов не найдено")
        
        # Проверяем наличие .env.example
        if Path('.env.example').exists():
            print("  [OK] .env.example существует")
        else:
            print("  [РЕКОМЕНДАЦИЯ] Создайте .env.example")
        
        return True

def final_check():
    """Финальная проверка"""
    print("\n" + "=" * 80)
    print("ФИНАЛЬНАЯ ПРОВЕРКА")
    print("=" * 80)
    
    checks = {
        '.gitignore существует': Path('.gitignore').exists(),
        '.env.example существует': Path('.env.example').exists(),
        'LICENSE существует': Path('LICENSE').exists(),
        'README.md существует': Path('README.md').exists()
    }
    
    all_passed = all(checks.values())
    
    print()
    for check, passed in checks.items():
        status = "[OK]" if passed else "[FAIL]"
        symbol = "✓" if passed else "✗"
        print(f"  {status} {check}")
    
    return all_passed

def main():
    """Главная функция"""
    print("\nПроверка безопасности перед публикацией на GitHub...\n")
    
    # Проверки
    git_safe = check_git_status()
    large_files = check_large_files()
    env_safe = check_env_files()
    final_passed = final_check()
    
    # Итог
    print("\n" + "=" * 80)
    
    if git_safe and env_safe and final_passed:
        print("✓ БЕЗОПАСНО ПУБЛИКОВАТЬ")
        print("=" * 80)
        print("\nВсе проверки пройдены!")
        print("Можно делать git add, commit, push")
        return 0
    else:
        print("✗ НЕ БЕЗОПАСНО ПУБЛИКОВАТЬ")
        print("=" * 80)
        print("\nИсправьте проблемы выше перед публикацией!")
        return 1

if __name__ == "__main__":
    sys.exit(main())



