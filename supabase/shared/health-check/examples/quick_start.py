# [NEXUS IDENTITY] ID: 5861981844084990866 | DATE: 2025-11-19

"""
Health Check System - Quick Start Example
Быстрый старт для интеграции health checks в приложение
"""

import asyncio
import time


# Вариант 1: FastAPI интеграция
def create_fastapi_example():
    """Создание FastAPI приложения с health checks"""
    
    from health_check import setup_health_checks_for_service

    # Создание FastAPI приложения
    app = setup_health_checks_for_service(
        service_name="my-fastapi-service",
        framework="fastapi",
        version="1.0.0"
    )
    
    # Ваши существующие endpoints
    @app.get("/")
    async def root():
        return {"message": "Hello from FastAPI with Health Checks!"}
    
    @app.get("/api/users")
    async def get_users():
        # Симуляция получения пользователей
        await asyncio.sleep(0.1)  # Имитация задержки БД
        return {"users": [{"id": 1, "name": "John"}]}
    
    @app.post("/api/data")
    async def create_data(data: dict):
        # Симуляция создания данных
        await asyncio.sleep(0.2)  # Имитация обработки
        return {"id": 123, "created": True}
    
    return app

# Вариант 2: Flask интеграция  
def create_flask_example():
    """Создание Flask приложения с health checks"""
    
    from flask import jsonify
    from health_check import setup_health_checks_for_service

    # Создание Flask приложения
    app = setup_health_checks_for_service(
        service_name="my-flask-service",
        framework="flask",
        version="1.0.0"
    )
    
    # Ваши существующие endpoints
    @app.route("/")
    def root():
        return jsonify({"message": "Hello from Flask with Health Checks!"})
    
    @app.route("/api/users")
    def get_users():
        # Симуляция получения пользователей
        time.sleep(0.1)  # Имитация задержки БД
        return jsonify({"users": [{"id": 1, "name": "John"}]})
    
    @app.route("/api/data", methods=["POST"])
    def create_data():
        # Симуляция создания данных
        time.sleep(0.2)  # Имитация обработки
        return jsonify({"id": 123, "created": True})
    
    return app

# Вариант 3: Standalone система мониторинга
async def create_standalone_monitoring():
    """Создание standalone системы мониторинга"""
    
    from health_check import HealthCheckSystem

    # Создание системы health checks
    health_system = HealthCheckSystem()
    
    # Регистрация ваших сервисов
    async def my_api_health():
        """Health check для вашего API сервиса"""
        return {
            'service_name': 'my-api',
            'status': 'healthy',
            'cpu_percent': 45.2,
            'memory_percent': 67.8,
            'response_time_ms': 250,
            'error_rate': 1.2,
            'active_connections': 42,
            'database_connected': True,
            'cache_hit_rate': 0.85
        }
    
    async def my_ml_service_health():
        """Health check для ML сервиса"""
        return {
            'service_name': 'my-ml-service',
            'status': 'degraded',
            'cpu_percent': 89.5,
            'memory_percent': 78.3,
            'response_time_ms': 1200,
            'error_rate': 3.1,
            'model_load_time': 2.5,
            'inference_queue_size': 15
        }
    
    # Регистрация сервисов
    health_system.register_service('my-api', my_api_health)
    health_system.register_service('my-ml-service', my_ml_service_health)
    
    # Запуск системы мониторинга
    print("Starting health monitoring...")
    await health_system.start_monitoring()
    
    # Получение обзора системы
    overview = await health_system.get_system_overview()
    print(f"System Overview: {overview}")
    
    # Генерация Kubernetes конфигураций
    k8s_configs = health_system.generate_kubernetes_configs(
        service_type='api_gateway',
        service_name='my-api'
    )
    
    # Сохранение конфигураций
    for config_name, config_content in k8s_configs.items():
        with open(f'{config_name}.yaml', 'w') as f:
            f.write(config_content)
    
    print("Generated Kubernetes configurations:")
    for config_name in k8s_configs.keys():
        print(f"  - {config_name}.yaml")
    
    # Экспорт отчета
    report_file = health_system.export_system_report()
    print(f"Health report exported to: {report_file}")
    
    return health_system

# Вариант 4: Минимальная интеграция
def create_minimal_integration():
    """Минимальная интеграция health checks"""
    
    import asyncio
    from datetime import datetime

    from health_check.endpoints import BasicHealthChecker

    # Создание простого health check
    checker = BasicHealthChecker("my-service", "1.0.0")
    
    # Регулярная проверка здоровья
    async def health_monitor():
        while True:
            try:
                health_info = checker.check()
                
                print(f"[{datetime.now()}] Health Status: {health_info.status}")
                print(f"  CPU: {health_info.cpu_percent}%")
                print(f"  Memory: {health_info.memory_usage_mb:.2f}MB")
                print(f"  Uptime: {health_info.uptime_seconds}s")
                
                if health_info.status.value in ['critical', 'unhealthy']:
                    print(f"⚠️ ALERT: Service health is {health_info.status.value}")
                
                # Проверка каждые 30 секунд
                await asyncio.sleep(30)
                
            except Exception as e:
                print(f"Health check error: {e}")
                await asyncio.sleep(60)  # При ошибке ждать дольше
    
    # Запуск мониторинга
    asyncio.create_task(health_monitor())
    
    return checker

