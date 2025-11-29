# [NEXUS IDENTITY] ID: 6203532718908278001 | DATE: 2025-11-19

"""
Тесты для системы устойчивости

Комплексное тестирование всех компонентов: circuit breaker, graceful degradation,
retry политики и fallback стратегии.
"""

import threading
import time
import unittest

from resilience import (CircuitBreaker, CircuitBreakerConfig,
                        CircuitBreakerOpenError, CircuitBreakerState,
                        DegradationLevel, FallbackStrategyManager,
                        GracefulDegradationConfig, GracefulDegradationManager, RetryPolicy)
from resilience import \
    RetryPolicyConfig  # Circuit Breaker; Graceful Degradation; Retry Policy; Fallback Strategies; Configuration; Utils
from resilience import (ServiceContext, ServiceType, create_circuit_breaker,
                        create_retry_policy, get_graceful_degradation_manager, get_resilience_status,
                        reset_all_resilience_systems)


class TestCircuitBreaker(unittest.TestCase):
    """Тесты для Circuit Breaker"""
    
    def setUp(self):
        self.config = CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=2,
            timeout=5.0,
            time_window=10.0
        )
        self.breaker = CircuitBreaker("test_service", self.config)
    
    def test_circuit_breaker_initial_state(self):
        """Тест начального состояния circuit breaker"""
        self.assertEqual(self.breaker.state, CircuitBreakerState.CLOSED)
        self.assertEqual(self.breaker.stats.total_requests, 0)
        self.assertEqual(self.breaker.stats.failure_count, 0)
        self.assertEqual(self.breaker.stats.success_count, 0)
    
    def test_successful_calls(self):
        """Тест успешных вызовов"""
        def success_func():
            return "success"
        
        for _ in range(3):
            result = self.breaker.call(success_func)
            self.assertEqual(result, "success")
        
        self.assertEqual(self.breaker.stats.total_requests, 3)
        self.assertEqual(self.breaker.stats.success_count, 3)
        self.assertEqual(self.breaker.state, CircuitBreakerState.CLOSED)
    
    def test_failed_calls_trigger_circuit_breaker(self):
        """Тест того, что неудачные вызовы активируют circuit breaker"""
        def failing_func():
            raise ConnectionError("Service unavailable")
        
        # Выполняем неудачные вызовы до порога
        for i in range(3):
            with self.assertRaises(ConnectionError):
                self.breaker.call(failing_func)
        
        self.assertEqual(self.breaker.state, CircuitBreakerState.OPEN)
        self.assertEqual(self.breaker.stats.failure_count, 3)
    
    def test_circuit_breaker_open_state(self):
        """Тест состояния OPEN circuit breaker"""
        def failing_func():
            raise ConnectionError("Service unavailable")
        
        # Активируем circuit breaker
        for _ in range(3):
            with self.assertRaises(ConnectionError):
                self.breaker.call(failing_func)
        
        # Проверяем, что все вызовы заблокированы
        with self.assertRaises(CircuitBreakerOpenError):
            self.breaker.call(lambda: "should not execute")
    
    def test_circuit_breaker_half_open_recovery(self):
        """Тест восстановления через HALF_OPEN состояние"""
        def failing_func():
            raise ConnectionError("Service unavailable")
        
        # Активируем circuit breaker
        for _ in range(3):
            with self.assertRaises(ConnectionError):
                self.breaker.call(failing_func)
        
        self.assertEqual(self.breaker.state, CircuitBreakerState.OPEN)
        
        # Имитируем прошествие времени (таймаут)
        self.breaker.stats.last_failure_time = time.time() - 10.0
        
        # Первый вызов должен перевести в HALF_OPEN
        with self.assertRaises(ConnectionError):
            self.breaker.call(failing_func)
        
        self.assertEqual(self.breaker.state, CircuitBreakerState.HALF_OPEN)
    
    def test_circuit_breaker_success_recovery(self):
        """Тест успешного восстановления из HALF_OPEN"""
        def mixed_func():
            # Первые два вызова - ошибки, следующие - успех
            if mixed_func.call_count < 2:
                mixed_func.call_count += 1
                raise ConnectionError("Service unavailable")
            mixed_func.call_count += 1
            return "success"
        
        mixed_func.call_count = 0
        
        # Активируем circuit breaker
        for _ in range(3):
            with self.assertRaises(ConnectionError):
                self.breaker.call(failing_func)
        
        # Переводим в HALF_OPEN симуляцией времени
        self.breaker.stats.last_failure_time = time.time() - 10.0
        
        # Успешные вызовы должны восстановить circuit breaker
        result = self.breaker.call(mixed_func)
        self.assertEqual(result, "success")
        self.assertEqual(self.breaker.state, CircuitBreakerState.HALF_OPEN)
        
        result = self.breaker.call(mixed_func)
        self.assertEqual(result, "success")
        self.assertEqual(self.breaker.state, CircuitBreakerState.CLOSED)
    
    def test_circuit_breaker_state_transitions(self):
        """Тест переходов состояний circuit breaker"""
        def failing_func():
            raise ConnectionError("Service unavailable")
        
        def success_func():
            return "success"
        
        # CLOSED -> OPEN
        for _ in range(3):
            with self.assertRaises(ConnectionError):
                self.breaker.call(failing_func)
        
        self.assertEqual(self.breaker.state, CircuitBreakerState.OPEN)
        self.assertEqual(len(self.breaker.stats.state_transitions), 1)
        
        # Переход в HALF_OPEN
        self.breaker.stats.last_failure_time = time.time() - 10.0
        
        with self.assertRaises(ConnectionError):
            self.breaker.call(failing_func)
        
        self.assertEqual(self.breaker.state, CircuitBreakerState.HALF_OPEN)
        
        # Переход обратно в CLOSED
        result = self.breaker.call(success_func)
        self.assertEqual(result, "success")
        result = self.breaker.call(success_func)
        self.assertEqual(result, "success")
        
        self.assertEqual(self.breaker.state, CircuitBreakerState.CLOSED)
    
    def test_circuit_breaker_cache(self):
        """Тест кэширования в circuit breaker"""
        config_with_cache = CircuitBreakerConfig(enable_caching=True, cache_ttl=60.0)
        breaker = CircuitBreaker("cached_service", config_with_cache)
        
        call_count = 0
        def expensive_func():
            nonlocal call_count
            call_count += 1
            return f"result_{call_count}"
        
        # Первый вызов
        result1 = breaker.call(expensive_func)
        self.assertEqual(result1, "result_1")
        self.assertEqual(call_count, 1)
        
        # Второй вызов должен взять из кэша
        result2 = breaker.call(expensive_func)
        self.assertEqual(result2, "result_1")  # Тот же результат
        self.assertEqual(call_count, 1)  # Функция не вызывалась повторно
    
    def test_circuit_breaker_reset(self):
        """Тест сброса circuit breaker"""
        def failing_func():
            raise ConnectionError("Service unavailable")
        
        # Активируем circuit breaker
        for _ in range(3):
            with self.assertRaises(ConnectionError):
                self.breaker.call(failing_func)
        
        self.assertEqual(self.breaker.state, CircuitBreakerState.OPEN)
        
        # Сбрасываем
        self.breaker.reset()
        
        self.assertEqual(self.breaker.state, CircuitBreakerState.CLOSED)
        self.assertEqual(self.breaker.stats.total_requests, 0)
        self.assertEqual(self.breaker.stats.failure_count, 0)
        self.assertEqual(self.breaker.stats.success_count, 0)


