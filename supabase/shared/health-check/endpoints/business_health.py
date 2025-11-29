# [NEXUS IDENTITY] ID: -6024607116270253605 | DATE: 2025-11-19

"""
Business Logic Health Check Endpoint
Проверка критических бизнес-функций
"""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import aiohttp


class BusinessHealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    MAINTENANCE = "maintenance"

@dataclass
class BusinessCheck:
    """Результат проверки бизнес-логики"""
    name: str
    category: str  # auth, data, processing, storage, integration
    status: BusinessHealthStatus
    response_time_ms: float
    details: Dict[str, Any]
    metrics: Dict[str, float]
    recommendations: List[str]
    last_success: Optional[str] = None
    error_message: Optional[str] = None

@dataclass
class BusinessHealthInfo:
    """Полная информация о состоянии бизнес-логики"""
    overall_status: BusinessHealthStatus
    check_time: str
    total_checks: int
    healthy_count: int
    degraded_count: int
    unhealthy_count: int
    critical_count: int
    categories: Dict[str, int]  # count by category
    checks: List[BusinessCheck]
    critical_functions: List[str]
    performance_trends: Dict[str, Any]

class BusinessFunctionChecker(ABC):
    """Абстрактный класс для проверки бизнес-функций"""
    
    @abstractmethod
    async def check(self) -> BusinessCheck:
        """Выполнить проверку функции"""

class AuthenticationChecker(BusinessFunctionChecker):
    """Проверка системы аутентификации"""
    
    def __init__(self, auth_service_url: str, timeout: int = 5):
        self.auth_service_url = auth_service_url
        self.timeout = timeout
    
    async def check(self) -> BusinessCheck:
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as session:
                # Проверка login endpoint
                async with session.get(f"{self.auth_service_url}/auth/health") as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    details = {
                        'auth_endpoint': f"{self.auth_service_url}/auth/health",
                        'status_code': response.status,
                        'login_available': response.status == 200
                    }
                    
                    if response.status == 200:
                        status = BusinessHealthStatus.HEALTHY
                        if response_time > 1000:
                            status = BusinessHealthStatus.DEGRADED
                    else:
                        status = BusinessHealthStatus.UNHEALTHY
                    
                    recommendations = []
                    if status == BusinessHealthStatus.DEGRADED:
                        recommendations.append("Проверить производительность сервера аутентификации")
                    elif status == BusinessHealthStatus.UNHEALTHY:
                        recommendations.append("Проверить доступность сервиса аутентификации")
                    
                    return BusinessCheck(
                        name="Authentication System",
                        category="auth",
                        status=status,
                        response_time_ms=response_time,
                        details=details,
                        metrics={'auth_response_time': response_time},
                        recommendations=recommendations,
                        last_success=datetime.now().isoformat()
                    )
                    
        except Exception as e:
            return BusinessCheck(
                name="Authentication System",
                category="auth",
                status=BusinessHealthStatus.CRITICAL,
                response_time_ms=(time.time() - start_time) * 1000,
                details={'error': str(e)},
                metrics={},
                recommendations=[
                    "Проверить доступность сервиса аутентификации",
                    "Проверить сетевое подключение",
                    "Проверить конфигурацию DNS"
                ],
                error_message=str(e)
            )

