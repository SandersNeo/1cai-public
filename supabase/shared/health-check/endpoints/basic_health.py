# [NEXUS IDENTITY] ID: 2867578939902545171 | DATE: 2025-11-19

"""
Basic Health Check Endpoint
Проверка основного состояния сервиса
"""

import time
import psutil
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"

@dataclass
class BasicHealthInfo:
    """Базовая информация о состоянии сервиса"""
    status: HealthStatus
    service_name: str
    version: str
    start_time: float
    uptime_seconds: int
    current_time: str
    hostname: str
    pid: int
    memory_usage_mb: float
    cpu_percent: float
    disk_usage_percent: float
    load_average: list
    response_time_ms: float
    error_message: Optional[str] = None

class BasicHealthChecker:
    """Базовый проверяльщик состояния сервиса"""
    
    def __init__(self, service_name: str, version: str):
        self.service_name = service_name
        self.version = version
        self.start_time = time.time()
        self.hostname = os.getenv('HOSTNAME', 'unknown')
        self.pid = os.getpid()
        
    def get_uptime(self) -> int:
        """Получить время работы сервиса в секундах"""
        return int(time.time() - self.start_time)
    
    def get_system_metrics(self) -> Dict[str, float]:
        """Получить системные метрики"""
        try:
            # Использование psutil для получения метрик
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            cpu_percent = psutil.cpu_percent(interval=1)
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else [0.0, 0.0, 0.0]
            
            return {
                'memory_usage_mb': memory.used / (1024 * 1024),
                'memory_available_mb': memory.available / (1024 * 1024),
                'memory_percent': memory.percent,
                'cpu_percent': cpu_percent,
                'disk_usage_percent': (disk.used / disk.total) * 100,
                'disk_free_gb': disk.free / (1024 * 1024 * 1024),
                'load_average': list(load_avg),
                'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat()
            }
        except Exception as e:
            return {
                'memory_usage_mb': 0.0,
                'cpu_percent': 0.0,
                'disk_usage_percent': 0.0,
                'load_average': [0.0, 0.0, 0.0],
                'error': str(e)
            }
    
    def determine_status(self, metrics: Dict[str, float]) -> HealthStatus:
        """Определить статус на основе метрик"""
        try:
            # Критические пороги
            if metrics.get('memory_percent', 0) > 95:
                return HealthStatus.CRITICAL
            
            if metrics.get('cpu_percent', 0) > 95:
                return HealthStatus.CRITICAL
            
            if metrics.get('disk_usage_percent', 0) > 95:
                return HealthStatus.CRITICAL
            
            # Предупреждающие пороги
            if metrics.get('memory_percent', 0) > 85:
                return HealthStatus.DEGRADED
            
            if metrics.get('cpu_percent', 0) > 80:
                return HealthStatus.DEGRADED
            
            if metrics.get('disk_usage_percent', 0) > 80:
                return HealthStatus.DEGRADED
            
            return HealthStatus.HEALTHY
            
        except Exception:
            return HealthStatus.UNHEALTHY
    
    def check(self) -> BasicHealthInfo:
        """Выполнить базовую проверку здоровья"""
        start_check_time = time.time()
        
        try:
            metrics = self.get_system_metrics()
            status = self.determine_status(metrics)
            uptime = self.get_uptime()
            
            health_info = BasicHealthInfo(
                status=status,
                service_name=self.service_name,
                version=self.version,
                start_time=self.start_time,
                uptime_seconds=uptime,
                current_time=datetime.now().isoformat(),
                hostname=self.hostname,
                pid=self.pid,
                memory_usage_mb=metrics.get('memory_usage_mb', 0.0),
                cpu_percent=metrics.get('cpu_percent', 0.0),
                disk_usage_percent=metrics.get('disk_usage_percent', 0.0),
                load_average=metrics.get('load_average', [0.0, 0.0, 0.0]),
                response_time_ms=(time.time() - start_check_time) * 1000
            )
            
            return health_info
            
        except Exception as e:
            return BasicHealthInfo(
                status=HealthStatus.UNHEALTHY,
                service_name=self.service_name,
                version=self.version,
                start_time=self.start_time,
                uptime_seconds=self.get_uptime(),
                current_time=datetime.now().isoformat(),
                hostname=self.hostname,
                pid=self.pid,
                memory_usage_mb=0.0,
                cpu_percent=0.0,
                disk_usage_percent=0.0,
                load_average=[0.0, 0.0, 0.0],
                response_time_ms=0.0,
                error_message=str(e)
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в словарь для JSON"""
        return asdict(self.check())
    
    def to_json(self) -> str:
        """Преобразовать в JSON строку"""
        return json.dumps(self.to_dict(), indent=2, default=str)

# FastAPI endpoint
def create_basic_health_endpoint(app, service_name: str, version: str):
    """Создать FastAPI endpoint для базовой проверки здоровья"""
    
    @app.get("/health/basic")
    async def basic_health():
        """Базовая проверка здоровья сервиса"""
        checker = BasicHealthChecker(service_name, version)
        return checker.to_dict()
    
    @app.get("/health")
    async def root_health():
        """Корневой endpoint для проверки здоровья"""
        checker = BasicHealthChecker(service_name, version)
        return checker.to_dict()

# Flask endpoint
def create_basic_health_blueprint(service_name: str, version: str):
    """Создать Flask blueprint для базовой проверки здоровья"""
    from flask import Blueprint, jsonify
    
    health_bp = Blueprint('health', __name__)
    
    @health_bp.route('/health/basic')
    def basic_health():
        """Базовая проверка здоровья сервиса"""
        checker = BasicHealthChecker(service_name, version)
        return jsonify(checker.to_dict())
    
    @health_bp.route('/health')
    def root_health():
        """Корневой endpoint для проверки здоровья"""
        checker = BasicHealthChecker(service_name, version)
        return jsonify(checker.to_dict())
    
    return health_bp

if __name__ == "__main__":
    # Пример использования
    checker = BasicHealthChecker("ai-assistant-service", "1.0.0")
    print(checker.to_json())