class TestGracefulDegradation(unittest.TestCase):
    """Тесты для Graceful Degradation"""
    
    def setUp(self):
        self.config = GracefulDegradationConfig(
            degradation_threshold=2,
            recovery_threshold=2
        )
        self.manager = GracefulDegradationManager(self.config)
        self.manager.register_service("test_service")
    
    def test_service_registration(self):
        """Тест регистрации сервиса"""
        level = self.manager.get_current_level("test_service")
        self.assertEqual(level, DegradationLevel.FULL_SERVICE)
    
    def test_evaluate_successful_request(self):
        """Тест оценки успешного запроса"""
        level = self.manager.evaluate_request("test_service", "test_op", True)
        self.assertEqual(level, DegradationLevel.FULL_SERVICE)
        
        metrics = self.manager.get_service_metrics("test_service")
        self.assertEqual(metrics.success_requests, 1)
        self.assertEqual(metrics.consecutive_successes, 1)
    
    def test_evaluate_failed_request(self):
        """Тест оценки неудачного запроса"""
        level = self.manager.evaluate_request("test_service", "test_op", False)
        self.assertEqual(level, DegradationLevel.FULL_SERVICE)
        
        metrics = self.manager.get_service_metrics("test_service")
        self.assertEqual(metrics.failed_requests, 1)
        self.assertEqual(metrics.consecutive_failures, 1)
    
    def test_degradation_activation(self):
        """Тест активации деградации"""
        # Выполняем неудачные запросы до порога деградации
        for i in range(2):
            level = self.manager.evaluate_request("test_service", f"op_{i}", False)
        
        # Должна активироваться деградация
        self.assertEqual(level, DegradationLevel.CACHED_DATA)
        
        metrics = self.manager.get_service_metrics("test_service")
        self.assertEqual(metrics.consecutive_failures, 2)
    
    def test_degradation_recovery(self):
        """Тест восстановления из деградации"""
        # Активируем деградацию
        for i in range(2):
            self.manager.evaluate_request("test_service", f"op_{i}", False)
        
        # Выполняем успешные запросы
        for i in range(2):
            level = self.manager.evaluate_request("test_service", f"op_success_{i}", True)
        
        # Должно произойти восстановление
        self.assertEqual(level, DegradationLevel.FULL_SERVICE)
    
    def test_multiple_services(self):
        """Тест работы с множественными сервисами"""
        self.manager.register_service("service_1")
        self.manager.register_service("service_2", DegradationLevel.CACHED_DATA)
        
        level1 = self.manager.get_current_level("service_1")
        level2 = self.manager.get_current_level("service_2")
        
        self.assertEqual(level1, DegradationLevel.FULL_SERVICE)
        self.assertEqual(level2, DegradationLevel.CACHED_DATA)
    
    def test_fallback_data_caching(self):
        """Тест кэширования fallback данных"""
        test_data = {"key": "value"}
        
        # Сохраняем fallback данные
        self.manager.store_fallback_data("test_service", "test_op", test_data)
        
        # Получаем обратно
        fallback_data = self.manager.get_fallback_data("test_service", "test_op")
        
        self.assertIsNotNone(fallback_data)
        self.assertEqual(fallback_data.data, test_data)
        self.assertFalse(fallback_data.is_expired())
    
    def test_force_degradation(self):
        """Тест принудительной деградации"""
        self.manager.force_degradation("test_service", DegradationLevel.MINIMAL_RESPONSE, "test_reason")
        
        level = self.manager.get_current_level("test_service")
        self.assertEqual(level, DegradationLevel.MINIMAL_RESPONSE)
    
    def test_degradation_report(self):
        """Тест отчета о деградации"""
        # Добавляем немного метрик
        self.manager.evaluate_request("test_service", "op1", True)
        self.manager.evaluate_request("test_service", "op2", False)
        
        report = self.manager.get_degradation_report()
        
        self.assertIn("timestamp", report)
        self.assertIn("total_services", report)
        self.assertIn("services", report)
        self.assertIn("test_service", report["services"])


