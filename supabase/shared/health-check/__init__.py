# [NEXUS IDENTITY] ID: 9174048270214367750 | DATE: 2025-11-19

"""
Health Check System - Main Index
Комплексная система health checks для всех сервисов
"""

from .endpoints import (
    BasicHealthChecker,
    DependenciesHealthChecker,
    BusinessHealthChecker,
    PerformanceHealthChecker,
    CustomMetricsHealthChecker,
    ComprehensiveHealthChecker,
    create_fastapi_health_endpoints,
    create_flask_health_blueprints,
    DEFAULT_DEPENDENCIES_CONFIG,
    DEFAULT_BUSINESS_CONFIG,
    DEFAULT_PERFORMANCE_CONFIG,
    DEFAULT_CUSTOM_METRICS_CONFIG
)

from .manager import (
    HealthCheckManager,
    OverallHealthStatus,
    IssueSeverity,
    IssueCategory,
    HealthIssue,
    ServiceHealth,
    HealthMetrics,
    HealthIssueDetector,
    RecommendationEngine
)

from .kubernetes.k8s_probes import (
    KubernetesProbesGenerator,
    ProbeType,
    ProbeProtocol,
    generate_all_k8s_configs,
    SERVICE_CONFIGS
)

from .dashboard.dashboard_server import (
    HealthDashboardServer,
    ServiceStatus,
    DashboardService,
    DashboardMetrics,
    Incident,
    create_dashboard_template
)

from .recovery.auto_recovery import (
    AutomatedRecoverySystem,
    RecoveryStatus,
    RecoveryType,
    RecoveryAction,
    RecoveryExecution,
    CircuitBreaker,
    ServiceRestartHandler,
    CacheClearer,
    TrafficSwitcher
)

