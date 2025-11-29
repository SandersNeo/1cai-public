# [NEXUS IDENTITY] ID: -3171894260982818376 | DATE: 2025-11-19

"""
Dependencies Health Check Endpoint
Проверка состояния зависимостей: БД, Redis, внешние API
"""

import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import aiohttp
import asyncpg
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class DependencyStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    TIMEOUT = "timeout"
    CONNECTION_ERROR = "connection_error"

@dataclass
class DependencyCheck:
    """Результат проверки одной зависимости"""
    name: str
    type: str  # database, redis, api, service
    status: DependencyStatus
    response_time_ms: float
    details: Dict[str, Any]
    error_message: Optional[str] = None
    last_success: Optional[str] = None

@dataclass
class DependenciesHealthInfo:
    """Полная информация о состоянии зависимостей"""
    overall_status: DependencyStatus
    check_time: str
    total_dependencies: int
    healthy_count: int
    degraded_count: int
    unhealthy_count: int
    dependencies: List[DependencyCheck]

class DependenciesHealthChecker:
    """Проверяльщик состояния зависимостей"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.timeout = config.get('timeout_seconds', 5)
        self.max_retries = config.get('max_retries', 3)
        
    async def check_database(self, db_config: Dict[str, Any]) -> DependencyCheck:
        """Проверка состояния базы данных"""
        start_time = time.time()
        name = db_config.get('name', 'database')
        
        try:
            # Создание подключения к PostgreSQL
            connection = await asyncpg.connect(
                host=db_config['host'],
                port=db_config.get('port', 5432),
                user=db_config['user'],
                password=db_config['password'],
                database=db_config['database'],
                timeout=self.timeout
            )
            
            # Выполнение простого запроса
            await connection.execute('SELECT 1')
            await connection.close()
            
            response_time = (time.time() - start_time) * 1000
            
            # Дополнительная информация
            details = {
                'host': db_config['host'],
                'port': db_config.get('port', 5432),
                'database': db_config['database'],
                'connection_successful': True
            }
            
            status = DependencyStatus.HEALTHY
            if response_time > 1000:  # Медленное соединение
                status = DependencyStatus.DEGRADED
            
            return DependencyCheck(
                name=name,
                type='database',
                status=status,
                response_time_ms=response_time,
                details=details,
                last_success=datetime.now().isoformat()
            )
            
        except asyncio.TimeoutError:
            return DependencyCheck(
                name=name,
                type='database',
                status=DependencyStatus.TIMEOUT,
                response_time_ms=self.timeout * 1000,
                details={'host': db_config['host']},
                error_message="Connection timeout"
            )
        except Exception as e:
            return DependencyCheck(
                name=name,
                type='database',
                status=DependencyStatus.CONNECTION_ERROR,
                response_time_ms=(time.time() - start_time) * 1000,
                details={'host': db_config['host']},
                error_message=str(e)
            )
    
    async def check_redis(self, redis_config: Dict[str, Any]) -> DependencyCheck:
        """Проверка состояния Redis"""
        start_time = time.time()
        name = redis_config.get('name', 'redis')
        
        try:
            # Создание подключения к Redis
            redis_client = redis.Redis(
                host=redis_config['host'],
                port=redis_config.get('port', 6379),
                password=redis_config.get('password'),
                decode_responses=True,
                socket_timeout=self.timeout
            )
            
            # Выполнение простой команды
            result = await redis_client.ping()
            await redis_client.close()
            
            if not result:
                raise Exception("Redis ping failed")
            
            response_time = (time.time() - start_time) * 1000
            
            details = {
                'host': redis_config['host'],
                'port': redis_config.get('port', 6379),
                'ping_successful': True
            }
            
            status = DependencyStatus.HEALTHY
            if response_time > 500:  # Медленный Redis
                status = DependencyStatus.DEGRADED
            
            return DependencyCheck(
                name=name,
                type='redis',
                status=status,
                response_time_ms=response_time,
                details=details,
                last_success=datetime.now().isoformat()
            )
            
        except asyncio.TimeoutError:
            return DependencyCheck(
                name=name,
                type='redis',
                status=DependencyStatus.TIMEOUT,
                response_time_ms=self.timeout * 1000,
                details={'host': redis_config['host']},
                error_message="Redis connection timeout"
            )
        except Exception as e:
            return DependencyCheck(
                name=name,
                type='redis',
                status=DependencyStatus.CONNECTION_ERROR,
                response_time_ms=(time.time() - start_time) * 1000,
                details={'host': redis_config['host']},
                error_message=str(e)
            )
    
    async def check_api(self, api_config: Dict[str, Any]) -> DependencyCheck:
        """Проверка состояния внешнего API"""
        start_time = time.time()
        name = api_config.get('name', 'api')
        url = api_config['url']
        method = api_config.get('method', 'GET').upper()
        headers = api_config.get('headers', {})
        expected_status = api_config.get('expected_status', 200)
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.request(method, url, headers=headers) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    details = {
                        'url': url,
                        'method': method,
                        'status_code': response.status,
                        'expected_status': expected_status
                    }
                    
                    if response.status == expected_status:
                        status = DependencyStatus.HEALTHY
                        if response_time > 2000:  # Медленный API
                            status = DependencyStatus.DEGRADED
                    elif 400 <= response.status < 500:
                        status = DependencyStatus.DEGRADED
                    else:
                        status = DependencyStatus.UNHEALTHY
                    
                    return DependencyCheck(
                        name=name,
                        type='api',
                        status=status,
                        response_time_ms=response_time,
                        details=details,
                        last_success=datetime.now().isoformat()
                    )
                    
        except asyncio.TimeoutError:
            return DependencyCheck(
                name=name,
                type='api',
                status=DependencyStatus.TIMEOUT,
                response_time_ms=self.timeout * 1000,
                details={'url': url},
                error_message="API request timeout"
            )
        except Exception as e:
            return DependencyCheck(
                name=name,
                type='api',
                status=DependencyStatus.CONNECTION_ERROR,
                response_time_ms=(time.time() - start_time) * 1000,
                details={'url': url},
                error_message=str(e)
            )
    
    async def check_service(self, service_config: Dict[str, Any]) -> DependencyCheck:
        """Проверка внутреннего сервиса"""
        start_time = time.time()
        name = service_config.get('name', 'service')
        url = service_config['url']
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(f"{url}/health") as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    details = {
                        'service_url': url,
                        'health_endpoint': f"{url}/health",
                        'status_code': response.status
                    }
                    
                    if response.status == 200:
                        status = DependencyStatus.HEALTHY
                        if response_time > 500:
                            status = DependencyStatus.DEGRADED
                    elif response.status == 503:
                        status = DependencyStatus.DEGRADED
                    else:
                        status = DependencyStatus.UNHEALTHY
                    
                    return DependencyCheck(
                        name=name,
                        type='service',
                        status=status,
                        response_time_ms=response_time,
                        details=details,
                        last_success=datetime.now().isoformat()
                    )
                    
        except asyncio.TimeoutError:
            return DependencyCheck(
                name=name,
                type='service',
                status=DependencyStatus.TIMEOUT,
                response_time_ms=self.timeout * 1000,
                details={'service_url': url},
                error_message="Service health check timeout"
            )
        except Exception as e:
            return DependencyCheck(
                name=name,
                type='service',
                status=DependencyStatus.CONNECTION_ERROR,
                response_time_ms=(time.time() - start_time) * 1000,
                details={'service_url': url},
                error_message=str(e)
            )
    
    async def check_all_dependencies(self) -> DependenciesHealthInfo:
        """Проверить все зависимости"""
        check_time = datetime.now()
        all_checks = []
        
        # Проверка баз данных
        if 'databases' in self.config:
            for db_config in self.config['databases']:
                check = await self.check_database(db_config)
                all_checks.append(check)
        
        # Проверка Redis
        if 'redis' in self.config:
            for redis_config in self.config['redis']:
                check = await self.check_redis(redis_config)
                all_checks.append(check)
        
        # Проверка API
        if 'apis' in self.config:
            for api_config in self.config['apis']:
                check = await self.check_api(api_config)
                all_checks.append(check)
        
        # Проверка сервисов
        if 'services' in self.config:
            for service_config in self.config['services']:
                check = await self.check_service(service_config)
                all_checks.append(check)
        
        # Подсчет статусов
        healthy_count = sum(1 for check in all_checks if check.status == DependencyStatus.HEALTHY)
        degraded_count = sum(1 for check in all_checks if check.status == DependencyStatus.DEGRADED)
        unhealthy_count = sum(1 for check in all_checks if check.status in [
            DependencyStatus.UNHEALTHY, 
            DependencyStatus.TIMEOUT, 
            DependencyStatus.CONNECTION_ERROR
        ])
        
        # Определение общего статуса
        if unhealthy_count > 0:
            overall_status = DependencyStatus.UNHEALTHY
        elif degraded_count > 0:
            overall_status = DependencyStatus.DEGRADED
        else:
            overall_status = DependencyStatus.HEALTHY
        
        return DependenciesHealthInfo(
            overall_status=overall_status,
            check_time=check_time.isoformat(),
            total_dependencies=len(all_checks),
            healthy_count=healthy_count,
            degraded_count=degraded_count,
            unhealthy_count=unhealthy_count,
            dependencies=all_checks
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в словарь"""
        # Асинхронный метод, нужно использовать asyncio.run
        raise NotImplementedError("Use async_check() instead")
    
    async def async_check(self) -> Dict[str, Any]:
        """Асинхронная проверка с преобразованием в словарь"""
        health_info = await self.check_all_dependencies()
        
        # Преобразование enum в строки
        dependencies_dict = []
        for dep in health_info.dependencies:
            dep_dict = asdict(dep)
            dep_dict['status'] = dep.status.value
            dependencies_dict.append(dep_dict)
        
        return {
            'overall_status': health_info.overall_status.value,
            'check_time': health_info.check_time,
            'total_dependencies': health_info.total_dependencies,
            'healthy_count': health_info.healthy_count,
            'degraded_count': health_info.degraded_count,
            'unhealthy_count': health_info.unhealthy_count,
            'dependencies': dependencies_dict
        }

