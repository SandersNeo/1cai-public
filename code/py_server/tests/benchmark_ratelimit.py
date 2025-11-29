# [NEXUS IDENTITY] ID: 4178572628119588004 | DATE: 2025-11-19

"""
Performance Benchmarks для системы Rate Limiting

Запуск:
    python tests/benchmark_ratelimit.py
    python -m pytest tests/benchmark_ratelimit.py --benchmark-only
    
Версия: 1.0.0
"""

import json
import statistics
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

# Добавляем путь для импортов
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import pytest_benchmark
except ImportError:
    pytest_benchmark = None
    print("Warning: pytest-benchmark not installed. Install with: pip install pytest-benchmark")


# =============================================================================
# BENCHMARK DATA STRUCTURES
# =============================================================================

@dataclass
class BenchmarkResult:
    """Результат бенчмарка"""
    name: str
    operations_per_second: float
    average_time_ms: float
    median_time_ms: float
    min_time_ms: float
    max_time_ms: float
    std_dev_ms: float
    total_operations: int
    total_time_seconds: float
    memory_usage_mb: float
    error_count: int
    metadata: Dict[str, Any]


@dataclass
class LoadTestResult:
    """Результат нагрузочного теста"""
    concurrency_level: int
    throughput_ops_per_sec: float
    average_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    error_rate_percent: float
    success_rate_percent: float
    total_requests: int
    successful_requests: int


# =============================================================================
# RATE LIMITING IMPLEMENTATIONS FOR BENCHMARKING
# =============================================================================

class MemoryRateLimiter:
    """Простая реализация rate limiter для бенчмарков"""
    
    def __init__(self):
        self.requests = {}
        self.lock = threading.Lock()
    
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Проверить, разрешен ли запрос"""
        current_time = time.time()
        
        with self.lock:
            if key not in self.requests:
                self.requests[key] = []
            
            # Очищаем старые запросы
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if current_time - req_time < window
            ]
            
            # Проверяем лимит
            if len(self.requests[key]) >= limit:
                return False
            
            # Добавляем текущий запрос
            self.requests[key].append(current_time)
            return True


class OptimizedRateLimiter:
    """Оптимизированная реализация rate limiter"""
    
    def __init__(self):
        self.buckets = {}
        self.lock = threading.Lock()
    
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Проверить, разрешен ли запрос (оптимизированная версия)"""
        current_time = int(time.time())
        bucket_key = f"{key}:{current_time // window}"
        
        with self.lock:
            if bucket_key not in self.buckets:
                self.buckets[bucket_key] = 0
            
            if self.buckets[bucket_key] >= limit:
                return False
            
            self.buckets[bucket_key] += 1
            return True


class RedisSimulator:
    """Симулятор Redis для бенчмарков"""
    
    def __init__(self):
        self.data = {}
        self.lock = threading.Lock()
    
    def incr(self, key: str) -> int:
        """Инкремент счетчика"""
        with self.lock:
            if key not in self.data:
                self.data[key] = 0
            self.data[key] += 1
            return self.data[key]
    
    def expire(self, key: str, seconds: int) -> bool:
        """Установка TTL (заглушка)"""
        return True
    
    def get(self, key: str) -> Optional[int]:
        """Получение значения"""
        return self.data.get(key)