import os
import asyncio
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class HealthCheckSystem:
    """Главный класс комплексной системы health checks"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Инициализация компонентов системы
        self.health_manager = HealthCheckManager(self.config.get('manager', {}))
        self.dashboard_server = None
        self.recovery_system = None
        
        # Зарегистрированные сервисы
        self.registered_services = {}
        
        self.setup_components()
    
    def setup_components(self):
        """Настройка компонентов системы"""
        
        # Настройка dashboard сервера
        dashboard_config = self.config.get('dashboard', {})
        if dashboard_config.get('enabled', True):
            self.dashboard_server = HealthDashboardServer(self.health_manager)
        
        # Настройка системы восстановления
        recovery_config = self.config.get('recovery', {})
        if recovery_config.get('enabled', True):
            self.recovery_system = AutomatedRecoverySystem(self.health_manager)
            
            # Добавление circuit breakers для всех сервисов
            for service_config in self.config.get('services', []):
                service_name = service_config.get('name')
                if service_name:
                    self.recovery_system.add_circuit_breaker(service_name)
    
    def register_service(self, service_name: str, health_check_func: Optional[callable] = None):
        """Ререгистрация сервиса для мониторинга"""
        
        if service_name in self.registered_services:
            logger.warning(f"Service {service_name} already registered")
            return
        
        # Создание default health check функции если не предоставлена
        if health_check_func is None:
            health_check_func = self._create_default_health_check(service_name)
        
        # Регистрация в health manager
        self.health_manager.register_service(service_name, health_check_func)
        
        self.registered_services[service_name] = {
            'name': service_name,
            'health_check': health_check_func,
            'registered_at': asyncio.get_event_loop().time()
        }
        
        logger.info(f"Registered service for health monitoring: {service_name}")
    
    def _create_default_health_check(self, service_name: str):
        """Создание default health check функции"""
        
        async def default_health_check():
            """Default health check для сервиса"""
            return {
                'service_name': service_name,
                'status': 'healthy',
                'cpu_percent': 45.2,
                'memory_percent': 67.8,
                'response_time_ms': 250,
                'error_rate': 1.2,
                'business_health_score': 85.5,
                'timestamp': asyncio.get_event_loop().time()
            }
        
        return default_health_check
    
    def setup_fastapi_app(self, app, service_name: str, version: str = "1.0.0"):
        """Настройка FastAPI приложения с health checks"""
        
        # Создание конфигурации для endpoints
        config = {
            'service_name': service_name,
            'version': version,
            'dependencies': DEFAULT_DEPENDENCIES_CONFIG,
            'business': DEFAULT_BUSINESS_CONFIG,
            'performance': DEFAULT_PERFORMANCE_CONFIG,
            'custom_metrics': DEFAULT_CUSTOM_METRICS_CONFIG
        }
        
        # Создание всех health check endpoints
        create_fastapi_health_endpoints(app, config)
        
        logger.info(f"FastAPI health endpoints created for {service_name}")
    
    def setup_flask_app(self, app, service_name: str, version: str = "1.0.0"):
        """Настройка Flask приложения с health checks"""
        
        # Создание конфигурации для endpoints
        config = {
            'service_name': service_name,
            'version': version,
            'dependencies': DEFAULT_DEPENDENCIES_CONFIG,
            'business': DEFAULT_BUSINESS_CONFIG,
            'performance': DEFAULT_PERFORMANCE_CONFIG,
            'custom_metrics': DEFAULT_CUSTOM_METRICS_CONFIG
        }
        
        # Создание всех health check blueprints
        blueprints = create_flask_health_blueprints(config)
        
        # Регистрация blueprints
        if hasattr(blueprints, 'register'):
            blueprints.register(app, url_prefix='/health')
        else:
            # Если blueprints является списком
            for bp in blueprints:
                app.register_blueprint(bp, url_prefix='/health')
        
        logger.info(f"Flask health endpoints created for {service_name}")
    
    def generate_kubernetes_configs(self, service_type: str, service_name: str,
                                  custom_config: Dict[str, Any] = None) -> Dict[str, str]:
        """Генерировать Kubernetes конфигурации для сервиса"""
        
        configs = generate_all_k8s_configs(service_type, service_name, custom_config)
        
        logger.info(f"Generated Kubernetes configs for {service_name}")
        return configs
    
    async def start_monitoring(self):
        """Запустить систему мониторинга"""
        
        # Запуск health manager
        await self.health_manager.start_monitoring()
        
        # Запуск системы восстановления
        if self.recovery_system:
            await self.recovery_system.start_auto_recovery()
        
        logger.info("Health check monitoring system started")
    
    async def stop_monitoring(self):
        """Остановить систему мониторинга"""
        
        # Остановка health manager
        await self.health_manager.stop_monitoring()
        
        # Остановка системы восстановления
        if self.recovery_system:
            self.recovery_system.stop_auto_recovery()
        
        logger.info("Health check monitoring system stopped")
    
    def start_dashboard(self, host: str = "0.0.0.0", port: int = 5000, debug: bool = False):
        """Запустить dashboard сервер"""
        
        if not self.dashboard_server:
            logger.warning("Dashboard server is not configured")
            return
        
        logger.info(f"Starting health monitoring dashboard at http://{host}:{port}")
        self.dashboard_server.run(host=host, port=port, debug=debug)
    
    async def get_system_overview(self) -> Dict[str, Any]:
        """Получить общий обзор системы здоровья"""
        
        overview = {
            'timestamp': asyncio.get_event_loop().time(),
            'registered_services': len(self.registered_services),
            'services': {}
        }
        
        # Получение данных от health manager
        if self.health_manager:
            overall_health = await self.health_manager.get_overall_health()
            overview.update({
                'overall_status': overall_health.get('overall_status', 'unknown'),
                'health_metrics': overall_health.get('summary', {}),
                'issues_count': len(overall_health.get('issues', [])),
                'recommendations': overall_health.get('recommendations', {})
            })
        
        # Добавление статистики восстановления
        if self.recovery_system:
            recovery_stats = self.recovery_system.get_recovery_statistics()
            overview['recovery_statistics'] = recovery_stats
        
        return overview
    
    def export_system_report(self, filename: str = None) -> str:
        """Экспортировать полный отчет о системе"""
        
        if not filename:
            filename = f"health_system_report_{int(asyncio.get_event_loop().time())}.json"
        
        # Создание отчета
        report = {
            'generated_at': asyncio.get_event_loop().time(),
            'system_overview': asyncio.run(self.get_system_overview()),
            'registered_services': list(self.registered_services.keys()),
            'health_history': self.health_manager.get_health_history(24),
            'recovery_report': self.recovery_system.export_recovery_report() if self.recovery_system else None
        }
        
        # Сохранение в файл
        with open(filename, 'w', encoding='utf-8') as f:
            import json
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        return filename
    
    def get_config_template(self) -> Dict[str, Any]:
        """Получить шаблон конфигурации системы"""
        
        return {
            'manager': {
                'check_intervals': {
                    'basic': 30,
                    'dependencies': 60,
                    'business': 300,
                    'performance': 60,
                    'custom_metrics': 600
                }
            },
            'dashboard': {
                'enabled': True,
                'host': '0.0.0.0',
                'port': 5000,
                'debug': False
            },
            'recovery': {
                'enabled': True,
                'auto_recovery': True,
                'circuit_breakers': {
                    'default_failure_threshold': 5,
                    'default_timeout': 60
                }
            },
            'services': [
                {
                    'name': 'api-gateway',
                    'type': 'api_gateway',
                    'port': 8080,
                    'health_check': {
                        'type': 'http',
                        'path': '/health'
                    }
                }
            ],
            'dependencies': DEFAULT_DEPENDENCIES_CONFIG,
            'business': DEFAULT_BUSINESS_CONFIG,
            'performance': DEFAULT_PERFORMANCE_CONFIG,
            'custom_metrics': DEFAULT_CUSTOM_METRICS_CONFIG
        }

# Функции-утилиты для быстрого старта
def create_health_check_system(config: Dict[str, Any] = None) -> HealthCheckSystem:
    """Создать экземпляр системы health checks"""
    return HealthCheckSystem(config)

def create_default_config() -> Dict[str, Any]:
    """Создать конфигурацию по умолчанию"""
    system = HealthCheckSystem()
    return system.get_config_template()

def setup_health_checks_for_service(service_name: str, framework: str = "fastapi",
                                  version: str = "1.0.0", config: Dict[str, Any] = None):
    """Быстрая настройка health checks для сервиса"""
    
    if framework.lower() == "fastapi":
        from fastapi import FastAPI
        app = FastAPI()
        
        system = HealthCheckSystem(config)
        system.setup_fastapi_app(app, service_name, version)
        
        return app
        
    elif framework.lower() == "flask":
        from flask import Flask
        app = Flask(__name__)
        
        system = HealthCheckSystem(config)
        system.setup_flask_app(app, service_name, version)
        
        return app
    
    else:
        raise ValueError(f"Unsupported framework: {framework}")

# Экспорт основных классов и функций
__all__ = [
    'HealthCheckSystem',
    'HealthCheckManager',
    'HealthDashboardServer',
    'AutomatedRecoverySystem',
    'KubernetesProbesGenerator',
    'ComprehensiveHealthChecker',
    'create_health_check_system',
    'create_default_config',
    'setup_health_checks_for_service',
    'DEFAULT_DEPENDENCIES_CONFIG',
    'DEFAULT_BUSINESS_CONFIG',
    'DEFAULT_PERFORMANCE_CONFIG',
    'DEFAULT_CUSTOM_METRICS_CONFIG',
    'SERVICE_CONFIGS'
]