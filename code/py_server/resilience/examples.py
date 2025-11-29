# [NEXUS IDENTITY] ID: -7973355668810514252 | DATE: 2025-11-19

"""
Примеры использования системы устойчивости

Демонстрирует различные способы применения circuit breaker, graceful degradation,
retry политик и fallback стратегий в реальных сценариях.
"""

import asyncio
import logging
import random
import time
from typing import Any, Dict

from . import (CircuitBreaker, CircuitBreakerConfig, GracefulDegradationConfig,
               GracefulDegradationManager, RetryPolicy,
               RetryPolicyConfig, ServiceContext, ServiceType,
               create_resilient_operation, get_fallback_strategy_manager, get_graceful_degradation_manager,
               with_exponential_backoff)

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("resilience_examples")


def example_1_basic_circuit_breaker():
    """Пример 1: Базовое использование circuit breaker"""
    print("\n=== Пример 1: Базовое использование Circuit Breaker ===")
    
    # Создаем circuit breaker
    config = CircuitBreakerConfig(
        failure_threshold=3,
        timeout=10.0,
        time_window=5.0
    )
    breaker = CircuitBreaker("api_service", config)
    
    # Симулируем API с случайными ошибками
    def unstable_api_call():
        if random.random() < 0.7:  # 70% вероятность ошибки
            raise ConnectionError("API недоступен")
        return {"status": "success", "data": "Test data"}
    
    # Выполняем несколько вызовов
    for i in range(10):
        try:
            result = breaker.call(unstable_api_call)
            print(f"Вызов {i+1}: Успех - {result}")
        except Exception as e:
            print(f"Вызов {i+1}: Ошибка - {e}")
        
        print(f"Состояние circuit breaker: {breaker.get_state()['state']}")
        time.sleep(1)


def example_2_retry_with_exponential_backoff():
    """Пример 2: Retry политика с экспоненциальной задержкой"""
    print("\n=== Пример 2: Retry с Exponential Backoff ===")
    
    # Создаем retry политику
    config = RetryPolicyConfig(
        max_attempts=4,
        base_delay=0.5,
        max_delay=8.0,
        exponential_base=2.0,
        jitter=True
    )
    retry_policy = RetryPolicy(config, "api_retry")
    
    # Функция, которая сначала часто ошибается, потом работает
    def flaky_function():
        if not hasattr(flaky_function, 'call_count'):
            flaky_function.call_count = 0
        
        flaky_function.call_count += 1
        
        if flaky_function.call_count <= 3:
            raise TimeoutError(f"Таймаут вызова {flaky_function.call_count}")
        return f"Успех на вызове {flaky_function.call_count}"
    
    try:
        start_time = time.time()
        result = retry_policy.execute(flaky_function)
        end_time = time.time()
        
        print(f"Результат: {result}")
        print(f"Время выполнения: {end_time - start_time:.2f}s")
        print(f"Статистика: {retry_policy.get_stats()}")
        
    except Exception as e:
        print(f"Все попытки исчерпаны: {e}")


def example_3_graceful_degradation_levels():
    """Пример 3: Управление уровнями graceful degradation"""
    print("\n=== Пример 3: Graceful Degradation Levels ===")
    
    # Создаем менеджер graceful degradation
    config = GracefulDegradationConfig(
        degradation_threshold=2,
        recovery_threshold=2
    )
    degradation_manager = GracefulDegradationManager(config)
    
    # Регистрируем сервис
    degradation_manager.register_service("user_service", "full_service")
    
    # Симулируем серию успехов и неудач
    operations = [
        ("login", False),   # Неудача
        ("get_profile", False),  # Неудача 
        ("get_data", False),     # Неудача (должна активировать деградацию)
        ("get_data", True),      # Успех
        ("get_data", True),      # Успех (должна откатить деградацию)
    ]
    
    for operation, success in operations:
        level = degradation_manager.evaluate_request("user_service", operation, success)
        metrics = degradation_manager.get_service_metrics("user_service")
        
        print(f"Операция '{operation}' - Успех: {success}")
        print(f"  Уровень деградации: {level.value}")
        print(f"  Последовательные неудачи: {metrics.consecutive_failures}")
        print(f"  Последовательные успехи: {metrics.consecutive_successes}")
        print()
    
    # Показать отчет
    report = degradation_manager.get_degradation_report()
    print(f"Отчет о деградации: {report}")


