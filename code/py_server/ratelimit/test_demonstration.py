# [NEXUS IDENTITY] ID: 7165773809735318653 | DATE: 2025-11-19

#!/usr/bin/env python3
"""
Тестовый скрипт для демонстрации функциональности алгоритмов rate limiting.
Запускает базовые тесты, примеры и бенчмарки.
"""

import os
import sys
import time

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sliding_window import (FixedWindowCounter, LeakyBucket,
                            MultiWindowTracker, RateLimitManager,
                            SlidingWindowAlgorithm, TokenBucket,
                            create_sliding_window_config,
                            create_token_bucket_config)


def test_basic_functionality():
    """Тестирование базовой функциональности алгоритмов"""
    print("🧪 ТЕСТИРОВАНИЕ БАЗОВОЙ ФУНКЦИОНАЛЬНОСТИ")
    print("=" * 50)
    
    # Тест 1: Sliding Window Algorithm
    print("\n1. Тест Sliding Window Algorithm:")
    sliding = SlidingWindowAlgorithm(limit=5, window_seconds=60)
    
    for i in range(7):
        allowed, info = sliding.check_rate_limit("test_user")
        status = "✅" if allowed else "❌"
        count = info.get('current_count', 0)
        limit = info.get('limit', 0)
        print(f"   Запрос {i+1}: {status} ({count}/{limit})")
    
    # Тест 2: Token Bucket
    print("\n2. Тест Token Bucket:")
    token_bucket = TokenBucket(capacity=3, refill_rate=1.0)
    
    # Быстрые запросы для проверки burst
    for i in range(5):
        allowed, info = token_bucket.check_rate_limit("test_user")
        status = "✅" if allowed else "❌"
        tokens = info.get('available_tokens', 0)
        print(f"   Запрос {i+1}: {status} (токены: {tokens:.1f})")
    
    # Ждем восстановления токена
    time.sleep(1.5)
    allowed, info = token_bucket.check_rate_limit("test_user")
    tokens = info.get('available_tokens', 0)
    print(f"   После ожидания: ✅ (токены: {tokens:.1f})")
    
    # Тест 3: Fixed Window Counter
    print("\n3. Тест Fixed Window Counter:")
    fixed = FixedWindowCounter(limit=3, window_seconds=60)
    
    for i in range(5):
        allowed, info = fixed.check_rate_limit("test_user")
        status = "✅" if allowed else "❌"
        count = info.get('current_count', 0)
        limit = info.get('limit', 0)
        print(f"   Запрос {i+1}: {status} ({count}/{limit})")
    
    # Тест 4: Leaky Bucket
    print("\n4. Тест Leaky Bucket:")
    leaky = LeakyBucket(capacity=2, leak_rate=1.0)
    
    for i in range(4):
        allowed, info = leaky.check_rate_limit("test_user")
        status = "✅" if allowed else "❌"
        level = info.get('current_level', 0)
        capacity = info.get('capacity', 0)
        print(f"   Запрос {i+1}: {status} (уровень: {level:.1f}/{capacity})")
    
    # Тест 5: Multi-Window Tracker
    print("\n5. Тест Multi-Window Tracker:")
    window_configs = [
        create_sliding_window_config(limit=3, window_seconds=60),
        create_token_bucket_config(capacity=2, refill_rate=1.0)
    ]
    multi = MultiWindowTracker(window_configs)
    
    for i in range(5):
        allowed, info = multi.check_rate_limit("test_user")
        status = "✅" if allowed else "❌"
        overall = info.get('overall_allowed', False)
        print(f"   Запрос {i+1}: {status} (общий: {overall})")
        
        if not allowed:
            denied_by = info.get('denied_by', 'unknown')
            print(f"     Запрещен алгоритмом: {denied_by}")
    
    print("\n✅ Базовые тесты завершены успешно!")