class DataProcessingChecker(BusinessFunctionChecker):
    """Проверка системы обработки данных"""
    
    def __init__(self, ml_service_url: str, timeout: int = 10):
        self.ml_service_url = ml_service_url
        self.timeout = timeout
    
    async def check(self) -> BusinessCheck:
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as session:
                # Тестовый запрос к ML сервису
                test_data = {
                    'test': True,
                    'operation': 'health_check'
                }
                
                async with session.post(
                    f"{self.ml_service_url}/ml/process",
                    json=test_data
                ) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    details = {
                        'ml_endpoint': f"{self.ml_service_url}/ml/process",
                        'status_code': response.status,
                        'test_data_sent': True
                    }
                    
                    if response.status == 200:
                        result = await response.json()
                        details.update(result)
                        status = BusinessHealthStatus.HEALTHY
                        
                        if response_time > 5000:
                            status = BusinessHealthStatus.DEGRADED
                    else:
                        status = BusinessHealthStatus.UNHEALTHY
                    
                    recommendations = []
                    if status == BusinessHealthStatus.DEGRADED:
                        recommendations.append("Оптимизировать алгоритмы ML")
                        recommendations.append("Проверить производительность GPU/CPU")
                    elif status == BusinessHealthStatus.UNHEALTHY:
                        recommendations.append("Проверить состояние ML модели")
                        recommendations.append("Проверить зависимости ML сервиса")
                    
                    return BusinessCheck(
                        name="Data Processing (ML)",
                        category="processing",
                        status=status,
                        response_time_ms=response_time,
                        details=details,
                        metrics={'ml_response_time': response_time},
                        recommendations=recommendations,
                        last_success=datetime.now().isoformat()
                    )
                    
        except Exception as e:
            return BusinessCheck(
                name="Data Processing (ML)",
                category="processing",
                status=BusinessHealthStatus.CRITICAL,
                response_time_ms=(time.time() - start_time) * 1000,
                details={'error': str(e)},
                metrics={},
                recommendations=[
                    "Проверить доступность ML сервиса",
                    "Проверить состояние GPU/CPU",
                    "Проверить зависимости модели"
                ],
                error_message=str(e)
            )

class DataIntegrityChecker(BusinessFunctionChecker):
    """Проверка целостности данных"""
    
    def __init__(self, db_service_url: str, timeout: int = 5):
        self.db_service_url = db_service_url
        self.timeout = timeout
    
    async def check(self) -> BusinessCheck:
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as session:
                # Проверка целостности БД
                async with session.get(f"{self.db_service_url}/db/integrity") as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    details = {
                        'db_endpoint': f"{self.db_service_url}/db/integrity",
                        'status_code': response.status
                    }
                    
                    if response.status == 200:
                        result = await response.json()
                        details.update(result)
                        
                        # Анализ результатов целостности
                        integrity_score = result.get('integrity_score', 0)
                        
                        if integrity_score >= 0.95:
                            status = BusinessHealthStatus.HEALTHY
                        elif integrity_score >= 0.8:
                            status = BusinessHealthStatus.DEGRADED
                        else:
                            status = BusinessHealthStatus.UNHEALTHY
                        
                        recommendations = []
                        if integrity_score < 0.95:
                            recommendations.append("Выполнить проверку целостности данных")
                            recommendations.append("Резервное копирование критических данных")
                    else:
                        status = BusinessHealthStatus.UNHEALTHY
                        recommendations = ["Проверить состояние базы данных"]
                    
                    return BusinessCheck(
                        name="Data Integrity",
                        category="data",
                        status=status,
                        response_time_ms=response_time,
                        details=details,
                        metrics={'integrity_score': result.get('integrity_score', 0)},
                        recommendations=recommendations,
                        last_success=datetime.now().isoformat()
                    )
                    
        except Exception as e:
            return BusinessCheck(
                name="Data Integrity",
                category="data",
                status=BusinessHealthStatus.CRITICAL,
                response_time_ms=(time.time() - start_time) * 1000,
                details={'error': str(e)},
                metrics={},
                recommendations=[
                    "Проверить доступность базы данных",
                    "Проверить права доступа",
                    "Проверить сетевое подключение"
                ],
                error_message=str(e)
            )