class TestRetryPolicy(unittest.TestCase):
    """Тесты для Retry Policy"""
    
    def setUp(self):
        self.config = RetryPolicyConfig(
            max_attempts=3,
            base_delay=0.1,
            max_delay=1.0,
            exponential_base=2.0
        )
        self.retry_policy = RetryPolicy(self.config, "test_retry")
    
    def test_successful_execution(self):
        """Тест успешного выполнения"""
        def success_func():
            return "success"
        
        result = self.retry_policy.execute(success_func)
        self.assertEqual(result, "success")
        
        stats = self.retry_policy.get_stats()
        self.assertEqual(stats.total_attempts, 1)
        self.assertEqual(stats.successful_attempts, 1)
        self.assertEqual(stats.failed_attempts, 0)
    
    def test_retry_on_failure(self):
        """Тест ретраев при неудаче"""
        attempt_count = 0
        
        def failing_func():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ConnectionError("Temporary error")
            return "success_after_retry"
        
        start_time = time.time()
        result = self.retry_policy.execute(failing_func)
        end_time = time.time()
        
        self.assertEqual(result, "success_after_retry")
        self.assertEqual(attempt_count, 3)
        self.assertGreater(end_time - start_time, 0.1)  # Должна быть задержка
        
        stats = self.retry_policy.get_stats()
        self.assertEqual(stats.total_attempts, 3)
        self.assertEqual(stats.successful_attempts, 1)
        self.assertEqual(stats.failed_attempts, 2)
    
    def test_exhausted_retries(self):
        """Тест исчерпания всех ретраев"""
        def always_failing_func():
            raise ConnectionError("Permanent error")
        
        with self.assertRaises(ConnectionError):
            self.retry_policy.execute(always_failing_func)
        
        stats = self.retry_policy.get_stats()
        self.assertEqual(stats.total_attempts, 3)
        self.assertEqual(stats.successful_attempts, 0)
        self.assertEqual(stats.failed_attempts, 3)
    
    def test_non_retryable_exceptions(self):
        """Тест невозможных для ретрая исключений"""
        def non_retryable_func():
            raise ValueError("Invalid input")
        
        with self.assertRaises(ValueError):
            self.retry_policy.execute(non_retryable_func)
        
        stats = self.retry_policy.get_stats()
        self.assertEqual(stats.total_attempts, 1)  # Только одна попытка
        self.assertEqual(stats.failed_attempts, 1)
    
    def test_exponential_backoff_calculation(self):
        """Тест вычисления экспоненциальной задержки"""
        # Проверяем, что задержки увеличиваются экспоненциально
        delays = []
        for attempt in range(1, 5):
            delay = self.retry_policy._calculate_delay(attempt)
            delays.append(delay)
        
        # Проверяем, что задержки увеличиваются
        self.assertGreater(delays[1], delays[0])
        self.assertGreater(delays[2], delays[1])
        self.assertGreater(delays[3], delays[2])
        
        # Проверяем, что они экспоненциальные (приблизительно)
        expected_ratio = self.config.exponential_base
        actual_ratio = delays[1] / delays[0]
        self.assertAlmostEqual(actual_ratio, expected_ratio, places=1)
    
    def test_max_delay_limit(self):
        """Тест ограничения максимальной задержки"""
        # Создаем политику с маленьким max_delay
        config = RetryPolicyConfig(max_attempts=5, max_delay=0.2)
        policy = RetryPolicy(config)
        
        # Задержки должны быть ограничены max_delay
        for attempt in range(1, 5):
            delay = policy._calculate_delay(attempt)
            self.assertLessEqual(delay, config.max_delay)
    
    async def test_async_execution(self):
        """Тест асинхронного выполнения"""
        async def async_success_func():
            return "async_success"
        
        result = await self.retry_policy.execute_async(async_success_func)
        self.assertEqual(result, "async_success")
    
    async def test_async_retry(self):
        """Тест асинхронных ретраев"""
        attempt_count = 0
        
        async def async_failing_func():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise ConnectionError("Async temporary error")
            return "async_success_after_retry"
        
        result = await self.retry_policy.execute_async(async_failing_func)
        self.assertEqual(result, "async_success_after_retry")
        self.assertEqual(attempt_count, 2)