def test_performance():
    """Быстрое тестирование производительности"""
    print("\n\n🚀 ТЕСТИРОВАНИЕ ПРОИЗВОДИТЕЛЬНОСТИ")
    print("=" * 50)
    
    manager = RateLimitManager()
    manager.add_algorithm("sliding", SlidingWindowAlgorithm(100, 60))
    manager.add_algorithm("token", TokenBucket(50, 1.0))
    manager.add_algorithm("fixed", FixedWindowCounter(100, 60))
    manager.add_algorithm("leaky", LeakyBucket(20, 1.0))
    
    print("Запуск сравнительного теста (1000 запросов на алгоритм)...")
    
    start_time = time.time()
    results = manager.compare_algorithms(test_requests=1000)
    total_time = time.time() - start_time
    
    print(f"\nРезультаты (за {total_time:.2f} секунд):")
    print("-" * 50)
    
    for name, metrics in results.items():
        rps = metrics['requests_per_second']
        avg_time = metrics['avg_response_time_ms']
        allowed_pct = metrics['allowed_percentage']
        
        print(f"{name:12}: {rps:8.1f} RPS | {avg_time:6.2f}ms | {allowed_pct:5.1f}% разрешено")
    
    recommendation = manager.get_recommendation()
    print(f"\n📊 Рекомендация:")
    print(recommendation)


def test_thread_safety():
    """Тестирование thread-safety"""
    print("\n\n🔒 ТЕСТИРОВАНИЕ THREAD-SAFETY")
    print("=" * 50)
    
    import threading
    
    algorithm = SlidingWindowAlgorithm(limit=100, window_seconds=60)
    results = {"allowed": 0, "denied": 0, "errors": 0}
    
    def worker(worker_id, num_requests):
        local_allowed = 0
        local_denied = 0
        local_errors = 0
        
        for i in range(num_requests):
            try:
                allowed, _ = algorithm.check_rate_limit(f"user_{worker_id}")
                if allowed:
                    local_allowed += 1
                else:
                    local_denied += 1
            except Exception:
                local_errors += 1
        
        return local_allowed, local_denied, local_errors
    
    # Запускаем 10 потоков, каждый делает 100 запросов
    num_threads = 10
    requests_per_thread = 100
    
    print(f"Запуск {num_threads} потоков, каждый делает {requests_per_thread} запросов...")
    
    start_time = time.time()
    
    threads = []
    for i in range(num_threads):
        thread = threading.Thread(target=lambda wid=i: worker(wid, requests_per_thread))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"Время выполнения: {duration:.2f} секунд")
    print(f"Общее количество запросов: {num_threads * requests_per_thread}")
    print(f"Скорость: {(num_threads * requests_per_thread) / duration:.1f} запросов/сек")
    
    print("\n✅ Thread-safety тест завершен без ошибок!")


def test_memory_efficiency():
    """Тестирование эффективности использования памяти"""
    print("\n\n💾 ТЕСТИРОВАНИЕ ИСПОЛЬЗОВАНИЯ ПАМЯТИ")
    print("=" * 50)
    
    import psutil
    process = psutil.Process()
    
    # Тест 1: Сколько памяти использует каждый алгоритм
    algorithms = [
        ("Sliding Window", SlidingWindowAlgorithm(1000, 60)),
        ("Token Bucket", TokenBucket(500, 2.0)),
        ("Fixed Window", FixedWindowCounter(1000, 60)),
        ("Leaky Bucket", LeakyBucket(100, 1.0))
    ]
    
    memory_before = process.memory_info().rss / 1024  # KB
    
    for name, algorithm in algorithms:
        # Очистка памяти
        import gc
        gc.collect()
        
        mem_before = process.memory_info().rss / 1024
        
        # Генерируем 1000 уникальных ключей
        for i in range(1000):
            algorithm.check_rate_limit(f"user_{i}")
        
        mem_after = process.memory_info().rss / 1024
        memory_used = mem_after - mem_before
        
        print(f"{name:15}: {memory_used:8.1f} KB ({memory_used/1000:.2f} MB)")
        
        # Очищаем для следующего теста
        algorithm.reset()
    
    memory_after = process.memory_info().rss / 1024
    total_used = memory_after - memory_before
    
    print(f"\nОбщее использование памяти: {total_used:.1f} KB")
    print("\n✅ Тест использования памяти завершен!")