# Демонстрация всех вариантов
async def demo_all_examples():
    """Демонстрация всех примеров интеграции"""
    
    print("🚀 Health Check System - Quick Start Examples")
    print("=" * 60)
    
    # Пример 1: FastAPI
    print("\n1. FASTAPI INTEGRATION")
    print("-" * 30)
    fastapi_app = create_fastapi_example()
    print("✅ FastAPI app created with health checks")
    print("Available endpoints:")
    print("  - GET /health (basic health)")
    print("  - GET /health/dependencies")
    print("  - GET /health/business")
    print("  - GET /health/performance")
    print("  - GET /health/custom-metrics")
    
    # Пример 2: Flask
    print("\n2. FLASK INTEGRATION")
    print("-" * 30)
    flask_app = create_flask_example()
    print("✅ Flask app created with health checks")
    print("Available endpoints:")
    print("  - GET /health (basic health)")
    print("  - GET /health/dependencies")
    print("  - GET /health/business")
    print("  - GET /health/performance")
    print("  - GET /health/custom-metrics")
    
    # Пример 3: Standalone мониторинг
    print("\n3. STANDALONE MONITORING")
    print("-" * 30)
    health_system = await create_standalone_monitoring()
    print("✅ Standalone monitoring system started")
    
    # Пример 4: Минимальная интеграция
    print("\n4. MINIMAL INTEGRATION")
    print("-" * 30)
    minimal_checker = create_minimal_integration()
    print("✅ Minimal health monitoring started")
    
    print("\n" + "=" * 60)
    print("📋 TO START THE APPLICATIONS:")
    print("=" * 60)
    print()
    print("FastAPI App:")
    print("  from examples.quick_start import create_fastapi_example")
    print("  app = create_fastapi_example()")
    print("  import uvicorn")
    print("  uvicorn.run(app, host='0.0.0.0', port=8000)")
    print()
    print("Flask App:")
    print("  from examples.quick_start import create_flask_example")
    print("  app = create_flask_example()")
    print("  app.run(host='0.0.0.0', port=8000)")
    print()
    print("Dashboard:")
    print("  health_system.start_dashboard(host='0.0.0.0', port=5000)")
    print()
    print("🔗 Available URLs:")
    print("  - Health Dashboard: http://localhost:5000")
    print("  - FastAPI Docs: http://localhost:8000/docs")
    print("  - Health Endpoint: http://localhost:8000/health")
    print()

# Функция для тестирования health checks
async def test_health_checks():
    """Функция для тестирования health checks"""
    
    print("🧪 Testing Health Check System")
    print("=" * 40)
    
    # Тест Basic Health Checker
    from health_check.endpoints import BasicHealthChecker
    
    print("\n1. Testing Basic Health Checker...")
    basic_checker = BasicHealthChecker("test-service", "1.0.0")
    basic_result = basic_checker.check()
    print(f"✅ Status: {basic_result.status.value}")
    print(f"   CPU: {basic_result.cpu_percent}%")
    print(f"   Memory: {basic_result.memory_usage_mb:.2f}MB")
    
    # Тест Dependencies Checker (без реальных зависимостей)
    from health_check.endpoints import DependenciesHealthChecker
    
    print("\n2. Testing Dependencies Checker...")
    deps_config = {
        'databases': [],
        'redis': [],
        'apis': [
            {
                'name': 'test_api',
                'url': 'https://httpbin.org/status/200',
                'expected_status': 200
            }
        ],
        'services': []
    }
    
    deps_checker = DependenciesHealthChecker(deps_config)
    try:
        deps_result = await deps_checker.async_check()
        print(f"✅ Status: {deps_result['overall_status']}")
        print(f"   Total dependencies: {deps_result['total_dependencies']}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Тест Performance Checker
    from health_check.endpoints import PerformanceHealthChecker
    
    print("\n3. Testing Performance Checker...")
    perf_config = {
        'endpoints': [
            {'url': '/health', 'method': 'GET'}
        ]
    }
    
    perf_checker = PerformanceHealthChecker(perf_config)
    try:
        perf_result = await perf_checker.async_check()
        print(f"✅ Status: {perf_result['overall_status']}")
        print(f"   Performance Score: {perf_result['performance_score']:.2f}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n✅ Health check system tests completed!")
    print("\n🎯 Next Steps:")
    print("1. Integrate with your existing application")
    print("2. Configure dependencies in health checks")
    print("3. Set up monitoring dashboard")
    print("4. Configure Kubernetes probes")
    print("5. Set up automated recovery")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Запуск тестов
        asyncio.run(test_health_checks())
    else:
        # Запуск демонстрации
        asyncio.run(demo_all_examples())