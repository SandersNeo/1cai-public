# [NEXUS IDENTITY] ID: -4359180632403751108 | DATE: 2025-11-19

#!/usr/bin/env python3
"""
Скрипт для запуска всех rate limiting тестов

Использование:
    python run_ratelimit_tests.py
    python run_ratelimit_tests.py --quick
    python run_ratelimit_tests.py --benchmark
    python run_ratelimit_tests.py --load-test

Версия: 1.0.0
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path


def run_command(command: str, description: str) -> bool:
    """Запуск команды с обработкой ошибок"""
    print(f"\n🚀 {description}")
    print(f"Команда: {command}")
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✅ {description} - завершено успешно")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - ошибка:")
        print(f"Return code: {e.returncode}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ {description} - неожиданная ошибка: {e}")
        return False


def check_dependencies() -> bool:
    """Проверка зависимостей"""
    print("🔍 Проверка зависимостей...")
    
    required_tools = ['python3', 'pip3']
    optional_tools = ['redis-server', 'locust']
    
    missing_required = []
    missing_optional = []
    
    # Проверяем обязательные инструменты
    for tool in required_tools:
        try:
            subprocess.run([tool, '--version'], capture_output=True, check=True)
            print(f"✅ {tool} - установлен")
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing_required.append(tool)
            print(f"❌ {tool} - не найден")
    
    # Проверяем опциональные инструменты
    for tool in optional_tools:
        try:
            subprocess.run([tool, '--version'], capture_output=True, check=True)
            print(f"✅ {tool} - установлен")
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing_optional.append(tool)
            print(f"⚠️ {tool} - не найден (опционально)")
    
    if missing_required:
        print(f"\n❌ Отсутствуют обязательные зависимости: {missing_required}")
        print("Установите их и повторите попытку")
        return False
    
    if missing_optional:
        print(f"\n⚠️ Отсутствуют опциональные зависимости: {missing_optional}")
        print("Некоторые тесты могут быть пропущены")
    
    return True


def install_dependencies() -> bool:
    """Установка зависимостей"""
    print("\n📦 Установка зависимостей...")
    
    # Проверяем наличие requirements файлов
    test_req_file = Path("requirements-test.txt")
    if not test_req_file.exists():
        print("❌ Файл requirements-test.txt не найден")
        return False
    
    try:
        # Устанавливаем тестовые зависимости
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements-test.txt"
        ], check=True, capture_output=True, text=True)
        
        print("✅ Зависимости установлены успешно")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки зависимостей: {e}")
        return False


def run_unit_tests() -> bool:
    """Запуск unit тестов"""
    return run_command(
        "pytest tests/test_ratelimit.py -v -m 'unit' --tb=short",
        "Запуск unit тестов"
    )


def run_integration_tests() -> bool:
    """Запуск integration тестов"""
    return run_command(
        "pytest tests/test_ratelimit.py -v -m 'integration' --tb=short",
        "Запуск integration тестов"
    )


def run_performance_tests() -> bool:
    """Запуск performance тестов"""
    return run_command(
        "pytest tests/test_ratelimit.py -v -m 'performance' --benchmark-only",
        "Запуск performance тестов"
    )


def run_stress_tests() -> bool:
    """Запуск stress тестов"""
    return run_command(
        "pytest tests/test_ratelimit.py -v -m 'stress' --tb=short",
        "Запуск stress тестов"
    )


def run_security_tests() -> bool:
    """Запуск security тестов"""
    return run_command(
        "pytest tests/test_ratelimit.py -v -m 'security' --tb=short",
        "Запуск security тестов"
    )


def run_thread_safety_tests() -> bool:
    """Запуск thread safety тестов"""
    return run_command(
        "pytest tests/test_ratelimit.py -v -m 'thread_safety' --tb=short",
        "Запуск thread safety тестов"
    )


def run_benchmarks() -> bool:
    """Запуск бенчмарков"""
    return run_command(
        "python tests/benchmark_ratelimit.py --quick",
        "Запуск бенчмарков"
    )


def run_load_tests() -> bool:
    """Запуск нагрузочных тестов"""
    print("\n🚀 Нагрузочное тестирование")
    print("=" * 50)
    print("Для запуска Locust GUI:")
    print("  locust -f tests/loadtest_ratelimit.py --host=http://localhost:8000")
    print("\nДля headless режима:")
    print("  locust -f tests/loadtest_ratelimit.py --headless -u 100 -r 5 -t 300s")
    print("\n⚠️ Убедитесь, что сервер запущен на http://localhost:8000")
    return True


def run_coverage_analysis() -> bool:
    """Анализ покрытия кода"""
    return run_command(
        "pytest tests/test_ratelimit.py --cov=ratelimit --cov-report=html --cov-report=term --cov-fail-under=90",
        "Анализ покрытия кода"
    )


def run_all_tests() -> bool:
    """Запуск всех тестов"""
    print("\n🧪 Запуск всех тестов rate limiting")
    print("=" * 50)
    
    tests = [
        ("Unit тесты", run_unit_tests),
        ("Integration тесты", run_integration_tests),
        ("Performance тесты", run_performance_tests),
        ("Stress тесты", run_stress_tests),
        ("Security тесты", run_security_tests),
        ("Thread safety тесты", run_thread_safety_tests),
        ("Бенчмарки", run_benchmarks),
        ("Покрытие кода", run_coverage_analysis)
    ]
    
    results = []
    start_time = time.time()
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} - неожиданная ошибка: {e}")
            results.append((test_name, False))
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Подводим итоги
    print(f"\n{'='*60}")
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
    print(f"{'='*60}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:<30} {status}")
    
    print(f"\nВремя выполнения: {total_time:.2f} секунд")
    print(f"Успешно: {passed}/{total} тестов ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 Все тесты прошли успешно!")
        return True
    else:
        print(f"\n⚠️ {total-passed} тестов завершились с ошибками")
        return False


def print_summary():
    """Вывод краткой справки"""
    print("""