class StorageChecker(BusinessFunctionChecker):
    """Проверка системы хранения"""
    
    def __init__(self, storage_service_url: str, timeout: int = 5):
        self.storage_service_url = storage_service_url
        self.timeout = timeout
    
    async def check(self) -> BusinessCheck:
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as session:
                # Проверка доступности хранилища
                async with session.get(f"{self.storage_service_url}/storage/health") as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    details = {
                        'storage_endpoint': f"{self.storage_service_url}/storage/health",
                        'status_code': response.status
                    }
                    
                    if response.status == 200:
                        result = await response.json()
                        details.update(result)
                        
                        # Проверка свободного места
                        free_space_percent = result.get('free_space_percent', 0)
                        
                        if free_space_percent >= 20:
                            status = BusinessHealthStatus.HEALTHY
                        elif free_space_percent >= 10:
                            status = BusinessHealthStatus.DEGRADED
                        else:
                            status = BusinessHealthStatus.UNHEALTHY
                        
                        recommendations = []
                        if free_space_percent < 20:
                            recommendations.append("Очистить неиспользуемые файлы")
                            recommendations.append("Расширить дисковое пространство")
                    else:
                        status = BusinessHealthStatus.UNHEALTHY
                        recommendations = ["Проверить состояние системы хранения"]
                    
                    return BusinessCheck(
                        name="Storage System",
                        category="storage",
                        status=status,
                        response_time_ms=response_time,
                        details=details,
                        metrics={'free_space_percent': result.get('free_space_percent', 0)},
                        recommendations=recommendations,
                        last_success=datetime.now().isoformat()
                    )
                    
        except Exception as e:
            return BusinessCheck(
                name="Storage System",
                category="storage",
                status=BusinessHealthStatus.CRITICAL,
                response_time_ms=(time.time() - start_time) * 1000,
                details={'error': str(e)},
                metrics={},
                recommendations=[
                    "Проверить доступность системы хранения",
                    "Проверить права доступа",
                    "Проверить сетевое подключение"
                ],
                error_message=str(e)
            )

