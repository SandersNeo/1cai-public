# [NEXUS IDENTITY] ID: 2006973352682360693 | DATE: 2025-11-19

"""
Health Check System Demo
Демонстрация всех возможностей системы health checks
"""

import asyncio
from typing import Any, Dict

# Импорт всех компонентов системы health checks
from supabase.shared.health_check import HealthCheckSystem
from supabase.shared.health_check.endpoints import (BasicHealthChecker,
                                                    BusinessHealthChecker,
                                                    CustomMetricsHealthChecker,
                                                    DependenciesHealthChecker,
                                                    PerformanceHealthChecker)
from supabase.shared.health_check.manager import HealthCheckManager


class HealthCheckDemo:
    """Демонстрация системы health checks"""
    
    def __init__(self):
        self.config = self.create_demo_config()
        self.health_system = HealthCheckSystem(self.config)
    
    def create_demo_config(self) -> Dict[str, Any]:
        """Создание конфигурации для демо"""
        return {
            'services': [
                {
                    'name': 'api-gateway',
                    'type': 'api_gateway',
                    'port': 8080
                },
                {
                    'name': 'auth-service',
                    'type': 'api_gateway',
                    'port': 8081
                },
                {
                    'name': 'user-service',
                    'type': 'api_gateway',
                    'port': 8082
                },
                {
                    'name': 'ml-service',
                    'type': 'ml_service',
                    'port': 8083
                },
                {
                    'name': 'notification-service',
                    'type': 'api_gateway',
                    'port': 8084
                }
            ],
            'dashboard': {
                'enabled': True,
                'host': '0.0.0.0',
                'port': 5000
            },
            'recovery': {
                'enabled': True,
                'auto_recovery': True
            },
            'manager': {
                'check_intervals': {
                    'basic': 30,
                    'dependencies': 60,
                    'business': 300,
                    'performance': 60,
                    'custom_metrics': 600
                }
            }
        }
    
    async def demo_basic_health_checks(self):
        """Демонстрация базовых health checks"""
        print("=" * 60)
        print("1. BASIC HEALTH CHECKS DEMO")
        print("=" * 60)
        
        # Создание Basic Health Checker
        checker = BasicHealthChecker("demo-service", "1.0.0")
        
        # Выполнение проверки
        health_info = checker.check()
        
        print(f"Service Name: {health_info.service_name}")
        print(f"Version: {health_info.version}")
        print(f"Status: {health_info.status}")
        print(f"Uptime: {health_info.uptime_seconds} seconds")
        print(f"CPU Usage: {health_info.cpu_percent}%")
        print(f"Memory Usage: {health_info.memory_usage_mb:.2f} MB")
        print(f"Disk Usage: {health_info.disk_usage_percent}%")
        print(f"Response Time: {health_info.response_time_ms:.2f} ms")
        print(f"Hostname: {health_info.hostname}")
        print(f"PID: {health_info.pid}")
        print()
        
        return health_info
    
    async def demo_dependencies_health_checks(self):
        """Демонстрация проверки зависимостей"""
        print("=" * 60)
        print("2. DEPENDENCIES HEALTH CHECKS DEMO")
        print("=" * 60)
        
        # Конфигурация зависимостей для демо
        demo_dependencies_config = {
            'timeout_seconds': 5,
            'max_retries': 3,
            'databases': [
                {
                    'name': 'demo_postgres',
                    'host': 'demo-postgres',
                    'port': 5432,
                    'user': 'demo_user',
                    'password': 'demo_password',
                    'database': 'demo_db'
                }
            ],
            'redis': [
                {
                    'name': 'demo_redis',
                    'host': 'demo-redis',
                    'port': 6379,
                    'password': 'demo_redis_password'
                }
            ],
            'apis': [
                {
                    'name': 'demo_external_api',
                    'url': 'https://httpbin.org/status/200',
                    'headers': {
                        'User-Agent': 'HealthCheckDemo/1.0'
                    },
                    'expected_status': 200
                }
            ],
            'services': [
                {
                    'name': 'demo_auth_service',
                    'url': 'http://demo-auth-service:8000'
                },
                {
                    'name': 'demo_ml_service',
                    'url': 'http://demo-ml-service:8001'
                }
            ]
        }
        
        checker = DependenciesHealthChecker(demo_dependencies_config)
        
        try:
            health_info = await checker.async_check()
            
            print(f"Overall Status: {health_info['overall_status']}")
            print(f"Total Dependencies: {health_info['total_dependencies']}")
            print(f"Healthy: {health_info['healthy_count']}")
            print(f"Degraded: {health_info['degraded_count']}")
            print(f"Unhealthy: {health_info['unhealthy_count']}")
            print()
            
            print("Dependencies Details:")
            for dep in health_info['dependencies']:
                print(f"  - {dep['name']} ({dep['type']}): {dep['status']}")
                print(f"    Response Time: {dep['response_time_ms']:.2f}ms")
                if dep.get('error_message'):
                    print(f"    Error: {dep['error_message']}")
            print()
            
            return health_info
            
        except Exception as e:
            print(f"Error in dependencies check: {e}")
            return {}
    
    async def demo_business_health_checks(self):
        """Демонстрация проверки бизнес-логики"""
        print("=" * 60)
        print("3. BUSINESS LOGIC HEALTH CHECKS DEMO")
        print("=" * 60)
        
        # Конфигурация для демо
        demo_business_config = {
            'auth_service_url': 'http://demo-auth-service:8000',
            'ml_service_url': 'http://demo-ml-service:8001',
            'db_service_url': 'http://demo-db-service:8002',
            'storage_service_url': 'http://demo-storage-service:8003'
        }
        
        checker = BusinessHealthChecker(demo_business_config)
        
        try:
            health_info = await checker.async_check()
            
            print(f"Overall Status: {health_info['overall_status']}")
            print(f"Total Checks: {health_info['total_checks']}")
            print(f"Healthy: {health_info['healthy_count']}")
            print(f"Degraded: {health_info['degraded_count']}")
            print(f"Critical: {health_info['critical_count']}")
            print()
            
            print("Business Functions:")
            for check in health_info['checks']:
                print(f"  - {check['name']} ({check['category']}): {check['status']}")
                print(f"    Response Time: {check['response_time_ms']:.2f}ms")
                if check.get('recommendations'):
                    print(f"    Recommendations: {', '.join(check['recommendations'])}")
            print()
            
            if health_info.get('critical_functions'):
                print("Critical Functions:")
                for func in health_info['critical_functions']:
                    print(f"  - {func}")
                print()
            
            return health_info
            
        except Exception as e:
            print(f"Error in business checks: {e}")
            return {}
    
    async def demo_performance_health_checks(self):
        """Демонстрация проверки производительности"""
        print("=" * 60)
        print("4. PERFORMANCE HEALTH CHECKS DEMO")
        print("=" * 60)
        
        demo_performance_config = {
            'base_url': 'http://demo-service:8000',
            'endpoints': [
                {'url': '/health', 'method': 'GET', 'timeout': 5},
                {'url': '/api/users', 'method': 'GET', 'timeout': 10},
                {'url': '/api/data', 'method': 'POST', 'timeout': 15}
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
        
        checker = PerformanceHealthChecker(demo_performance_config)
        
        try:
            health_info = await checker.async_check()
            
            print(f"Overall Status: {health_info['overall_status']}")
            print(f"Performance Score: {health_info['performance_score']:.2f}")
            print(f"CPU Usage: {health_info['current_metrics']['cpu_percent']:.2f}%")
            print(f"Memory Usage: {health_info['current_metrics']['memory_percent']:.2f}%")
            print(f"Load Average: {health_info['current_metrics']['load_average']}")
            print()
            
            if health_info.get('bottlenecks'):
                print("Identified Bottlenecks:")
                for bottleneck in health_info['bottlenecks']:
                    print(f"  - {bottleneck}")
                print()
            
            if health_info.get('recommendations'):
                print("Performance Recommendations:")
                for recommendation in health_info['recommendations']:
                    print(f"  - {recommendation}")
                print()
            
            if health_info.get('trends'):
                print("Performance Trends:")
                for trend_type, trend_value in health_info['trends'].items():
                    print(f"  - {trend_type}: {trend_value}")
                print()
            
            return health_info
            
        except Exception as e:
            print(f"Error in performance checks: {e}")
            return {}
    
    async def demo_custom_metrics_health_checks(self):
        """Демонстрация кастомных бизнес-метрик"""
        print("=" * 60)
        print("5. CUSTOM BUSINESS METRICS DEMO")
        print("=" * 60)
        
        demo_custom_metrics_config = {
            'analytics_service_url': 'http://demo-analytics:8005',
            'api_gateway_url': 'http://demo-gateway:8000',
            'billing_service_url': 'http://demo-billing:8006'
        }
        
        checker = CustomMetricsHealthChecker(demo_custom_metrics_config)
        
        try:
            health_info = await checker.async_check()
            
            print(f"Overall Status: {health_info['overall_status']}")
            print(f"Total Metrics: {health_info['total_metrics']}")
            print(f"Business Health Score: {health_info['business_health_score']:.2f}")
            print()
            
            print("Business Metrics:")
            for metric_check in health_info['metrics']:
                metric = metric_check['metric']
                print(f"  - {metric['name']}: {metric['value']} {metric.get('unit', '')}")
                print(f"    Status: {metric['status']}")
                if metric.get('description'):
                    print(f"    Description: {metric['description']}")
                print(f"    Trend: {metric_check['trend']}")
                if metric_check.get('recommendations'):
                    print(f"    Recommendations: {', '.join(metric_check['recommendations'])}")
                print()
            
            if health_info.get('key_insights'):
                print("Key Business Insights:")
                for insight in health_info['key_insights']:
                    print(f"  - {insight}")
                print()
            
            return health_info
            
        except Exception as e:
            print(f"Error in custom metrics checks: {e}")
            return {}
    
    async def demo_health_check_manager(self):
        """Демонстрация Health Check Manager"""
        print("=" * 60)
        print("6. HEALTH CHECK MANAGER DEMO")
        print("=" * 60)
        
        manager = HealthCheckManager()
        
        # Регистрация демо сервисов
        async def demo_api_health():
            return {
                'service_name': 'demo-api',
                'status': 'healthy',
                'cpu_percent': 45.2,
                'memory_percent': 67.8,
                'response_time_ms': 250,
                'error_rate': 1.2,
                'business_health_score': 85.5
            }
        
        async def demo_ml_health():
            return {
                'service_name': 'demo-ml',
                'status': 'degraded',
                'cpu_percent': 89.5,
                'memory_percent': 78.3,
                'response_time_ms': 1200,
                'error_rate': 3.1,
                'business_health_score': 72.1
            }
        
        async def demo_db_health():
            return {
                'service_name': 'demo-db',
                'status': 'healthy',
                'cpu_percent': 23.1,
                'memory_percent': 45.7,
                'response_time_ms': 85,
                'error_rate': 0.3,
                'business_health_score': 95.2
            }
        
        # Регистрация сервисов
        manager.register_service('demo-api', demo_api_health)
        manager.register_service('demo-ml', demo_ml_health)
        manager.register_service('demo-db', demo_db_health)
        
        print("Registered Services:")
        for service_name in manager.services.keys():
            print(f"  - {service_name}")
        print()
        
        # Получение общего состояния здоровья
        overall_health = await manager.get_overall_health()
        
        print(f"Overall Status: {overall_health['overall_status']}")
        print(f"Timestamp: {overall_health['timestamp']}")
        print()
        
        print("Summary:")
        summary = overall_health['summary']
        print(f"  Total Services: {summary['total_services']}")
        print(f"  Healthy Services: {summary['healthy_services']}")
        print(f"  Degraded Services: {summary['degraded_services']}")
        print(f"  Unhealthy Services: {summary['unhealthy_services']}")
        print(f"  Critical Services: {summary['critical_services']}")
        print(f"  Total Issues: {summary['total_issues']}")
        print()
        
        print("Individual Service Status:")
        for service_name, service_health in overall_health['services'].items():
            print(f"  - {service_name}: {service_health['status']}")
            print(f"    Health Score: {service_health['health_score']:.2f}")
            print(f"    Response Time: {service_health['response_time_ms']:.2f}ms")
            print(f"    Issues Count: {len(service_health['issues'])}")
        print()
        
        if overall_health.get('issues'):
            print("Detected Issues:")
            for issue in overall_health['issues']:
                print(f"  - {issue['title']} ({issue['severity']})")
                print(f"    Category: {issue['category']}")
                print(f"    Affected Services: {', '.join(issue['affected_services'])}")
                if issue.get('recommendations'):
                    print(f"    Recommendations: {', '.join(issue['recommendations'])}")
            print()
        
        if overall_health.get('recommendations'):
            print("System Recommendations:")
            recommendations = overall_health['recommendations']
            
            if recommendations.get('immediate_actions'):
                print("  Immediate Actions:")
                for action in recommendations['immediate_actions']:
                    print(f"    - {action}")
            
            if recommendations.get('short_term_actions'):
                print("  Short-term Actions:")
                for action in recommendations['short_term_actions']:
                    print(f"    - {action}")
            
            if recommendations.get('long_term_actions'):
                print("  Long-term Actions:")
                for action in recommendations['long_term_actions']:
                    print(f"    - {action}")
            print()
        
        if overall_health.get('trends'):
            print("Health Trends:")
            for trend_type, trend_value in overall_health['trends'].items():
                print(f"  - {trend_type}: {trend_value}")
            print()
        
        return overall_health
    
    async def demo_comprehensive_system(self):
        """Демонстрация комплексной системы"""
        print("=" * 60)
        print("7. COMPREHENSIVE HEALTH CHECK SYSTEM DEMO")
        print("=" * 60)
        
        # Регистрация всех демо сервисов
        services = [
            'api-gateway', 'auth-service', 'user-service', 
            'ml-service', 'notification-service', 'analytics-service'
        ]
        
        for service_name in services:
            if service_name.startswith('api') or service_name.endswith('service'):
                async def create_service_health(name: str):
                    return {
                        'service_name': name,
                        'status': 'healthy',
                        'cpu_percent': 40 + (hash(name) % 30),
                        'memory_percent': 50 + (hash(name) % 25),
                        'response_time_ms': 100 + (hash(name) % 200),
                        'error_rate': (hash(name) % 10) / 10,
                        'business_health_score': 80 + (hash(name) % 15),
                        'dependencies_status': {
                            'database': 'healthy',
                            'redis': 'healthy' if hash(name) % 3 != 0 else 'degraded'
                        }
                    }
                
                self.health_system.register_service(
                    service_name, 
                    create_service_health(service_name)
                )
        
        print("Registered Services:")
        for service_name in self.health_system.registered_services.keys():
            print(f"  - {service_name}")
        print()
        
        # Получение общего обзора системы
        system_overview = await self.health_system.get_system_overview()
        
        print("System Overview:")
        print(f"  Registered Services: {system_overview['registered_services']}")
        print(f"  Overall Status: {system_overview.get('overall_status', 'N/A')}")
        print(f"  Issues Count: {system_overview.get('issues_count', 0)}")
        print()
        
        if system_overview.get('health_metrics'):
            metrics = system_overview['health_metrics']
            print("Health Metrics:")
            print(f"  Overall Health Score: {metrics.get('overall_health_score', 0):.2f}")
            print(f"  Average Response Time: {metrics.get('average_response_time', 0):.2f}ms")
            print(f"  System Uptime: {metrics.get('system_uptime_percentage', 0):.2f}%")
            print(f"  Active Incidents: {metrics.get('active_incidents', 0)}")
            print()
        
        if system_overview.get('recovery_statistics'):
            recovery_stats = system_overview['recovery_statistics']
            print("Recovery Statistics:")
            print(f"  Total Executions: {recovery_stats.get('total_executions', 0)}")
            print(f"  Success Rate: {recovery_stats.get('success_rate', 0):.2%}")
            print()
        
        return system_overview
    
    async def demo_kubernetes_configs(self):
        """Демонстрация генерации Kubernetes конфигураций"""
        print("=" * 60)
        print("8. KUBERNETES CONFIGS GENERATION DEMO")
        print("=" * 60)
        
        # Генерация конфигураций для разных типов сервисов
        service_configs = [
            ('api_gateway', 'api-gateway'),
            ('ml_service', 'ml-service'),
            ('database_service', 'postgres-service'),
            ('cache_service', 'redis-service'),
            ('frontend_app', 'web-frontend')
        ]
        
        for service_type, service_name in service_configs:
            print(f"Generating configs for {service_type}: {service_name}")
            
            custom_config = {
                'image': f'myregistry.com/{service_name}:v1.0.0',
                'version': '1.0.0',
                'replicas': 3,
                'env': [
                    {'name': 'LOG_LEVEL', 'value': 'INFO'},
                    {'name': 'HEALTH_CHECK_INTERVAL', 'value': '30'},
                    {'name': 'SERVICE_NAME', 'value': service_name}
                ],
                'ingress': {
                    'host': f'{service_name}.example.com',
                    'ingress_class': 'nginx'
                },
                'hpa': {
                    'min_replicas': 2,
                    'max_replicas': 10,
                    'cpu_target': 70,
                    'memory_target': 80
                }
            }
            
            configs = self.health_system.generate_kubernetes_configs(
                service_type, service_name, custom_config
            )
            
            print(f"  Generated {len(configs)} configuration files:")
            for config_name in configs.keys():
                print(f"    - {config_name}.yaml")
            print()
    
    async def run_full_demo(self):
        """Запуск полной демонстрации"""
        print("🚀 HEALTH CHECK SYSTEM - COMPLETE DEMO")
        print("=" * 80)
        print()
        
        # Последовательное выполнение всех демо
        await self.demo_basic_health_checks()
        await asyncio.sleep(1)
        
        await self.demo_dependencies_health_checks()
        await asyncio.sleep(1)
        
        await self.demo_business_health_checks()
        await asyncio.sleep(1)
        
        await self.demo_performance_health_checks()
        await asyncio.sleep(1)
        
        await self.demo_custom_metrics_health_checks()
        await asyncio.sleep(1)
        
        await self.demo_health_check_manager()
        await asyncio.sleep(1)
        
        await self.demo_comprehensive_system()
        await asyncio.sleep(1)
        
        await self.demo_kubernetes_configs()
        
        print("=" * 80)
        print("✅ DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print()
        print("📋 Next Steps:")
        print("1. Review generated health check configurations")
        print("2. Start the health monitoring dashboard")
        print("3. Configure alerts and notifications")
        print("4. Deploy to your Kubernetes cluster")
        print("5. Set up continuous monitoring")
        print()
        print("🔗 Useful Links:")
        print("- Dashboard: http://localhost:5000")
        print("- Health Endpoints: http://localhost:8000/health/*")
        print("- Documentation: docs/health-checks.md")
        print()

async def main():
    """Главная функция демо"""
    demo = HealthCheckDemo()
    
    print("Choose demo option:")
    print("1. Full Demo (All Components)")
    print("2. Basic Health Checks Only")
    print("3. Dependencies Health Checks Only")
    print("4. Business Logic Health Checks Only")
    print("5. Performance Health Checks Only")
    print("6. Custom Metrics Health Checks Only")
    print("7. Health Check Manager Only")
    print("8. Kubernetes Configs Only")
    print("9. Start Dashboard Server")
    print("0. Exit")
    print()
    
    try:
        choice = input("Enter your choice (0-9): ").strip()
        
        if choice == "1":
            await demo.run_full_demo()
        elif choice == "2":
            await demo.demo_basic_health_checks()
        elif choice == "3":
            await demo.demo_dependencies_health_checks()
        elif choice == "4":
            await demo.demo_business_health_checks()
        elif choice == "5":
            await demo.demo_performance_health_checks()
        elif choice == "6":
            await demo.demo_custom_metrics_health_checks()
        elif choice == "7":
            await demo.demo_health_check_manager()
        elif choice == "8":
            await demo.demo_kubernetes_configs()
        elif choice == "9":
            print("Starting Health Monitoring Dashboard...")
            print("Dashboard will be available at: http://localhost:5000")
            demo.health_system.start_dashboard(host='0.0.0.0', port=5000, debug=True)
        elif choice == "0":
            print("Goodbye!")
        else:
            print("Invalid choice. Please run again.")
    
    except KeyboardInterrupt:
        print("\nDemo interrupted by user.")
    except Exception as e:
        print(f"\nDemo error: {e}")

if __name__ == "__main__":
    print("🏥 Health Check System Demo")
    print("=" * 40)
    asyncio.run(main())