class RedisRateLimiter:
    """Rate limiter с симуляцией Redis"""
    
    def __init__(self, redis_sim: RedisSimulator):
        self.redis = redis_sim
        self.prefix = "ratelimit:"
    
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Проверить, разрешен ли запрос"""
        redis_key = f"{self.prefix}{key}"
        
        # Симулируем Redis операции
        current_count = self.redis.get(redis_key) or 0
        
        if current_count >= limit:
            return False
        
        self.redis.incr(redis_key)
        self.redis.expire(redis_key, window)
        return True


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_memory_usage() -> float:
    """Получить использование памяти в MB"""
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    except ImportError:
        # Fallback без psutil
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


@contextmanager
def benchmark_context():
    """Контекстный менеджер для бенчмарков"""
    start_time = time.perf_counter()
    start_memory = get_memory_usage()
    
    try:
        yield
    finally:
        end_time = time.perf_counter()
        end_memory = get_memory_usage()
        
        print(f"Memory usage: {start_memory:.1f}MB -> {end_memory:.1f}MB "
              f"(+{end_memory - start_memory:.1f}MB)")
        print(f"Execution time: {end_time - start_time:.3f}s")


def run_timing_test(func: callable, iterations: int) -> List[float]:
    """Запустить тест времени выполнения"""
    times = []
    
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times.append((end - start) * 1000)  # в миллисекундах
    
    return times


# =============================================================================
# BENCHMARK CLASSES
# =============================================================================

class RateLimiterBenchmark:
    """Бенчмарк для rate limiter'ов"""
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
    
    def benchmark_memory_limiter(self, iterations: int = 10000) -> BenchmarkResult:
        """Бенчмарк memory-based rate limiter"""
        limiter = MemoryRateLimiter()
        
        def test_operation():
            return limiter.is_allowed("test_key", 100, 60)
        
        print(f"\n=== Benchmarking Memory Rate Limiter ({iterations} iterations) ===")
        
        with benchmark_context():
            times = run_timing_test(test_operation, iterations)
        
        # Вычисляем статистики
        total_time = sum(times) / 1000  # обратно в секунды
        ops_per_sec = iterations / total_time
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        min_time = min(times)
        max_time = max(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0
        
        result = BenchmarkResult(
            name="Memory Rate Limiter",
            operations_per_second=ops_per_sec,
            average_time_ms=avg_time,
            median_time_ms=median_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            std_dev_ms=std_dev,
            total_operations=iterations,
            total_time_seconds=total_time,
            memory_usage_mb=get_memory_usage(),
            error_count=0,
            metadata={"implementation": "memory", "limit": 100, "window": 60}
        )
        
        self.results.append(result)
        return result
    
    def benchmark_optimized_limiter(self, iterations: int = 10000) -> BenchmarkResult:
        """Бенчмарк оптимизированного rate limiter"""
        limiter = OptimizedRateLimiter()
        
        def test_operation():
            return limiter.is_allowed("test_key", 100, 60)
        
        print(f"\n=== Benchmarking Optimized Rate Limiter ({iterations} iterations) ===")
        
        with benchmark_context():
            times = run_timing_test(test_operation, iterations)
        
        total_time = sum(times) / 1000
        ops_per_sec = iterations / total_time
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        min_time = min(times)
        max_time = max(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0
        
        result = BenchmarkResult(
            name="Optimized Rate Limiter",
            operations_per_second=ops_per_sec,
            average_time_ms=avg_time,
            median_time_ms=median_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            std_dev_ms=std_dev,
            total_operations=iterations,
            total_time_seconds=total_time,
            memory_usage_mb=get_memory_usage(),
            error_count=0,
            metadata={"implementation": "optimized", "limit": 100, "window": 60}
        )
        
        self.results.append(result)
        return result
    
    def benchmark_redis_limiter(self, iterations: int = 10000) -> BenchmarkResult:
        """Бенчмарк Redis-based rate limiter"""
        redis_sim = RedisSimulator()
        limiter = RedisRateLimiter(redis_sim)
        
        def test_operation():
            return limiter.is_allowed("test_key", 100, 60)
        
        print(f"\n=== Benchmarking Redis Rate Limiter ({iterations} iterations) ===")
        
        with benchmark_context():
            times = run_timing_test(test_operation, iterations)
        
        total_time = sum(times) / 1000
        ops_per_sec = iterations / total_time
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        min_time = min(times)
        max_time = max(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0
        
        result = BenchmarkResult(
            name="Redis Rate Limiter",
            operations_per_second=ops_per_sec,
            average_time_ms=avg_time,
            median_time_ms=median_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            std_dev_ms=std_dev,
            total_operations=iterations,
            total_time_seconds=total_time,
            memory_usage_mb=get_memory_usage(),
            error_count=0,
            metadata={"implementation": "redis", "limit": 100, "window": 60}
        )
        
        self.results.append(result)
        return result
    
    def benchmark_concurrent_performance(self, threads: int = 10, 
                                       operations_per_thread: int = 1000) -> BenchmarkResult:
        """Бенчмарк конкурентной производительности"""
        limiter = MemoryRateLimiter()
        results = []
        errors = []
        
        def worker_thread(thread_id: int):
            thread_results = []
            for i in range(operations_per_thread):
                key = f"thread_{thread_id}_key_{i}"
                try:
                    allowed = limiter.is_allowed(key, 100, 60)
                    thread_results.append(allowed)
                except Exception as e:
                    errors.append(str(e))
            return thread_results
        
        print(f"\n=== Benchmarking Concurrent Performance ===")
        print(f"Threads: {threads}, Operations per thread: {operations_per_thread}")
        
        with benchmark_context():
            start_time = time.perf_counter()
            
            with ThreadPoolExecutor(max_workers=threads) as executor:
                futures = [executor.submit(worker_thread, i) for i in range(threads)]
                
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        results.extend(result)
                    except Exception as e:
                        errors.append(str(e))
            
            end_time = time.perf_counter()
        
        total_time = end_time - start_time
        total_operations = len(results)
        ops_per_sec = total_operations / total_time
        error_count = len(errors)
        
        # Подсчитываем разрешенные запросы
        allowed_count = sum(results) if results else 0
        blocked_count = total_operations - allowed_count
        
        result = BenchmarkResult(
            name=f"Concurrent Performance ({threads} threads)",
            operations_per_second=ops_per_sec,
            average_time_ms=(total_time / total_operations) * 1000,
            median_time_ms=0,  # Не применимо для конкурентного теста
            min_time_ms=0,
            max_time_ms=0,
            std_dev_ms=0,
            total_operations=total_operations,
            total_time_seconds=total_time,
            memory_usage_mb=get_memory_usage(),
            error_count=error_count,
            metadata={
                "threads": threads,
                "operations_per_thread": operations_per_thread,
                "allowed_requests": allowed_count,
                "blocked_requests": blocked_count,
                "block_rate": blocked_count / max(total_operations, 1)
            }
        )
        
        self.results.append(result)
        return result
    
    def benchmark_scalability(self, max_concurrency: int = 100) -> List[LoadTestResult]:
        """Бенчмарк масштабируемости"""
        limiter = MemoryRateLimiter()
        results = []
        
        print(f"\n=== Benchmarking Scalability (up to {max_concurrency} concurrent users) ===")
        
        for concurrency in [1, 5, 10, 25, 50, 100]:
            print(f"Testing with {concurrency} concurrent users...")
            
            latencies = []
            successes = 0
            errors = 0
            total_requests = 0
            
            def load_worker():
                latencies_worker = []
                successes_worker = 0
                errors_worker = 0
                
                for _ in range(100):  # 100 запросов на worker
                    start = time.perf_counter()
                    
                    try:
                        allowed = limiter.is_allowed(f"load_test_key", 100, 60)
                        end = time.perf_counter()
                        
                        latency = (end - start) * 1000  # в миллисекундах
                        latencies_worker.append(latency)
                        
                        total_requests += 1
                        if allowed:
                            successes_worker += 1
                        else:
                            errors_worker += 1
                            
                    except Exception:
                        errors_worker += 1
                        total_requests += 1
                
                return latencies_worker, successes_worker, errors_worker
            
            # Запускаем concurrent workers
            start_time = time.perf_counter()
            
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [executor.submit(load_worker) for _ in range(concurrency)]
                
                for future in as_completed(futures):
                    try:
                        latencies_worker, successes_worker, errors_worker = future.result()
                        latencies.extend(latencies_worker)
                        successes += successes_worker
                        errors += errors_worker
                    except Exception:
                        errors += 100  # Предполагаем 100 неудачных запросов
            
            end_time = time.perf_counter()
            test_duration = end_time - start_time
            
            # Вычисляем статистики
            throughput = total_requests / test_duration
            avg_latency = statistics.mean(latencies) if latencies else 0
            p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) > 20 else 0  # 95-й перцентиль
            p99_latency = statistics.quantiles(latencies, n=100)[98] if len(latencies) > 100 else 0  # 99-й перцентиль
            error_rate = (errors / max(total_requests, 1)) * 100
            success_rate = (successes / max(total_requests, 1)) * 100
            
            result = LoadTestResult(
                concurrency_level=concurrency,
                throughput_ops_per_sec=throughput,
                average_latency_ms=avg_latency,
                p95_latency_ms=p95_latency,
                p99_latency_ms=p99_latency,
                error_rate_percent=error_rate,
                success_rate_percent=success_rate,
                total_requests=total_requests,
                successful_requests=successes
            )
            
            results.append(result)
        
        return results
    
    def print_results(self):
        """Вывести результаты бенчмарков"""
        print("\n" + "=" * 80)
        print("BENCHMARK RESULTS")
        print("=" * 80)
        
        for result in self.results:
            print(f"\n📊 {result.name}")
            print(f"   Operations/sec: {result.operations_per_second:,.0f}")
            print(f"   Avg time: {result.average_time_ms:.3f}ms")
            print(f"   Median time: {result.median_time_ms:.3f}ms")
            print(f"   Min/Max time: {result.min_time_ms:.3f}ms / {result.max_time_ms:.3f}ms")
            print(f"   Std deviation: {result.std_dev_ms:.3f}ms")
            print(f"   Memory usage: {result.memory_usage_mb:.1f}MB")
            print(f"   Errors: {result.error_count}")
            
            if "threads" in result.metadata:
                print(f"   Block rate: {result.metadata.get('block_rate', 0):.1%}")
    
    def save_results(self, filename: str = "benchmark_results.json"):
        """Сохранить результаты в файл"""
        data = {
            "timestamp": time.time(),
            "results": [
                {
                    **result.__dict__,
                    "metadata": result.metadata
                }
                for result in self.results
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\nResults saved to {filename}")


# =============================================================================
# MAIN BENCHMARK EXECUTION
# =============================================================================

def run_all_benchmarks():
    """Запустить все бенчмарки"""
    print("🚀 Starting Rate Limiting Performance Benchmarks")
    print("=" * 60)
    
    benchmark = RateLimiterBenchmark()
    
    try:
        # Базовая производительность
        benchmark.benchmark_memory_limiter(10000)
        benchmark.benchmark_optimized_limiter(10000) 
        benchmark.benchmark_redis_limiter(10000)
        
        # Конкурентная производительность
        benchmark.benchmark_concurrent_performance(10, 1000)
        benchmark.benchmark_concurrent_performance(50, 500)
        
        # Масштабируемость
        scalability_results = benchmark.benchmark_scalability(100)
        
        # Выводим результаты
        benchmark.print_results()
        
        # Выводим результаты масштабируемости
        print("\n📈 SCALABILITY RESULTS")
        print("-" * 40)
        for result in scalability_results:
            print(f"Concurrency {result.concurrency_level:3d}: "
                  f"Throughput {result.throughput_ops_per_sec:6.0f} ops/sec, "
                  f"Avg latency {result.average_latency_ms:6.2f}ms, "
                  f"P95 latency {result.p95_latency_ms:6.2f}ms, "
                  f"Errors {result.error_rate_percent:5.1f}%")
        
        # Сохраняем результаты
        benchmark.save_results()
        
        # Сравнение производительности
        print("\n🏆 PERFORMANCE COMPARISON")
        print("-" * 40)
        memory_result = next((r for r in benchmark.results if "Memory" in r.name), None)
        optimized_result = next((r for r in benchmark.results if "Optimized" in r.name), None)
        redis_result = next((r for r in benchmark.results if "Redis" in r.name), None)
        
        if memory_result and optimized_result:
            speedup = optimized_result.operations_per_second / memory_result.operations_per_second
            print(f"Optimized vs Memory: {speedup:.2f}x speedup")
        
        if memory_result and redis_result:
            ratio = redis_result.operations_per_second / memory_result.operations_per_second
            print(f"Redis vs Memory: {ratio:.2f}x performance")
        
        print("\n✅ Benchmarks completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        raise


def run_quick_benchmark():
    """Запустить быстрый бенчмарк"""
    print("⚡ Running Quick Benchmark")
    
    benchmark = RateLimiterBenchmark()
    
    # Быстрые тесты
    benchmark.benchmark_memory_limiter(1000)
    benchmark.benchmark_optimized_limiter(1000)
    benchmark.benchmark_concurrent_performance(5, 100)
    
    benchmark.print_results()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Rate Limiting Benchmarks")
    parser.add_argument("--quick", action="store_true", help="Run quick benchmark")
    parser.add_argument("--save", default="benchmark_results.json", help="Save results to file")
    parser.add_argument("--no-save", action="store_true", help="Don't save results")
    
    args = parser.parse_args()
    
    try:
        if args.quick:
            run_quick_benchmark()
        else:
            run_all_benchmarks()
        
        if not args.no_save:
            print(f"\nResults saved to {args.save}")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Benchmark interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Benchmark failed: {e}")
        sys.exit(1)