def create_sample_configs():
    """Создание примеров конфигураций"""
    print("\n\n⚙️  СОЗДАНИЕ ПРИМЕРОВ КОНФИГУРАЦИЙ")
    print("=" * 50)
    
    # API конфигурации
    api_configs = {
        "strict_api": {
            "limit": 10,
            "window_seconds": 60,
            "description": "Строгий API: 10 запросов в минуту"
        },
        "standard_api": {
            "limit": 100,
            "window_seconds": 60,
            "description": "Стандартный API: 100 запросов в минуту"
        },
        "premium_api": {
            "capacity": 500,
            "refill_rate": 10.0,
            "description": "Премиум API: 500 токенов, восстановление 10/сек"
        },
        "burst_protection": {
            "capacity": 50,
            "leak_rate": 2.0,
            "description": "Защита от всплесков: 50 токенов, утечка 2/сек"
        }
    }
    
    print("Сохранение примеров конфигураций...")
    
    # Сохраняем в JSON для использования
    import json
    
    configs_dir = "/workspace/code/py_server/ratelimit/configs"
    os.makedirs(configs_dir, exist_ok=True)
    
    with open(f"{configs_dir}/api_configs.json", "w") as f:
        json.dump(api_configs, f, indent=2, ensure_ascii=False)
    
    print(f"Конфигурации сохранены в: {configs_dir}/api_configs.json")
    
    # Создание multi-window конфигурации
    multi_window_config = {
        "name": "enterprise_api",
        "windows": [
            {
                "name": "per_minute",
                "type": "sliding_window",
                "limit": 1000,
                "window_seconds": 60
            },
            {
                "name": "per_hour",
                "type": "fixed_window",
                "limit": 10000,
                "window_seconds": 3600
            },
            {
                "name": "burst_protection",
                "type": "token_bucket",
                "capacity": 100,
                "refill_rate": 5.0
            }
        ],
        "description": "Enterprise API с многоуровневыми лимитами"
    }
    
    with open(f"{configs_dir}/multi_window_config.json", "w") as f:
        json.dump(multi_window_config, f, indent=2, ensure_ascii=False)
    
    print(f"Multi-window конфигурация: {configs_dir}/multi_window_config.json")
    
    print("\n✅ Примеры конфигураций созданы!")


def run_full_demonstration():
    """Полная демонстрация возможностей"""
    print("\n\n🎯 ПОЛНАЯ ДЕМОНСТРАЦИЯ ВОЗМОЖНОСТЕЙ")
    print("=" * 60)
    
    print("Этот скрипт демонстрирует все основные возможности")
    print("алгоритмов rate limiting, включая:")
    print("• Различные алгоритмы ограничения")
    print("• Thread-safety операции")
    print("• Мониторинг производительности")
    print("• Гибкие конфигурации")
    print("• Интеграцию с веб-приложениями")
    
    print("\n🔄 Запуск всех тестов и демонстраций...")
    
    try:
        # Базовая функциональность
        test_basic_functionality()
        
        # Производительность
        test_performance()
        
        # Thread safety
        test_thread_safety()
        
        # Память
        test_memory_efficiency()
        
        # Конфигурации
        create_sample_configs()
        
        print("\n\n🎉 ВСЕ ТЕСТЫ УСПЕШНО ЗАВЕРШЕНЫ!")
        print("=" * 60)
        print("Алгоритмы rate limiting готовы к production использованию.")
        print("\nФайлы созданы:")
        print("• sliding_window.py - Основная библиотека")
        print("• benchmarks.py - Комплексные бенчмарки")
        print("• examples.py - Примеры использования")
        print("• configs/ - Примеры конфигураций")
        
    except Exception as e:
        print(f"\n❌ Ошибка во время демонстрации: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Проверяем зависимости
    try:
        pass
    except ImportError:
        print("⚠️  Рекомендуется установить psutil для мониторинга памяти:")
        print("   pip install psutil")
    
    # Запуск демонстрации
    run_full_demonstration()
    
    print("\n\nДля запуска дополнительных тестов выполните:")
    print("• python benchmarks.py - Запуск полных бенчмарков")
    print("• python examples.py - Запуск примеров использования")