# Конфигурация по умолчанию
DEFAULT_DEPENDENCIES_CONFIG = {
    'timeout_seconds': 5,
    'max_retries': 3,
    'databases': [
        {
            'name': 'main_postgres',
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', '5432')),
            'user': os.getenv('POSTGRES_USER', 'user'),
            'password': os.getenv('POSTGRES_PASSWORD', 'password'),
            'database': os.getenv('POSTGRES_DB', 'app_db')
        }
    ],
    'redis': [
        {
            'name': 'main_redis',
            'host': os.getenv('REDIS_HOST', 'localhost'),
            'port': int(os.getenv('REDIS_PORT', '6379')),
            'password': os.getenv('REDIS_PASSWORD')
        }
    ],
    'apis': [
        {
            'name': 'supabase_api',
            'url': os.getenv('SUPABASE_URL', ''),
            'headers': {
                'Authorization': f"Bearer {os.getenv('SUPABASE_ANON_KEY', '')}"
            },
            'expected_status': 200
        }
    ],
    'services': [
        {
            'name': 'api_gateway',
            'url': os.getenv('API_GATEWAY_URL', 'http://localhost:8000')
        },
        {
            'name': 'ml_service',
            'url': os.getenv('ML_SERVICE_URL', 'http://localhost:8001')
        }
    ]
}

if __name__ == "__main__":
    pass

    # Пример использования
    async def main():
        config = DEFAULT_DEPENDENCIES_CONFIG
        checker = DependenciesHealthChecker(config)
        result = await checker.async_check()
        print(json.dumps(result, indent=2))
    
    asyncio.run(main())