def example_4_fallback_strategies():
    """Пример 4: Fallback стратегии для различных сервисов"""
    print("\n=== Пример 4: Fallback стратегии ===")
    
    degradation_manager = get_graceful_degradation_manager()
    fallback_manager = get_fallback_strategy_manager()
    
    # Пример 1: MCP Tools Fallback
    print("1. MCP Tools Fallback:")
    
    def mock_mcp_tools_list():
        # Симулируем ошибку получения списка инструментов
        raise ConnectionError("MCP сервис недоступен")
    
    context = ServiceContext(
        service_name="mcp_client",
        service_type=ServiceType.MCP_TOOL,
        operation="tools/list"
    )
    
    fallback_result = fallback_manager.handle_service_fallback(
        ServiceType.MCP_TOOL,
        context,
        mock_mcp_tools_list
    )
    
    print(f"  Результат: {fallback_result.data}")
    print(f"  Источник: {fallback_result.source}")
    
    # Пример 2: OAuth2 Fallback
    print("\n2. OAuth2 Fallback:")
    
    def mock_oauth_authenticate(user_id: str):
        raise TimeoutError("OAuth сервис недоступен")
    
    context = ServiceContext(
        service_name="oauth_service",
        service_type=ServiceType.OAUTH2,
        operation="authenticate"
    )
    
    fallback_result = fallback_manager.handle_service_fallback(
        ServiceType.OAUTH2,
        context,
        mock_oauth_authenticate,
        user_id="test_user"
    )
    
    print(f"  Результат: {fallback_result.data}")
    print(f"  Источник: {fallback_result.source}")


def example_5_decorator_pattern():
    """Пример 5: Использование декораторов для устойчивости"""
    print("\n=== Пример 5: Декораторы устойчивости ===")
    
    # Использование декоратора с retry
    @with_exponential_backoff(max_attempts=3, base_delay=0.5)
    def unreliable_api_call():
        if random.random() < 0.6:
            raise ConnectionError("Сервис временно недоступен")
        return {"status": "success", "timestamp": time.time()}
    
    # Выполняем несколько вызовов
    for i in range(5):
        try:
            result = unreliable_api_call()
            print(f"Вызов {i+1}: {result}")
        except Exception as e:
            print(f"Вызов {i+1}: Неудача - {e}")
        time.sleep(1)
    
    # Использование декоратора для устойчивой операции
    print("\nУстойчивая операция:")
    
    @create_resilient_operation("payment_service", ServiceType.EXTERNAL_API)
    def process_payment(amount: float, user_id: str):
        # Симулируем платежную операцию
        if random.random() < 0.8:
            raise ConnectionError("Платежный сервис недоступен")
        return {"transaction_id": "TXN123", "amount": amount, "status": "completed"}
    
    # Тестируем устойчивую операцию
    try:
        result = process_payment(100.0, "user123")
        print(f"Результат платежа: {result}")
    except Exception as e:
        print(f"Ошибка платежа: {e}")


def example_6_async_operations():
    """Пример 6: Асинхронные операции с устойчивостью"""
    print("\n=== Пример 6: Асинхронные операции ===")
    
    async def async_api_call(delay: float = 1.0):
        """Асинхронный API вызов"""
        await asyncio.sleep(delay)
        if random.random() < 0.5:
            raise TimeoutError("Асинхронный API недоступен")
        return {"async_result": "success", "delay": delay}
    
    async def run_async_example():
        # Создаем асинхронную retry политику
        config = RetryPolicyConfig(
            max_attempts=3,
            base_delay=0.5,
            max_delay=2.0
        )
        retry_policy = RetryPolicy(config, "async_retry")
        
        # Выполняем асинхронную операцию с ретраями
        try:
            start_time = time.time()
            result = await retry_policy.execute_async(async_api_call)
            end_time = time.time()
            
            print(f"Асинхронный результат: {result}")
            print(f"Время выполнения: {end_time - start_time:.2f}s")
            
        except Exception as e:
            print(f"Асинхронная ошибка: {e}")
    
    # Запускаем асинхронный пример
    asyncio.run(run_async_example())


def example_7_monitoring_and_status():
    """Пример 7: Мониторинг и статус системы устойчивости"""
    print("\n=== Пример 7: Мониторинг системы ===")
    
    from . import get_resilience_status

    # Создаем несколько компонентов устойчивости
    circuit_breaker = create_circuit_breaker("monitored_service", ServiceType.EXTERNAL_API)
    retry_policy = create_retry_policy("monitored_retry", "external_api")
    degradation_manager = get_graceful_degradation_manager()
    
    degradation_manager.register_service("monitored_service")
    
    # Симулируем операции
    def monitored_operation():
        if random.random() < 0.3:
            raise ConnectionError("Ошибка мониторинга")
        return {"monitored": "success"}
    
    # Выполняем операции
    for i in range(10):
        try:
            # Вызываем с retry и circuit breaker
            result = retry_policy.execute(
                lambda: circuit_breaker.call(monitored_operation)
            )
            degradation_manager.evaluate_request("monitored_service", "monitored_operation", True)
            print(f"Операция {i+1}: Успех")
        except Exception as e:
            degradation_manager.evaluate_request("monitored_service", "monitored_operation", False)
            print(f"Операция {i+1}: Ошибка - {e}")
    
    # Получаем статус системы
    status = get_resilience_status()
    print(f"\nСтатус системы устойчивости:")
    print(f"Circuit Breakers: {len(status['circuit_breakers'])}")
    print(f"Retry Policies: {len(status['retry_policies'])}")
    print(f"Services in degradation: {len(status['graceful_degradation']['services'])}")
    
    # Детальный статус circuit breaker
    cb_status = circuit_breaker.get_state()
    print(f"\nДетали Circuit Breaker '{cb_status['name']}':")
    print(f"  Состояние: {cb_status['state']}")
    print(f"  Всего запросов: {cb_status['stats']['total_requests']}")
    print(f"  Успешных: {cb_status['stats']['success_count']}")
    print(f"  Неуспешных: {cb_status['stats']['failure_count']}")
    print(f"  Процент успеха: {cb_status['stats']['success_rate']:.1f}%")