class BusinessHealthChecker:
    """Основной проверяльщик бизнес-логики"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.checkers = []
        
        # Инициализация проверяльщиков
        if 'auth_service_url' in config:
            self.checkers.append(AuthenticationChecker(config['auth_service_url']))
        
        if 'ml_service_url' in config:
            self.checkers.append(DataProcessingChecker(config['ml_service_url']))
        
        if 'db_service_url' in config:
            self.checkers.append(DataIntegrityChecker(config['db_service_url']))
        
        if 'storage_service_url' in config:
            self.checkers.append(StorageChecker(config['storage_service_url']))
        
        # Добавление кастомных проверяльщиков
        for checker_config in config.get('custom_checkers', []):
            if checker_config['type'] == 'function':
                self.checkers.append(CustomFunctionChecker(checker_config))
    
    async def check_all_business_functions(self) -> BusinessHealthInfo:
        """Проверить все бизнес-функции"""
        check_time = datetime.now()
        all_checks = []
        
        # Параллельное выполнение всех проверок
        tasks = [checker.check() for checker in self.checkers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                # Обработка ошибок
                all_checks.append(BusinessCheck(
                    name="Unknown Function",
                    category="unknown",
                    status=BusinessHealthStatus.CRITICAL,
                    response_time_ms=0,
                    details={'exception': str(result)},
                    metrics={},
                    recommendations=["Проверить конфигурацию проверяльщика"],
                    error_message=str(result)
                ))
            else:
                all_checks.append(result)
        
        # Подсчет статусов
        healthy_count = sum(1 for check in all_checks if check.status == BusinessHealthStatus.HEALTHY)
        degraded_count = sum(1 for check in all_checks if check.status == BusinessHealthStatus.DEGRADED)
        unhealthy_count = sum(1 for check in all_checks if check.status == BusinessHealthStatus.UNHEALTHY)
        critical_count = sum(1 for check in all_checks if check.status == BusinessHealthStatus.CRITICAL)
        
        # Подсчет по категориям
        categories = {}
        for check in all_checks:
            categories[check.category] = categories.get(check.category, 0) + 1
        
        # Критические функции
        critical_functions = [
            check.name for check in all_checks 
            if check.status in [BusinessHealthStatus.UNHEALTHY, BusinessHealthStatus.CRITICAL]
        ]
        
        # Определение общего статуса
        if critical_count > 0:
            overall_status = BusinessHealthStatus.CRITICAL
        elif unhealthy_count > 0:
            overall_status = BusinessHealthStatus.UNHEALTHY
        elif degraded_count > 0:
            overall_status = BusinessHealthStatus.DEGRADED
        else:
            overall_status = BusinessHealthStatus.HEALTHY
        
        return BusinessHealthInfo(
            overall_status=overall_status,
            check_time=check_time.isoformat(),
            total_checks=len(all_checks),
            healthy_count=healthy_count,
            degraded_count=degraded_count,
            unhealthy_count=unhealthy_count,
            critical_count=critical_count,
            categories=categories,
            checks=all_checks,
            critical_functions=critical_functions,
            performance_trends={}
        )
    
    async def async_check(self) -> Dict[str, Any]:
        """Асинхронная проверка с преобразованием в словарь"""
        health_info = await self.check_all_business_functions()
        
        # Преобразование enum в строки
        checks_dict = []
        for check in health_info.checks:
            check_dict = asdict(check)
            check_dict['status'] = check.status.value
            checks_dict.append(check_dict)
        
        return {
            'overall_status': health_info.overall_status.value,
            'check_time': health_info.check_time,
            'total_checks': health_info.total_checks,
            'healthy_count': health_info.healthy_count,
            'degraded_count': health_info.degraded_count,
            'unhealthy_count': health_info.unhealthy_count,
            'critical_count': health_info.critical_count,
            'categories': health_info.categories,
            'checks': checks_dict,
            'critical_functions': health_info.critical_functions,
            'performance_trends': health_info.performance_trends
        }

class CustomFunctionChecker(BusinessFunctionChecker):
    """Кастомный проверяльщик функции"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config['name']
        self.category = config.get('category', 'custom')
        self.function = config['function']
        self.timeout = config.get('timeout', 5)
    
    async def check(self) -> BusinessCheck:
        start_time = time.time()
        
        try:
            if callable(self.function):
                # Если функция асинхронная
                if asyncio.iscoroutinefunction(self.function):
                    result = await asyncio.wait_for(
                        self.function(), 
                        timeout=self.timeout
                    )
                else:
                    # Синхронная функция
                    result = self.function()
                
                response_time = (time.time() - start_time) * 1000
                
                return BusinessCheck(
                    name=self.name,
                    category=self.category,
                    status=BusinessHealthStatus.HEALTHY,
                    response_time_ms=response_time,
                    details={'result': result},
                    metrics={},
                    recommendations=[],
                    last_success=datetime.now().isoformat()
                )
            else:
                raise Exception("Function is not callable")
                
        except asyncio.TimeoutError:
            return BusinessCheck(
                name=self.name,
                category=self.category,
                status=BusinessHealthStatus.TIMEOUT,
                response_time_ms=self.timeout * 1000,
                details={'timeout': self.timeout},
                metrics={},
                recommendations=["Оптимизировать функцию или увеличить таймаут"],
                error_message="Function execution timeout"
            )
        except Exception as e:
            return BusinessCheck(
                name=self.name,
                category=self.category,
                status=BusinessHealthStatus.CRITICAL,
                response_time_ms=(time.time() - start_time) * 1000,
                details={'error': str(e)},
                metrics={},
                recommendations=["Исправить ошибку в кастомной функции"],
                error_message=str(e)
            )

# Конфигурация по умолчанию
DEFAULT_BUSINESS_CONFIG = {
    'auth_service_url': os.getenv('AUTH_SERVICE_URL', 'http://localhost:8002'),
    'ml_service_url': os.getenv('ML_SERVICE_URL', 'http://localhost:8001'),
    'db_service_url': os.getenv('DB_SERVICE_URL', 'http://localhost:8003'),
    'storage_service_url': os.getenv('STORAGE_SERVICE_URL', 'http://localhost:8004'),
    'custom_checkers': []
}

if __name__ == "__main__":
    pass

    # Пример использования
    async def main():
        config = DEFAULT_BUSINESS_CONFIG
        checker = BusinessHealthChecker(config)
        result = await checker.async_check()
        print(json.dumps(result, indent=2))
    
    asyncio.run(main())