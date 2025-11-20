# [NEXUS IDENTITY] ID: -2543687953652327610 | DATE: 2025-11-19

"""
Health Check Endpoints Index
Объединяет все типы health checks
"""

from .basic_health import BasicHealthChecker, create_basic_health_endpoint, create_basic_health_blueprint
from .dependencies_health import DependenciesHealthChecker, DEFAULT_DEPENDENCIES_CONFIG
from .business_health import BusinessHealthChecker, DEFAULT_BUSINESS_CONFIG
from .performance_health import PerformanceHealthChecker, DEFAULT_PERFORMANCE_CONFIG
from .custom_metrics_health import CustomMetricsHealthChecker, DEFAULT_CUSTOM_METRICS_CONFIG

import os
from typing import Dict, Any, List
import asyncio

class ComprehensiveHealthChecker:
    """Комплексный проверяльщик здоровья системы"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Инициализация всех проверяльщиков
        self.basic_checker = BasicHealthChecker(
            service_name=self.config.get('service_name', 'unknown-service'),
            version=self.config.get('version', '1.0.0')
        )
        
        self.dependencies_checker = DependenciesHealthChecker(
            self.config.get('dependencies', DEFAULT_DEPENDENCIES_CONFIG)
        )
        
        self.business_checker = BusinessHealthChecker(
            self.config.get('business', DEFAULT_BUSINESS_CONFIG)
        )
        
        self.performance_checker = PerformanceHealthChecker(
            self.config.get('performance', DEFAULT_PERFORMANCE_CONFIG)
        )
        
        self.custom_metrics_checker = CustomMetricsHealthChecker(
            self.config.get('custom_metrics', DEFAULT_CUSTOM_METRICS_CONFIG)
        )
    
    async def comprehensive_check(self) -> Dict[str, Any]:
        """Выполнить комплексную проверку здоровья"""
        
        # Параллельное выполнение всех проверок
        tasks = [
            self._wrap_async_check('basic', self.basic_checker.async_check),
            self._wrap_async_check('dependencies', self.dependencies_checker.async_check),
            self._wrap_async_check('business', self.business_checker.async_check),
            self._wrap_async_check('performance', self.performance_checker.async_check),
            self._wrap_async_check('custom_metrics', self.custom_metrics_checker.async_check)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обработка результатов
        health_data = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                health_data[tasks[i].get_name()] = {
                    'status': 'error',
                    'error': str(result)
                }
            else:
                health_data[result['type']] = result['data']
        
        # Вычисление общего статуса
        overall_status = self._calculate_overall_status(health_data)
        
        return {
            'overall_status': overall_status,
            'timestamp': asyncio.get_event_loop().time(),
            'checks': health_data,
            'summary': self._generate_summary(health_data)
        }
    
    async def _wrap_async_check(self, check_type: str, check_func) -> Dict[str, Any]:
        """Обертка для асинхронной проверки"""
        try:
            if check_type == 'basic':
                # basic_checker не асинхронный
                data = check_func.to_dict()
            else:
                data = await check_func()
            
            return {'type': check_type, 'data': data}
        except Exception as e:
            return {'type': check_type, 'data': {'error': str(e)}}
    
    def _calculate_overall_status(self, health_data: Dict[str, Any]) -> str:
        """Вычислить общий статус системы"""
        status_priority = {
            'critical': 5,
            'unhealthy': 4,
            'degraded': 3,
            'warning': 2,
            'healthy': 1,
            'excellent': 0,
            'optimal': 0,
            'good': 1,
            'acceptable': 2,
            'poor': 4
        }
        
        max_priority = 0
        found_issues = []
        
        for check_type, check_data in health_data.items():
            if 'error' in check_data:
                max_priority = max(max_priority, 5)
                found_issues.append(f"{check_type}: error")
                continue
            
            # Получение статуса из различных полей
            status = None
            if 'status' in check_data:
                status = check_data['status']
            elif 'overall_status' in check_data:
                status = check_data['overall_status']
            elif 'checks' in check_data:
                # Для бизнес-метрик
                status = check_data.get('overall_status', 'healthy')
            
            if status and status in status_priority:
                priority = status_priority[status]
                max_priority = max(max_priority, priority)
                
                if priority >= 3:
                    found_issues.append(f"{check_type}: {status}")
        
        # Определение итогового статуса
        if max_priority >= 5:
            return 'critical'
        elif max_priority >= 4:
            return 'unhealthy'
        elif max_priority >= 3:
            return 'degraded'
        elif max_priority >= 2:
            return 'warning'
        else:
            return 'healthy'
    
    def _generate_summary(self, health_data: Dict[str, Any]) -> Dict[str, Any]:
        """Генерировать сводку состояния"""
        summary = {
            'total_checks': len(health_data),
            'healthy_components': 0,
            'degraded_components': 0,
            'unhealthy_components': 0,
            'critical_components': 0,
            'total_issues': 0,
            'top_issues': []
        }
        
        for check_type, check_data in health_data.items():
            if 'error' in check_data:
                summary['critical_components'] += 1
                summary['total_issues'] += 1
                summary['top_issues'].append(f"{check_type}: system error")
                continue
            
            # Определение статуса компонента
            status = None
            if 'status' in check_data:
                status = check_data['status']
            elif 'overall_status' in check_data:
                status = check_data['overall_status']
            
            if status:
                if status in ['healthy', 'excellent', 'optimal', 'good']:
                    summary['healthy_components'] += 1
                elif status in ['degraded', 'warning', 'acceptable']:
                    summary['degraded_components'] += 1
                    summary['total_issues'] += 1
                    summary['top_issues'].append(f"{check_type}: {status}")
                elif status in ['unhealthy', 'poor']:
                    summary['unhealthy_components'] += 1
                    summary['total_issues'] += 1
                    summary['top_issues'].append(f"{check_type}: {status}")
                elif status in ['critical']:
                    summary['critical_components'] += 1
                    summary['total_issues'] += 1
                    summary['top_issues'].append(f"{check_type}: {status}")
        
        # Ограничение списка проблем
        summary['top_issues'] = summary['top_issues'][:5]
        
        return summary

def create_fastapi_health_endpoints(app, config: Dict[str, Any] = None):
    """Создать все FastAPI endpoints для health checks"""
    
    @app.get("/health")
    async def health_root():
        """Корневой endpoint проверки здоровья"""
        checker = ComprehensiveHealthChecker(config)
        return await checker.comprehensive_check()
    
    @app.get("/health/basic")
    async def health_basic():
        """Базовая проверка здоровья"""
        from .basic_health import BasicHealthChecker
        checker = BasicHealthChecker(
            service_name=config.get('service_name', 'unknown-service') if config else 'unknown-service',
            version=config.get('version', '1.0.0') if config else '1.0.0'
        )
        return checker.to_dict()
    
    @app.get("/health/dependencies")
    async def health_dependencies():
        """Проверка зависимостей"""
        from .dependencies_health import DependenciesHealthChecker, DEFAULT_DEPENDENCIES_CONFIG
        checker = DependenciesHealthChecker(
            config.get('dependencies', DEFAULT_DEPENDENCIES_CONFIG) if config else DEFAULT_DEPENDENCIES_CONFIG
        )
        return await checker.async_check()
    
    @app.get("/health/business")
    async def health_business():
        """Проверка бизнес-логики"""
        from .business_health import BusinessHealthChecker, DEFAULT_BUSINESS_CONFIG
        checker = BusinessHealthChecker(
            config.get('business', DEFAULT_BUSINESS_CONFIG) if config else DEFAULT_BUSINESS_CONFIG
        )
        return await checker.async_check()
    
    @app.get("/health/performance")
    async def health_performance():
        """Проверка производительности"""
        from .performance_health import PerformanceHealthChecker, DEFAULT_PERFORMANCE_CONFIG
        checker = PerformanceHealthChecker(
            config.get('performance', DEFAULT_PERFORMANCE_CONFIG) if config else DEFAULT_PERFORMANCE_CONFIG
        )
        return await checker.async_check()
    
    @app.get("/health/custom-metrics")
    async def health_custom_metrics():
        """Проверка кастомных метрик"""
        from .custom_metrics_health import CustomMetricsHealthChecker, DEFAULT_CUSTOM_METRICS_CONFIG
        checker = CustomMetricsHealthChecker(
            config.get('custom_metrics', DEFAULT_CUSTOM_METRICS_CONFIG) if config else DEFAULT_CUSTOM_METRICS_CONFIG
        )
        return await checker.async_check()

def create_flask_health_blueprints(config: Dict[str, Any] = None):
    """Создать все Flask blueprints для health checks"""
    from flask import Blueprint, jsonify
    
    # Комплексный health check
    @Blueprint('health', __name__)
    class HealthBlueprint:
        
        @staticmethod
        @Blueprint.route('/health')
        def health_root():
            """Корневой endpoint проверки здоровья"""
            checker = ComprehensiveHealthChecker(config)
            # В Flask нужно запустить асинхронную функцию
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(checker.comprehensive_check())
            loop.close()
            return jsonify(result)
        
        @staticmethod
        @Blueprint.route('/health/basic')
        def health_basic():
            """Базовая проверка здоровья"""
            from .basic_health import BasicHealthChecker
            checker = BasicHealthChecker(
                service_name=config.get('service_name', 'unknown-service') if config else 'unknown-service',
                version=config.get('version', '1.0.0') if config else '1.0.0'
            )
            return jsonify(checker.to_dict())
        
        @staticmethod
        @Blueprint.route('/health/dependencies')
        def health_dependencies():
            """Проверка зависимостей"""
            from .dependencies_health import DependenciesHealthChecker, DEFAULT_DEPENDENCIES_CONFIG
            checker = DependenciesHealthChecker(
                config.get('dependencies', DEFAULT_DEPENDENCIES_CONFIG) if config else DEFAULT_DEPENDENCIES_CONFIG
            )
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(checker.async_check())
            loop.close()
            return jsonify(result)
        
        @staticmethod
        @Blueprint.route('/health/business')
        def health_business():
            """Проверка бизнес-логики"""
            from .business_health import BusinessHealthChecker, DEFAULT_BUSINESS_CONFIG
            checker = BusinessHealthChecker(
                config.get('business', DEFAULT_BUSINESS_CONFIG) if config else DEFAULT_BUSINESS_CONFIG
            )
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(checker.async_check())
            loop.close()
            return jsonify(result)
        
        @staticmethod
        @Blueprint.route('/health/performance')
        def health_performance():
            """Проверка производительности"""
            from .performance_health import PerformanceHealthChecker, DEFAULT_PERFORMANCE_CONFIG
            checker = PerformanceHealthChecker(
                config.get('performance', DEFAULT_PERFORMANCE_CONFIG) if config else DEFAULT_PERFORMANCE_CONFIG
            )
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(checker.async_check())
            loop.close()
            return jsonify(result)
        
        @staticmethod
        @Blueprint.route('/health/custom-metrics')
        def health_custom_metrics():
            """Проверка кастомных метрик"""
            from .custom_metrics_health import CustomMetricsHealthChecker, DEFAULT_CUSTOM_METRICS_CONFIG
            checker = CustomMetricsHealthChecker(
                config.get('custom_metrics', DEFAULT_CUSTOM_METRICS_CONFIG) if config else DEFAULT_CUSTOM_METRICS_CONFIG
            )
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(checker.async_check())
            loop.close()
            return jsonify(result)

# Экспорт основных классов
__all__ = [
    'BasicHealthChecker',
    'DependenciesHealthChecker', 
    'BusinessHealthChecker',
    'PerformanceHealthChecker',
    'CustomMetricsHealthChecker',
    'ComprehensiveHealthChecker',
    'create_fastapi_health_endpoints',
    'create_flask_health_blueprints',
    'DEFAULT_DEPENDENCIES_CONFIG',
    'DEFAULT_BUSINESS_CONFIG',
    'DEFAULT_PERFORMANCE_CONFIG',
    'DEFAULT_CUSTOM_METRICS_CONFIG'
]