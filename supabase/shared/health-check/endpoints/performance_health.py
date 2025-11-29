# [NEXUS IDENTITY] ID: -6942207176650117971 | DATE: 2025-11-19

"""
Performance Health Check Endpoint
Проверка производительности: время отклика, память, нагрузка
"""

import asyncio
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

import aiohttp
import psutil


class PerformanceStatus(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    DEGRADED = "degraded"
    POOR = "poor"
    CRITICAL = "critical"

@dataclass
class PerformanceMetrics:
    """Метрики производительности"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    load_average: List[float]
    process_count: int
    thread_count: int
    file_descriptors: int

@dataclass
class PerformanceCheck:
    """Результат проверки производительности"""
    name: str
    status: PerformanceStatus
    response_time_ms: float
    current_metrics: PerformanceMetrics
    thresholds: Dict[str, float]
    recommendations: List[str]
    performance_score: float
    bottlenecks: List[str]

@dataclass
class PerformanceHealthInfo:
    """Полная информация о производительности"""
    overall_status: PerformanceStatus
    check_time: str
    performance_score: float
    current_metrics: PerformanceMetrics
    historical_metrics: List[Dict[str, Any]]
    trends: Dict[str, str]  # improving, degrading, stable
    bottlenecks: List[str]
    recommendations: List[str]
    alert_thresholds: Dict[str, float]

class PerformanceMonitor:
    """Монитор производительности системы"""
    
    def __init__(self):
        self.baseline_metrics = {}
        self.history = []
        self.max_history_size = 100
    
    def get_current_metrics(self) -> PerformanceMetrics:
        """Получить текущие метрики производительности"""
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Память
        memory = psutil.virtual_memory()
        
        # Диск I/O
        disk_io = psutil.disk_io_counters()
        disk_read_mb = disk_io.read_bytes / (1024 * 1024) if disk_io else 0
        disk_write_mb = disk_io.write_bytes / (1024 * 1024) if disk_io else 0
        
        # Сетевой I/O
        network_io = psutil.net_io_counters()
        network_sent_mb = network_io.bytes_sent / (1024 * 1024) if network_io else 0
        network_recv_mb = network_io.bytes_recv / (1024 * 1024) if network_io else 0
        
        # Load average
        load_avg = list(os.getloadavg()) if hasattr(os, 'getloadavg') else [0.0, 0.0, 0.0]
        
        # Процессы и потоки
        process_count = len(psutil.pids())
        
        try:
            current_process = psutil.Process()
            thread_count = current_process.num_threads()
            file_descriptors = current_process.num_fds() if hasattr(current_process, 'num_fds') else 0
        except:
            thread_count = 0
            file_descriptors = 0
        
        return PerformanceMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / (1024 * 1024),
            memory_available_mb=memory.available / (1024 * 1024),
            disk_io_read_mb=disk_read_mb,
            disk_io_write_mb=disk_write_mb,
            network_sent_mb=network_sent_mb,
            network_recv_mb=network_recv_mb,
            load_average=load_avg,
            process_count=process_count,
            thread_count=thread_count,
            file_descriptors=file_descriptors
        )
    
    def calculate_performance_score(self, metrics: PerformanceMetrics, thresholds: Dict[str, float]) -> float:
        """Вычислить общий балл производительности (0-100)"""
        score = 100.0
        penalties = []
        
        # CPU penalty
        if metrics.cpu_percent > thresholds.get('cpu_critical', 95):
            score -= 30
            penalties.append("Критическая загрузка CPU")
        elif metrics.cpu_percent > thresholds.get('cpu_warning', 80):
            score -= 15
            penalties.append("Высокая загрузка CPU")
        elif metrics.cpu_percent > thresholds.get('cpu_normal', 60):
            score -= 5
        
        # Memory penalty
        if metrics.memory_percent > thresholds.get('memory_critical', 95):
            score -= 25
            penalties.append("Критическое использование памяти")
        elif metrics.memory_percent > thresholds.get('memory_warning', 85):
            score -= 12
            penalties.append("Высокое использование памяти")
        elif metrics.memory_percent > thresholds.get('memory_normal', 70):
            score -= 3
        
        # Load average penalty
        load_1min = metrics.load_average[0]
        cpu_count = psutil.cpu_count()
        if load_1min > cpu_count * 2:
            score -= 20
            penalties.append("Слишком высокая нагрузка системы")
        elif load_1min > cpu_count * 1.5:
            score -= 10
            penalties.append("Повышенная нагрузка системы")
        
        # Thread count penalty
        if metrics.thread_count > thresholds.get('threads_warning', 1000):
            score -= 10
            penalties.append("Слишком много потоков")
        
        # File descriptors penalty
        if metrics.file_descriptors > thresholds.get('fds_warning', 1000):
            score -= 5
            penalties.append("Много открытых файлов")
        
        return max(0.0, score)
    
    def determine_status(self, score: float, metrics: PerformanceMetrics) -> PerformanceStatus:
        """Определить статус производительности"""
        if score >= 90 and metrics.cpu_percent < 50 and metrics.memory_percent < 60:
            return PerformanceStatus.EXCELLENT
        elif score >= 80:
            return PerformanceStatus.GOOD
        elif score >= 65:
            return PerformanceStatus.ACCEPTABLE
        elif score >= 50:
            return PerformanceStatus.DEGRADED
        elif score >= 30:
            return PerformanceStatus.POOR
        else:
            return PerformanceStatus.CRITICAL
    
    def analyze_trends(self) -> Dict[str, str]:
        """Анализ трендов производительности"""
        if len(self.history) < 5:
            return {"trend": "insufficient_data"}
        
        # Анализ последних 5 измерений
        recent_metrics = self.history[-5:]
        
        cpu_trend = self._calculate_trend([m['cpu_percent'] for m in recent_metrics])
        memory_trend = self._calculate_trend([m['memory_percent'] for m in recent_metrics])
        load_trend = self._calculate_trend([m['load_average'][0] for m in recent_metrics])
        
        return {
            'cpu_trend': cpu_trend,
            'memory_trend': memory_trend,
            'load_trend': load_trend
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Вычислить тренд для последовательности значений"""
        if len(values) < 3:
            return "stable"
        
        # Простая линейная регрессия
        n = len(values)
        x = list(range(n))
        
        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(x[i] * values[i] for i in range(n))
        sum_x2 = sum(xi * xi for xi in x)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        if slope > 0.5:
            return "degrading"
        elif slope < -0.5:
            return "improving"
        else:
            return "stable"

class PerformanceHealthChecker:
    """Проверяльщик производительности"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.monitor = PerformanceMonitor()
        self.thresholds = config.get('thresholds', {
            'cpu_normal': 60,
            'cpu_warning': 80,
            'cpu_critical': 95,
            'memory_normal': 70,
            'memory_warning': 85,
            'memory_critical': 95,
            'threads_warning': 1000,
            'fds_warning': 1000
        })
    
    async def check_endpoint_performance(self, endpoint_url: str, method: str = "GET", 
                                       timeout: int = 10) -> Dict[str, Any]:
        """Проверить производительность endpoint'а"""
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as session:
                async with session.request(method, endpoint_url) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    return {
                        'endpoint': endpoint_url,
                        'method': method,
                        'status_code': response.status,
                        'response_time_ms': response_time,
                        'success': response.status < 400
                    }
                    
        except asyncio.TimeoutError:
            return {
                'endpoint': endpoint_url,
                'method': method,
                'status_code': 408,
                'response_time_ms': timeout * 1000,
                'success': False,
                'error': 'timeout'
            }
        except Exception as e:
            return {
                'endpoint': endpoint_url,
                'method': method,
                'status_code': 500,
                'response_time_ms': (time.time() - start_time) * 1000,
                'success': False,
                'error': str(e)
            }
    
    async def check_all_endpoints(self) -> List[Dict[str, Any]]:
        """Проверить производительность всех endpoints"""
        endpoints = self.config.get('endpoints', [
            {'url': '/health', 'method': 'GET'},
            {'url': '/health/dependencies', 'method': 'GET'},
            {'url': '/health/business', 'method': 'GET'},
            {'url': '/health/performance', 'method': 'GET'},
            {'url': '/metrics', 'method': 'GET'}
        ])
        
        base_url = self.config.get('base_url', 'http://localhost:8000')
        
        tasks = []
        for endpoint in endpoints:
            url = f"{base_url}{endpoint['url']}"
            method = endpoint.get('method', 'GET')
            timeout = endpoint.get('timeout', 10)
            
            task = self.check_endpoint_performance(url, method, timeout)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        return results
    
    async def check_performance(self) -> PerformanceHealthInfo:
        """Полная проверка производительности"""
        check_time = datetime.now()
        
        # Получение системных метрик
        current_metrics = self.monitor.get_current_metrics()
        
        # Вычисление балла производительности
        performance_score = self.monitor.calculate_performance_score(
            current_metrics, self.thresholds
        )
        
        # Определение статуса
        overall_status = self.monitor.determine_status(performance_score, current_metrics)
        
        # Проверка bottlenecks
        bottlenecks = self._identify_bottlenecks(current_metrics)
        
        # Проверка endpoints
        endpoint_results = await self.check_all_endpoints()
        slow_endpoints = [r for r in endpoint_results if r.get('response_time_ms', 0) > 2000]
        failed_endpoints = [r for r in endpoint_results if not r.get('success', True)]
        
        bottlenecks.extend([f"Slow endpoint: {r['endpoint']}" for r in slow_endpoints])
        bottlenecks.extend([f"Failed endpoint: {r['endpoint']}" for r in failed_endpoints])
        
        # Генерация рекомендаций
        recommendations = self._generate_recommendations(
            current_metrics, overall_status, bottlenecks
        )
        
        # Анализ трендов
        trends = self.monitor.analyze_trends()
        
        # Сохранение в историю
        history_entry = {
            'timestamp': check_time.isoformat(),
            'metrics': asdict(current_metrics),
            'score': performance_score,
            'status': overall_status.value
        }
        
        self.monitor.history.append(history_entry)
        if len(self.monitor.history) > self.monitor.max_history_size:
            self.monitor.history.pop(0)
        
        return PerformanceHealthInfo(
            overall_status=overall_status,
            check_time=check_time.isoformat(),
            performance_score=performance_score,
            current_metrics=current_metrics,
            historical_metrics=self.monitor.history[-10:],  # Последние 10 записей
            trends=trends,
            bottlenecks=bottlenecks,
            recommendations=recommendations,
            alert_thresholds=self.thresholds
        )
    
    def _identify_bottlenecks(self, metrics: PerformanceMetrics) -> List[str]:
        """Идентифицировать узкие места производительности"""
        bottlenecks = []
        
        if metrics.cpu_percent > 80:
            bottlenecks.append(f"High CPU usage: {metrics.cpu_percent:.1f}%")
        
        if metrics.memory_percent > 85:
            bottlenecks.append(f"High memory usage: {metrics.memory_percent:.1f}%")
        
        if metrics.load_average[0] > psutil.cpu_count() * 1.5:
            bottlenecks.append(f"High system load: {metrics.load_average[0]:.2f}")
        
        if metrics.thread_count > 1000:
            bottlenecks.append(f"High thread count: {metrics.thread_count}")
        
        return bottlenecks
    
    def _generate_recommendations(self, metrics: PerformanceMetrics, 
                                status: PerformanceStatus, 
                                bottlenecks: List[str]) -> List[str]:
        """Генерировать рекомендации по улучшению производительности"""
        recommendations = []
        
        if status in [PerformanceStatus.POOR, PerformanceStatus.CRITICAL]:
            recommendations.append("🚨 Критические проблемы производительности требуют немедленного внимания")
        
        if metrics.cpu_percent > 80:
            recommendations.append("💻 Оптимизировать использование CPU или добавить вычислительные ресурсы")
        
        if metrics.memory_percent > 85:
            recommendations.append("🧠 Увеличить объем памяти или оптимизировать использование")
        
        if "system load" in " ".join(bottlenecks):
            recommendations.append("⚖️ Проверить процессы с высокой нагрузкой")
        
        if metrics.load_average[0] > psutil.cpu_count() * 2:
            recommendations.append("📈 Рассмотреть горизонтальное масштабирование")
        
        if status == PerformanceStatus.EXCELLENT:
            recommendations.append("✅ Система работает оптимально")
        
        return recommendations
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в словарь"""
        # Асинхронный метод, нужно использовать asyncio.run
        raise NotImplementedError("Use async_check() instead")
    
    async def async_check(self) -> Dict[str, Any]:
        """Асинхронная проверка с преобразованием в словарь"""
        health_info = await self.check_performance()
        
        # Преобразование enum в строки
        result = asdict(health_info)
        result['overall_status'] = health_info.overall_status.value
        
        return result

# Конфигурация по умолчанию
DEFAULT_PERFORMANCE_CONFIG = {
    'base_url': 'http://localhost:8000',
    'endpoints': [
        {'url': '/health', 'method': 'GET', 'timeout': 5},
        {'url': '/health/dependencies', 'method': 'GET', 'timeout': 10},
        {'url': '/health/business', 'method': 'GET', 'timeout': 10},
        {'url': '/health/performance', 'method': 'GET', 'timeout': 5},
        {'url': '/metrics', 'method': 'GET', 'timeout': 5}
    ],
    'thresholds': {
        'cpu_normal': 60,
        'cpu_warning': 80,
        'cpu_critical': 95,
        'memory_normal': 70,
        'memory_warning': 85,
        'memory_critical': 95,
        'threads_warning': 1000,
        'fds_warning': 1000
    }
}

if __name__ == "__main__":
    # Пример использования
    async def main():
        config = DEFAULT_PERFORMANCE_CONFIG
        checker = PerformanceHealthChecker(config)
        result = await checker.async_check()
        print(json.dumps(result, indent=2, default=str))
    
    asyncio.run(main())