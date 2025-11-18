"""
Performance Benchmarks - Бенчмарки для всех компонентов
======================================================

Система бенчмарков для:
- Event-Driven Architecture
- Self-Evolving AI
- Self-Healing Code
- Distributed Network
- Code DNA
- Predictive Generation

Измерение:
- Latency
- Throughput
- Memory usage
- CPU usage
- Scalability
"""

import asyncio
import logging
import time
import tracemalloc
import psutil
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from statistics import mean, median, stdev

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Результат бенчмарка"""
    
    name: str
    iterations: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    p50_time: float
    p95_time: float
    p99_time: float
    throughput: float  # Операций в секунду
    memory_peak: float  # MB
    cpu_avg: float  # %
    errors: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация результата"""
        return {
            "name": self.name,
            "iterations": self.iterations,
            "total_time": self.total_time,
            "avg_time": self.avg_time,
            "min_time": self.min_time,
            "max_time": self.max_time,
            "p50_time": self.p50_time,
            "p95_time": self.p95_time,
            "p99_time": self.p99_time,
            "throughput": self.throughput,
            "memory_peak": self.memory_peak,
            "cpu_avg": self.cpu_avg,
            "errors": self.errors,
            "timestamp": self.timestamp.isoformat()
        }


class BenchmarkRunner:
    """Запуск бенчмарков"""
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
    
    async def benchmark_event_bus(
        self,
        event_bus,
        iterations: int = 1000,
        concurrent: int = 10
    ) -> BenchmarkResult:
        """Бенчмарк Event Bus"""
        from src.infrastructure.event_bus import Event, EventType
        
        tracemalloc.start()
        process = psutil.Process()
        cpu_before = process.cpu_percent()
        
        times = []
        errors = 0
        
        start_time = time.time()
        
        for i in range(iterations):
            try:
                iter_start = time.time()
                
                event = Event(
                    type=EventType.ML_TRAINING_STARTED,
                    payload={"iteration": i}
                )
                await event_bus.publish(event)
                
                iter_time = (time.time() - iter_start) * 1000  # ms
                times.append(iter_time)
            except Exception as e:
                errors += 1
                logger.error(f"Error in benchmark iteration {i}: {e}")
        
        total_time = time.time() - start_time
        
        # Статистика
        times_sorted = sorted(times)
        n = len(times_sorted)
        
        result = BenchmarkResult(
            name="event_bus_publish",
            iterations=iterations,
            total_time=total_time,
            avg_time=mean(times) if times else 0,
            min_time=min(times) if times else 0,
            max_time=max(times) if times else 0,
            p50_time=times_sorted[n//2] if times_sorted else 0,
            p95_time=times_sorted[int(n*0.95)] if times_sorted else 0,
            p99_time=times_sorted[int(n*0.99)] if times_sorted else 0,
            throughput=iterations / total_time if total_time > 0 else 0,
            memory_peak=tracemalloc.get_traced_memory()[1] / 1024 / 1024,  # MB
            cpu_avg=process.cpu_percent() - cpu_before,
            errors=errors
        )
        
        tracemalloc.stop()
        self.results.append(result)
        
        return result
    
    async def benchmark_self_evolving(
        self,
        evolving_ai,
        iterations: int = 10
    ) -> BenchmarkResult:
        """Бенчмарк Self-Evolving AI"""
        tracemalloc.start()
        process = psutil.Process()
        cpu_before = process.cpu_percent()
        
        times = []
        errors = 0
        
        start_time = time.time()
        
        for i in range(iterations):
            try:
                iter_start = time.time()
                await evolving_ai.evolve()
                iter_time = (time.time() - iter_start) * 1000
                times.append(iter_time)
            except Exception as e:
                errors += 1
                logger.error(f"Error in evolution {i}: {e}")
        
        total_time = time.time() - start_time
        
        times_sorted = sorted(times)
        n = len(times_sorted)
        
        result = BenchmarkResult(
            name="self_evolving_ai",
            iterations=iterations,
            total_time=total_time,
            avg_time=mean(times) if times else 0,
            min_time=min(times) if times else 0,
            max_time=max(times) if times else 0,
            p50_time=times_sorted[n//2] if times_sorted else 0,
            p95_time=times_sorted[int(n*0.95)] if times_sorted else 0,
            p99_time=times_sorted[int(n*0.99)] if times_sorted else 0,
            throughput=iterations / total_time if total_time > 0 else 0,
            memory_peak=tracemalloc.get_traced_memory()[1] / 1024 / 1024,
            cpu_avg=process.cpu_percent() - cpu_before,
            errors=errors
        )
        
        tracemalloc.stop()
        self.results.append(result)
        
        return result
    
    async def benchmark_self_healing(
        self,
        healing_code,
        iterations: int = 100
    ) -> BenchmarkResult:
        """Бенчмарк Self-Healing Code"""
        tracemalloc.start()
        process = psutil.Process()
        cpu_before = process.cpu_percent()
        
        times = []
        errors = 0
        
        start_time = time.time()
        
        for i in range(iterations):
            try:
                iter_start = time.time()
                
                # Симуляция ошибки
                error = ValueError(f"Test error {i}")
                await healing_code.handle_error(
                    error,
                    context={"file_path": "test.py", "line_number": i}
                )
                
                iter_time = (time.time() - iter_start) * 1000
                times.append(iter_time)
            except Exception as e:
                errors += 1
                logger.error(f"Error in healing {i}: {e}")
        
        total_time = time.time() - start_time
        
        times_sorted = sorted(times)
        n = len(times_sorted)
        
        result = BenchmarkResult(
            name="self_healing_code",
            iterations=iterations,
            total_time=total_time,
            avg_time=mean(times) if times else 0,
            min_time=min(times) if times else 0,
            max_time=max(times) if times else 0,
            p50_time=times_sorted[n//2] if times_sorted else 0,
            p95_time=times_sorted[int(n*0.95)] if times_sorted else 0,
            p99_time=times_sorted[int(n*0.99)] if times_sorted else 0,
            throughput=iterations / total_time if total_time > 0 else 0,
            memory_peak=tracemalloc.get_traced_memory()[1] / 1024 / 1024,
            cpu_avg=process.cpu_percent() - cpu_before,
            errors=errors
        )
        
        tracemalloc.stop()
        self.results.append(result)
        
        return result
    
    def get_all_results(self) -> List[BenchmarkResult]:
        """Получение всех результатов"""
        return self.results.copy()
    
    def generate_report(self) -> str:
        """Генерация отчета"""
        report = ["=" * 80]
        report.append("PERFORMANCE BENCHMARKS REPORT")
        report.append("=" * 80)
        report.append("")
        
        for result in self.results:
            report.append(f"Benchmark: {result.name}")
            report.append(f"  Iterations: {result.iterations}")
            report.append(f"  Total time: {result.total_time:.2f}s")
            report.append(f"  Avg time: {result.avg_time:.2f}ms")
            report.append(f"  P50: {result.p50_time:.2f}ms")
            report.append(f"  P95: {result.p95_time:.2f}ms")
            report.append(f"  P99: {result.p99_time:.2f}ms")
            report.append(f"  Throughput: {result.throughput:.2f} ops/sec")
            report.append(f"  Memory peak: {result.memory_peak:.2f} MB")
            report.append(f"  CPU avg: {result.cpu_avg:.2f}%")
            report.append(f"  Errors: {result.errors}")
            report.append("")
        
        return "\n".join(report)