def example_8_configuration_and_customization():
    """Пример 8: Конфигурация и кастомизация"""
    print("\n=== Пример 8: Конфигурация системы ===")
    
    from .config import (CircuitBreakerConfig, GracefulDegradationConfig,
                         ResilienceConfig, RetryPolicyConfig, update_config)

    # Создаем кастомную конфигурацию
    custom_config = ResilienceConfig(
        circuit_breakers={
            ServiceType.EXTERNAL_API: CircuitBreakerConfig(
                failure_threshold=2,
                timeout=30.0,
                success_threshold=5
            )
        },
        retry_policies={
            "custom": RetryPolicyConfig(
                max_attempts=5,
                base_delay=0.2,
                max_delay=10.0,
                jitter=True
            )
        },
        degradation=GracefulDegradationConfig(
            degradation_threshold=5,
            recovery_threshold=3,
            enable_notifications=True
        )
    )
    
    # Обновляем конфигурацию
    update_config(custom_config)
    
    # Создаем компоненты с кастомной конфигурацией
    custom_breaker = create_circuit_breaker("custom_service", ServiceType.EXTERNAL_API)
    custom_retry = create_retry_policy("custom_retry", "custom")
    
    print("Созданы компоненты с кастомной конфигурацией:")
    print(f"Circuit Breaker конфиг: failure_threshold={custom_breaker.config.failure_threshold}")
    print(f"Retry конфиг: max_attempts={custom_retry.config.max_attempts}")
    
    # Тестируем кастомные настройки
    def custom_test_operation():
        if random.random() < 0.4:
            raise ConnectionError("Кастомная ошибка")
        return "custom_success"
    
    try:
        result = custom_retry.execute(
            lambda: custom_breaker.call(custom_test_operation)
        )
        print(f"Результат кастомной операции: {result}")
    except Exception as e:
        print(f"Ошибка кастомной операции: {e}")


async def example_9_integration_with_web_framework():
    """Пример 9: Интеграция с веб-фреймворком (симуляция FastAPI)"""
    print("\n=== Пример 9: Интеграция с веб-фреймворком ===")
    
    # Симулируем FastAPI приложение с middleware
    class MockRequest:
        def __init__(self, path: str, method: str = "GET"):
            self.path = path
            self.method = method
    
    class MockResponse:
        def __init__(self, status_code: int = 200, content: str = "OK"):
            self.status_code = status_code
            self.content = content
    
    async def mock_endpoint_handler(request: MockRequest) -> Dict[str, Any]:
        """Симуляция эндпоинта API"""
        if random.random() < 0.2:
            raise TimeoutError("API endpoint недоступен")
        return {"message": f"Успешный ответ для {request.path}"}
    
    # Симулируем middleware для circuit breaker
    async def circuit_breaker_middleware(request: MockRequest, handler):
        """Middleware для автоматического применения circuit breaker"""
        breaker = create_circuit_breaker(f"endpoint_{request.path}", ServiceType.EXTERNAL_API)
        
        try:
            result = breaker.call(handler, request)
            if asyncio.iscoroutine(result):
                result = await result
            return MockResponse(200, str(result))
        except Exception as e:
            return MockResponse(503, f"Service Unavailable: {e}")
    
    # Тестируем интеграцию
    test_requests = [
        MockRequest("/api/users"),
        MockRequest("/api/orders"),
        MockRequest("/api/products"),
    ]
    
    for request in test_requests:
        print(f"\nОбработка запроса: {request.method} {request.path}")
        
        response = await circuit_breaker_middleware(
            request, 
            lambda req: mock_endpoint_handler(req)
        )
        
        print(f"Ответ: {response.status_code} - {response.content}")


def run_all_examples():
    """Запуск всех примеров"""
    print("🚀 Запуск всех примеров системы устойчивости")
    print("=" * 60)
    
    try:
        example_1_basic_circuit_breaker()
        example_2_retry_with_exponential_backoff()
        example_3_graceful_degradation_levels()
        example_4_fallback_strategies()
        example_5_decorator_pattern()
        example_6_async_operations()
        example_7_monitoring_and_status()
        example_8_configuration_and_customization()
        example_9_integration_with_web_framework()
        
        print("\n" + "=" * 60)
        print("✅ Все примеры выполнены успешно!")
        
    except Exception as e:
        print(f"\n❌ Ошибка при выполнении примеров: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_examples()