class TestFallbackStrategies(unittest.TestCase):
    """Тесты для Fallback Strategies"""
    
    def setUp(self):
        self.degradation_manager = get_graceful_degradation_manager()
        self.degradation_manager.register_service("test_service")
        
        self.fallback_manager = FallbackStrategyManager(self.degradation_manager)
    
    def test_1c_fallback_strategy(self):
        """Тест fallback стратегии для 1С"""
        def failing_1c_func():
            raise ConnectionError("1C service unavailable")
        
        context = ServiceContext(
            service_name="test_service",
            service_type=ServiceType.DB,
            operation="get_metadata"
        )
        
        # Устанавливаем уровень деградации для тестирования fallback
        self.degradation_manager.force_degradation("test_service", DegradationLevel.CACHED_DATA)
        
        result = self.fallback_manager.handle_service_fallback(
            ServiceType.DB, context, failing_1c_func
        )
        
        self.assertTrue(result.success)
        self.assertIn("fallback", result.data)
        self.assertEqual(result.source, "simplified")
    
    def test_oauth2_fallback_strategy(self):
        """Тест fallback стратегии для OAuth2"""
        def failing_oauth_func(user_id: str):
            raise TimeoutError("OAuth service unavailable")
        
        context = ServiceContext(
            service_name="test_service",
            service_type=ServiceType.OAUTH2,
            operation="authenticate"
        )
        
        self.degradation_manager.force_degradation("test_service", DegradationLevel.SIMPLIFIED_RESPONSE)
        
        result = self.fallback_manager.handle_service_fallback(
            ServiceType.OAUTH2, context, failing_oauth_func, user_id="test_user"
        )
        
        self.assertTrue(result.success)
        self.assertIn("access_token", result.data)
        self.assertTrue(result.data.get("fallback", False))
    
    def test_mcp_fallback_strategy(self):
        """Тест fallback стратегии для MCP"""
        def failing_mcp_func():
            raise ConnectionError("MCP service unavailable")
        
        context = ServiceContext(
            service_name="test_service",
            service_type=ServiceType.MCP_TOOL,
            operation="tools/list"
        )
        
        result = self.fallback_manager.handle_service_fallback(
            ServiceType.MCP_TOOL, context, failing_mcp_func
        )
        
        self.assertTrue(result.success)
        self.assertIn("tools", result.data)
        self.assertGreater(len(result.data["tools"]), 0)
    
    def test_fallback_data_caching(self):
        """Тест кэширования fallback данных"""
        # Сохраняем данные через fallback стратегию
        test_data = {"cached_result": "test_value"}
        self.degradation_manager.store_fallback_data("test_service", "test_op", test_data)
        
        # Получаем данные обратно
        cached_data = self.degradation_manager.get_fallback_data("test_service", "test_op")
        
        self.assertIsNotNone(cached_data)
        self.assertEqual(cached_data.data, test_data)