🧪 Rate Limiting Test Suite
============================

Использование:
  python run_ratelimit_tests.py                    # Все тесты
  python run_ratelimit_tests.py --quick            # Быстрые тесты
  python run_ratelimit_tests.py --unit             # Только unit тесты
  python run_ratelimit_tests.py --benchmark        # Бенчмарки
  python run_ratelimit_tests.py --load-test        # Нагрузочное тестирование
  python run_ratelimit_tests.py --coverage         # Покрытие кода
  python run_ratelimit_tests.py --install-deps     # Установить зависимости

Дополнительные команды:
  make test-ratelimit                              # Все тесты (через make)
  make test-ratelimit-unit                         # Unit тесты
  make test-ratelimit-performance                  # Performance тесты
  make test-ratelimit-benchmark                    # Бенчмарки
  make test-ratelimit-load                         # Нагрузочное тестирование

Документация:
  tests/README_RATELIMIT_TESTS.md                  # Подробная документация
  RATELIMIT_TESTS_SUMMARY.md                       # Обзор проекта
""")


def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(
        description="Запуск rate limiting тестов",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s                    # Все тесты
  %(prog)s --quick            # Быстрые тесты
  %(prog)s --benchmark        # Только бенчмарки
  %(prog)s --install-deps     # Установить зависимости
        """
    )
    
    parser.add_argument(
        '--quick', 
        action='store_true', 
        help='Быстрые тесты (пропускает долгие тесты)'
    )
    parser.add_argument(
        '--unit', 
        action='store_true', 
        help='Только unit тесты'
    )
    parser.add_argument(
        '--integration', 
        action='store_true', 
        help='Только integration тесты'
    )
    parser.add_argument(
        '--performance', 
        action='store_true', 
        help='Только performance тесты'
    )
    parser.add_argument(
        '--stress', 
        action='store_true', 
        help='Только stress тесты'
    )
    parser.add_argument(
        '--security', 
        action='store_true', 
        help='Только security тесты'
    )
    parser.add_argument(
        '--thread-safety', 
        action='store_true', 
        help='Только thread safety тесты'
    )
    parser.add_argument(
        '--benchmark', 
        action='store_true', 
        help='Только бенчмарки'
    )
    parser.add_argument(
        '--load-test', 
        action='store_true', 
        help='Нагрузочное тестирование (инструкции)'
    )
    parser.add_argument(
        '--coverage', 
        action='store_true', 
        help='Анализ покрытия кода'
    )
    parser.add_argument(
        '--install-deps', 
        action='store_true', 
        help='Установить зависимости'
    )
    parser.add_argument(
        '--help-commands', 
        action='store_true', 
        help='Показать доступные команды'
    )
    
    args = parser.parse_args()
    
    # Показываем справку
    if args.help_commands:
        print_summary()
        return 0
    
    # Проверяем, что мы в правильной директории
    if not Path("tests/test_ratelimit.py").exists():
        print("❌ Файл tests/test_ratelimit.py не найден")
        print("Убедитесь, что вы находитесь в корневой директории проекта")
        return 1
    
    # Установка зависимостей
    if args.install_deps:
        if not install_dependencies():
            return 1
        return 0
    
    # Проверка зависимостей
    if not check_dependencies():
        return 1
    
    # Определяем, какие тесты запускать
    test_functions = []
    
    if args.unit:
        test_functions.append(("Unit тесты", run_unit_tests))
    elif args.integration:
        test_functions.append(("Integration тесты", run_integration_tests))
    elif args.performance:
        test_functions.append(("Performance тесты", run_performance_tests))
    elif args.stress:
        test_functions.append(("Stress тесты", run_stress_tests))
    elif args.security:
        test_functions.append(("Security тесты", run_security_tests))
    elif args.thread_safety:
        test_functions.append(("Thread safety тесты", run_thread_safety_tests))
    elif args.benchmark:
        test_functions.append(("Бенчмарки", run_benchmarks))
    elif args.load_test:
        if not run_load_tests():
            return 1
        return 0
    elif args.coverage:
        if not run_coverage_analysis():
            return 1
        return 0
    else:
        # Все тесты или быстрые тесты
        if args.quick:
            test_functions = [
                ("Unit тесты", run_unit_tests),
                ("Integration тесты", run_integration_tests),
                ("Thread safety тесты", run_thread_safety_tests),
                ("Бенчмарки (быстрые)", run_benchmarks)
            ]
        else:
            return run_all_tests()
    
    # Запускаем выбранные тесты
    print(f"\n🚀 Запуск {len(test_functions)} тестов...")
    
    success = True
    for test_name, test_func in test_functions:
        try:
            if not test_func():
                success = False
        except Exception as e:
            print(f"❌ {test_name} - неожиданная ошибка: {e}")
            success = False
    
    if success:
        print(f"\n🎉 Все выбранные тесты завершились успешно!")
        return 0
    else:
        print(f"\n⚠️ Некоторые тесты завершились с ошибками")
        return 1


if __name__ == "__main__":
    sys.exit(main())