class TestConfiguration(unittest.TestCase):
    """Тесты для конфигурации"""
    
    def test_default_config(self):
        """Тест конфигурации по умолчанию"""
        from resilience.config import DEFAULT_CONFIG
        
        self.assertIsNotNone(DEFAULT_CONFIG)
        self.assertIn(ServiceType.EXTERNAL_API, DEFAULT_CONFIG.circuit_breakers)
        self.assertIn("default", DEFAULT_CONFIG.retry_policies)
    
    def test_custom_config(self):
        """Тест кастомной конфигурации"""
        custom_config = ResilienceConfig(
            circuit_breakers={
                ServiceType.EXTERNAL_API: CircuitBreakerConfig(failure_threshold=10)
            }
        )
        
        from resilience.config import update_config
        update_config(custom_config)
        
        # Проверяем, что конфигурация обновилась
        from resilience.config import get_circuit_breaker_config
        config = get_circuit_breaker_config(ServiceType.EXTERNAL_API)
        self.assertEqual(config.failure_threshold, 10)


class TestIntegration(unittest.TestCase):
    """Интеграционные тесты"""
    
    def setUp(self):
        # Очищаем все системы перед тестом
        reset_all_resilience_systems()
    
    def test_create_circuit_breaker(self):
        """Тест создания circuit breaker через фабрику"""
        breaker = create_circuit_breaker("integration_test", ServiceType.EXTERNAL_API)
        self.assertIsInstance(breaker, CircuitBreaker)
        self.assertEqual(breaker.name, "integration_test")
    
    def test_create_retry_policy(self):
        """Тест создания retry политики через фабрику"""
        policy = create_retry_policy("integration_test", "default")
        self.assertIsInstance(policy, RetryPolicy)
        self.assertEqual(policy.name, "integration_test")
    
    def test_resilience_status(self):
        """Тест получения статуса системы"""
        # Создаем несколько компонентов
        create_circuit_breaker("test_service", ServiceType.EXTERNAL_API)
        create_retry_policy("test_retry", "default")
        
        status = get_resilience_status()
        
        self.assertIn("circuit_breakers", status)
        self.assertIn("retry_policies", status)
        self.assertIn("graceful_degradation", status)
    
    def test_component_interaction(self):
        """Тест взаимодействия компонентов"""
        # Создаем компоненты
        breaker = create_circuit_breaker("interaction_test", ServiceType.EXTERNAL_API)
        retry_policy = create_retry_policy("interaction_retry", "default")
        
        # Выполняем операцию через все компоненты
        def test_operation():
            return "integration_success"
        
        result = retry_policy.execute(lambda: breaker.call(test_operation))
        self.assertEqual(result, "integration_success")
        
        # Проверяем статистику
        cb_stats = breaker.get_state()
        retry_stats = retry_policy.get_stats()
        
        self.assertEqual(cb_stats["stats"]["total_requests"], 1)
        self.assertEqual(retry_stats.total_attempts, 1)


class TestPerformance(unittest.TestCase):
    """Тесты производительности"""
    
    def test_circuit_breaker_performance(self):
        """Тест производительности circuit breaker"""
        config = CircuitBreakerConfig(failure_threshold=100)
        breaker = CircuitBreaker("perf_test", config)
        
        def fast_func():
            return "success"
        
        # Выполняем много быстрых вызовов
        start_time = time.time()
        for _ in range(1000):
            breaker.call(fast_func)
        end_time = time.time()
        
        # Должно выполняться быстро
        self.assertLess(end_time - start_time, 1.0)
        self.assertEqual(breaker.stats.total_requests, 1000)
    
    def test_retry_policy_performance(self):
        """Тест производительности retry политики"""
        config = RetryPolicyConfig(max_attempts=3, base_delay=0.01)
        policy = RetryPolicy(config, "perf_test")
        
        def fast_func():
            return "success"
        
        # Выполняем много вызовов
        start_time = time.time()
        for _ in range(100):
            policy.execute(fast_func)
        end_time = time.time()
        
        # Должно выполняться быстро (без задержек для успешных вызовов)
        self.assertLess(end_time - start_time, 1.0)
        self.assertEqual(policy.stats.total_attempts, 100)


class TestThreadSafety(unittest.TestCase):
    """Тесты многопоточности"""
    
    def test_circuit_breaker_thread_safety(self):
        """Тест потокобезопасности circuit breaker"""
        config = CircuitBreakerConfig(failure_threshold=50)
        breaker = CircuitBreaker("thread_test", config)
        
        def thread_func(thread_id):
            time.sleep(0.01)  # Небольшая задержка
            if thread_id < 30:  # Некоторые потоки "ошибаются"
                raise ConnectionError("Thread error")
            return f"success_{thread_id}"
        
        # Запускаем множественные потоки
        threads = []
        results = []
        results_lock = threading.Lock()
        
        def worker(thread_id):
            try:
                result = breaker.call(lambda: thread_func(thread_id))
                with results_lock:
                    results.append(("success", thread_id, result))
            except Exception as e:
                with results_lock:
                    results.append(("error", thread_id, str(e)))
        
        for i in range(50):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Ждем завершения всех потоков
        for thread in threads:
            thread.join()
        
        # Проверяем результаты
        self.assertEqual(len(results), 50)
        success_count = sum(1 for r in results if r[0] == "success")
        self.assertGreater(success_count, 0)
        
        # Circuit breaker должен работать корректно
        self.assertGreater(breaker.stats.total_requests, 0)
    
    def test_graceful_degradation_thread_safety(self):
        """Тест потокобезопасности graceful degradation"""
        manager = GracefulDegradationManager(GracefulDegradationConfig())
        manager.register_service("thread_test_service")
        
        results = []
        results_lock = threading.Lock()
        
        def worker(operation_id):
            # Смешиваем успешные и неудачные операции
            success = (operation_id % 2) == 0
            level = manager.evaluate_request("thread_test_service", f"op_{operation_id}", success)
            
            with results_lock:
                results.append((operation_id, success, level))
        
        # Запускаем множественные потоки
        threads = []
        for i in range(100):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Ждем завершения
        for thread in threads:
            thread.join()
        
        # Проверяем, что все операции были обработаны
        self.assertEqual(len(results), 100)
        
        # Метрики должны быть корректными
        metrics = manager.get_service_metrics("thread_test_service")
        self.assertEqual(metrics.total_requests, 100)


def run_all_tests():
    """Запуск всех тестов"""
    # Создаем test suite
    test_classes = [
        TestCircuitBreaker,
        TestGracefulDegradation,
        TestRetryPolicy,
        TestFallbackStrategies,
        TestConfiguration,
        TestIntegration,
        TestPerformance,
        TestThreadSafety
    ]
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Возвращаем результат
    return result.wasSuccessful()


if __name__ == "__main__":
    print("🧪 Запуск тестов системы устойчивости")
    print("=" * 60)
    
    success = run_all_tests()
    
    print("=" * 60)
    if success:
        print("✅ Все тесты прошли успешно!")
    else:
        print("❌ Некоторые тесты провалились!")
    
    exit(0 if success else 1)