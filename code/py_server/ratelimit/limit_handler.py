# [NEXUS IDENTITY] ID: -5682335831497462398 | DATE: 2025-11-19

"""
Система обработки превышения лимитов (Graceful Degradation)
Основана на стандартах обработки ошибок из 1С:Предприятие

Особенности:
- Информативные ответы с Retry-After заголовками
- Специализированные сообщения для разных типов лимитов
- Интеграция с системой мониторинга и алертов
- Recovery механизмы для автоматического восстановления
- Graceful degradation для критичных операций
"""

import asyncio
import json
import logging
import time
import uuid
import weakref
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse

# Настройка логгера
logger = logging.getLogger(__name__)


class LimitType(Enum):
    """Типы лимитов для специализированной обработки"""
    RATE_LIMIT = "rate_limit"  # Стандартный rate limiting
    CONCURRENT_REQUESTS = "concurrent_requests"  # Ограничение одновременных запросов
    API_QUOTA = "api_quota"  # Дневные/часовые квоты
    BANDWIDTH = "bandwidth"  # Лимиты трафика
    RESOURCE_INTENSIVE = "resource_intensive"  # Тяжелые операции
    EXTERNAL_API = "external_api"  # Лимиты внешних сервисов


class LimitSeverity(Enum):
    """Серьезность нарушения лимита"""
    LOW = "low"  # Мягкое превышение, предупреждение
    MEDIUM = "medium"  # Стандартное превышение лимита
    HIGH = "high"  # Критическое превышение
    CRITICAL = "critical"  # Экстремальное превышение


class HTTPStatusCode(Enum):
    """HTTP статусы для разных типов превышений лимитов"""
    TOO_MANY_REQUESTS = 429  # Стандартный ответ
    SERVICE_UNAVAILABLE = 503  # Extreme overload
    ENHANCE_YOUR_CALM = 420  # Дружественные API
    BANDWIDTH_LIMIT_EXCEEDED = 509  # Лимит трафика
    INSUFFICIENT_STORAGE = 507  # Переполнение квот


@dataclass
class LimitViolation:
    """Структура для описания нарушения лимита"""
    violation_id: str
    timestamp: str
    client_id: str
    limit_type: LimitType
    severity: LimitSeverity
    current_usage: int
    limit_value: int
    window_start: Optional[str] = None
    window_end: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    request_id: Optional[str] = None
    trace_id: Optional[str] = None
    estimated_recovery_time: Optional[int] = None  # секунды
    retry_after_seconds: Optional[int] = None
    rate_limit_headers: Optional[Dict[str, str]] = None
    business_context: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для логирования"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Конвертация в JSON для структурированного логирования"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


class RetryAfterCalculator:
    """
    Класс для расчета времени ожидания с учетом различных факторов
    Использует экспоненциальную задержку и адаптивные стратегии
    """
    
    def __init__(self):
        self.base_delay = 1  # Базовая задержка в секундах
        self.max_delay = 3600  # Максимальная задержка 1 час
        self.backoff_factor = 2  # Фактор экспоненциальной задержки
        self.jitter_range = 0.1  # Разброс для избежания thundering herd
    
    def calculate_delay(self, 
                       violation: LimitViolation, 
                       previous_attempts: int = 0,
                       client_reliability: float = 1.0) -> int:
        """
        Расчет времени ожидания с учетом:
        - Типа лимита
        - Серьезности нарушения
        - Истории клиента
        - Надежности клиента
        """
        
        # Базовый расчет на основе типа лимита
        base_delay = self._get_base_delay_by_limit_type(violation.limit_type)
        
        # Экспоненциальная задержка с учетом попыток
        exponential_delay = base_delay * (self.backoff_factor ** min(previous_attempts, 10))
        
        # Корректировка на основе серьезности
        severity_multiplier = self._get_severity_multiplier(violation.severity)
        adjusted_delay = exponential_delay * severity_multiplier
        
        # Корректировка на основе надежности клиента
        reliability_factor = max(0.1, client_reliability)
        final_delay = adjusted_delay / reliability_factor
        
        # Добавление jitter для избежания synchronized retries
        jitter = final_delay * (hash(str(violation.violation_id)) % 1000 / 1000 - 0.5) * self.jitter_range * 2
        final_delay += jitter
        
        # Применение минимальных и максимальных ограничений
        return max(1, min(int(final_delay), self.max_delay))
    
    def _get_base_delay_by_limit_type(self, limit_type: LimitType) -> int:
        """Базовая задержка в зависимости от типа лимита"""
        delay_map = {
            LimitType.RATE_LIMIT: 5,
            LimitType.CONCURRENT_REQUESTS: 2,
            LimitType.API_QUOTA: 300,  # 5 минут для квот
            LimitType.BANDWIDTH: 60,
            LimitType.RESOURCE_INTENSIVE: 30,
            LimitType.EXTERNAL_API: 10
        }
        return delay_map.get(limit_type, 5)
    
    def _get_severity_multiplier(self, severity: LimitSeverity) -> float:
        """Множитель задержки в зависимости от серьезности"""
        multiplier_map = {
            LimitSeverity.LOW: 0.5,
            LimitSeverity.MEDIUM: 1.0,
            LimitSeverity.HIGH: 2.0,
            LimitSeverity.CRITICAL: 5.0
        }
        return multiplier_map.get(severity, 1.0)


class LimitViolationLogger:
    """
    Система структурированного логирования нарушений лимитов
    Основана на стандартах 1С по структурированному логированию
    """
    
    def __init__(self):
        self.logger = logging.getLogger("limit_violations")
        self.alert_thresholds = {
            LimitSeverity.HIGH: 10,  # Превышения высокого уровня
            LimitSeverity.CRITICAL: 1  # Критические превышения
        }
    
    def log_violation(self, violation: LimitViolation):
        """Логирование нарушения в структурированном формате"""
        
        log_entry = {
            "event_type": "limit_violation",
            "timestamp": violation.timestamp,
            "violation_id": violation.violation_id,
            "client_id": violation.client_id,
            "limit_type": violation.limit_type.value,
            "severity": violation.severity.value,
            "current_usage": violation.current_usage,
            "limit_value": violation.limit_value,
            "retry_after_seconds": violation.retry_after_seconds,
            "estimated_recovery_time": violation.estimated_recovery_time,
            "endpoint": violation.endpoint,
            "method": violation.method,
            "request_id": violation.request_id,
            "trace_id": violation.trace_id,
            "error_code": violation.error_code,
            "ip_address": self._mask_ip(violation.ip_address),
            "user_agent": self._truncate_user_agent(violation.user_agent),
            "business_context": violation.business_context
        }
        
        # Определение уровня логирования
        log_level = self._get_log_level(violation.severity)
        
        # Структурированное логирование в JSON
        self.logger.log(log_level, 
                       f"Limit violation: {violation.limit_type.value} exceeded", 
                       extra={"structured_data": log_entry})
        
        # Проверка необходимости отправки алерта
        self._check_alert_threshold(violation)
    
    def _mask_ip(self, ip_address: Optional[str]) -> Optional[str]:
        """Маскирование IP адреса для безопасности"""
        if not ip_address:
            return None
        
        # Маскирование последних октетов
        parts = ip_address.split('.')
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.***.***"
        
        return "***.***.***.***"
    
    def _truncate_user_agent(self, user_agent: Optional[str]) -> Optional[str]:
        """Усечение User-Agent для безопасного логирования"""
        if not user_agent:
            return None
        
        # Ограничение длины для избежания раздувания логов
        return user_agent[:100] + "..." if len(user_agent) > 100 else user_agent
    
    def _get_log_level(self, severity: LimitSeverity) -> int:
        """Определение уровня логирования"""
        level_map = {
            LimitSeverity.LOW: logging.INFO,
            LimitSeverity.MEDIUM: logging.WARNING,
            LimitSeverity.HIGH: logging.ERROR,
            LimitSeverity.CRITICAL: logging.CRITICAL
        }
        return level_map.get(severity, logging.WARNING)
    
    def _check_alert_threshold(self, violation: LimitViolation):
        """Проверка порогов для отправки алертов"""
        if violation.severity in self.alert_thresholds:
            # Здесь можно интегрировать с системами мониторинга
            # Например, отправка в Prometheus, Grafana, или другую систему алертов
            self._send_alert(violation)
    
    def _send_alert(self, violation: LimitViolation):
        """Отправка алерта в систему мониторинга"""
        alert_data = {
            "alert_type": "limit_violation",
            "severity": violation.severity.value,
            "limit_type": violation.limit_type.value,
            "client_id": violation.client_id,
            "violation_id": violation.violation_id,
            "timestamp": violation.timestamp,
            "current_usage": violation.current_usage,
            "limit_value": violation.limit_value,
            "retry_after_seconds": violation.retry_after_seconds,
            "endpoint": violation.endpoint
        }
        
        # Интеграция с системой мониторинга
        logger.critical(f"LIMIT VIOLATION ALERT: {json.dumps(alert_data, ensure_ascii=False)}")


class AdaptiveResponse:
    """
    Генератор адаптивных ответов в зависимости от типа клиента и контекста
    Обеспечивает отличный UX даже при превышении лимитов
    """
    
    def __init__(self):
        self.retry_after_header = "Retry-After"
        self.rate_limit_headers = {
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining", 
            "X-RateLimit-Reset",
            "X-RateLimit-Window"
        }
    
    def create_response(self, 
                       violation: LimitViolation,
                       client_type: str = "default",
                       language: str = "ru") -> Dict[str, Any]:
        """
        Создание адаптивного ответа с учетом:
        - Типа клиента (API, веб-интерфейс, мобильное приложение)
        - Языка пользователя
        - Серьезности нарушения
        - Контекста бизнес-операции
        """
        
        http_status = self._get_http_status(violation)
        message = self._get_user_message(violation, client_type, language)
        
        response_data = {
            "error": {
                "code": violation.error_code or f"LIMIT_{violation.limit_type.value.upper()}",
                "message": message["user"],
                "details": message["details"],
                "help_url": message.get("help_url"),
                "violation_id": violation.violation_id,
                "timestamp": violation.timestamp
            },
            "retry_info": {
                "retry_after_seconds": violation.retry_after_seconds,
                "estimated_recovery_time": violation.estimated_recovery_time,
                "window_start": violation.window_start,
                "window_end": violation.window_end
            }
        }
        
        # Добавление бизнес-контекста для важных операций
        if violation.business_context:
            response_data["business_context"] = violation.business_context
        
        return {
            "status_code": http_status,
            "headers": self._build_headers(violation),
            "body": response_data
        }
    
    def _get_http_status(self, violation: LimitViolation) -> int:
        """Выбор HTTP статуса в зависимости от типа лимита"""
        status_map = {
            LimitType.RATE_LIMIT: HTTPStatusCode.TOO_MANY_REQUESTS.value,
            LimitType.CONCURRENT_REQUESTS: HTTPStatusCode.TOO_MANY_REQUESTS.value,
            LimitType.API_QUOTA: HTTPStatusCode.INSUFFICIENT_STORAGE.value,
            LimitType.BANDWIDTH: HTTPStatusCode.BANDWIDTH_LIMIT_EXCEEDED.value,
            LimitType.RESOURCE_INTENSIVE: HTTPStatusCode.SERVICE_UNAVAILABLE.value,
            LimitType.EXTERNAL_API: HTTPStatusCode.ENHANCE_YOUR_CALM.value
        }
        
        base_status = status_map.get(violation.limit_type, HTTPStatusCode.TOO_MANY_REQUESTS.value)
        
        # Корректировка на основе серьезности
        if violation.severity == LimitSeverity.CRITICAL:
            return HTTPStatusCode.SERVICE_UNAVAILABLE.value
        
        return base_status
    
    def _get_user_message(self, 
                         violation: LimitViolation, 
                         client_type: str, 
                         language: str) -> Dict[str, str]:
        """Получение локализованного сообщения для пользователя"""
        
        # База сообщений на русском языке
        messages_ru = {
            LimitType.RATE_LIMIT: {
                "user": "Слишком много запросов. Пожалуйста, повторите попытку позже.",
                "details": "Превышена частота запросов. Сервис ограничивает количество обращений для обеспечения стабильной работы."
            },
            LimitType.CONCURRENT_REQUESTS: {
                "user": "Слишком много одновременных операций. Подождите завершения текущих операций.",
                "details": "Сервис обрабатывает максимально допустимое количество одновременных запросов."
            },
            LimitType.API_QUOTA: {
                "user": "Превышена дневная квота API. Попробуйте завтра или обратитесь к администратору.",
                "details": "Исчерпана выделенная квота запросов на текущий период времени."
            },
            LimitType.BANDWIDTH: {
                "user": "Превышен лимит трафика. Попробуйте загрузить данные меньшего размера.",
                "details": "Сервис ограничивает объем передаваемых данных для обеспечения стабильности."
            },
            LimitType.RESOURCE_INTENSIVE: {
                "user": "Сервис перегружен тяжелыми операциями. Попробуйте позже.",
                "details": "Система ограничивает ресурсоемкие операции в период высокой нагрузки."
            },
            LimitType.EXTERNAL_API: {
                "user": "Внешний сервис временно недоступен. Попробуйте позже.",
                "details": "Превышены лимиты внешнего API или сервис недоступен."
            }
        }
        
        # Базовые сообщения
        base_message = messages_ru.get(violation.limit_type, {
            "user": "Временные ограничения. Попробуйте позже.",
            "details": "Сервис временно недоступен из-за ограничений."
        })
        
        # Адаптация сообщения в зависимости от типа клиента
        if client_type == "api":
            base_message["details"] += f" Error Code: LIMIT_{violation.limit_type.value.upper()}"
        elif client_type == "mobile":
            base_message["user"] += " 🔄"
        elif client_type == "web":
            pass  # Сообщения уже оптимизированы для веба
        
        # Добавление ссылки на справку для критических случаев
        if violation.severity == LimitSeverity.CRITICAL:
            base_message["help_url"] = "/docs/rate-limits-help"
        
        return base_message
    
    def _build_headers(self, violation: LimitViolation) -> Dict[str, str]:
        """Построение HTTP заголовков для ответа"""
        headers = {
            "Retry-After": str(violation.retry_after_seconds or 60),
            "X-RateLimit-Type": violation.limit_type.value,
            "X-RateLimit-Severity": violation.severity.value,
            "X-Violation-ID": violation.violation_id,
            "Content-Type": "application/json; charset=utf-8"
        }
        
        # Добавление rate limit headers если доступны
        if violation.rate_limit_headers:
            headers.update(violation.rate_limit_headers)
        
        # Добавление информации о окне лимита
        if violation.window_start:
            headers["X-RateLimit-Window-Start"] = violation.window_start
        if violation.window_end:
            headers["X-RateLimit-Window-End"] = violation.window_end
        
        return headers


class CircuitBreaker:
    """
    Circuit Breaker для extreme cases превышения лимитов
    Обеспечивает автоматическое восстановление и защиту системы
    """
    
    class State(Enum):
        CLOSED = "closed"  # Нормальное состояние
        OPEN = "open"  # Цепь разомкнута, блокировка запросов
        HALF_OPEN = "half_open"  # Пробная разблокировка
    
    def __init__(self, 
                 failure_threshold: int = 10,
                 recovery_timeout: int = 60,
                 expected_exception: type = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = self.State.CLOSED
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Выполнение функции через circuit breaker
        """
        async with self._lock:
            if self.state == self.State.OPEN:
                if self._should_attempt_reset():
                    self.state = self.State.HALF_OPEN
                else:
                    raise CircuitBreakerOpenException("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except self.expected_exception as e:
            await self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Проверка, можно ли попытаться сбросить circuit breaker"""
        return (self.last_failure_time and 
                time.time() - self.last_failure_time >= self.recovery_timeout)
    
    async def _on_success(self):
        """Обработка успешного выполнения"""
        async with self._lock:
            self.failure_count = 0
            if self.state == self.State.HALF_OPEN:
                self.state = self.State.CLOSED
                logger.info("Circuit breaker reset to CLOSED state")
    
    async def _on_failure(self):
        """Обработка неудачного выполнения"""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == self.State.CLOSED and self.failure_count >= self.failure_threshold:
                self.state = self.State.OPEN
                logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
            elif self.state == self.State.HALF_OPEN:
                self.state = self.State.OPEN
                logger.warning("Circuit breaker reopened during HALF_OPEN state")


class CircuitBreakerOpenException(Exception):
    """Исключение при разомкнутом circuit breaker"""


class RateLimitHandler:
    """
    Основной класс для обработки превышения лимитов
    Обеспечивает graceful degradation и автоматическое восстановление
    """
    
    def __init__(self):
        self.retry_calculator = RetryAfterCalculator()
        self.violation_logger = LimitViolationLogger()
        self.adaptive_response = AdaptiveResponse()
        
        # Хранилище для отслеживания состояния клиентов
        self.client_states = weakref.WeakValueDictionary()
        
        # Circuit breaker для extreme cases
        self.circuit_breakers = {
            limit_type: CircuitBreaker(failure_threshold=20, recovery_timeout=300)
            for limit_type in LimitType
        }
        
        # Колбэки для мониторинга
        self.monitoring_callbacks: List[Callable] = []
    
    async def handle_limit_violation(self, 
                                    request: Request,
                                    limit_type: LimitType,
                                    current_usage: int,
                                    limit_value: int,
                                    business_context: Optional[Dict[str, Any]] = None) -> Response:
        """
        Основной метод обработки нарушения лимита
        """
        violation_id = str(uuid.uuid4())
        client_id = self._extract_client_id(request)
        
        # Определение серьезности нарушения
        severity = self._determine_severity(limit_type, current_usage, limit_value)
        
        # Получение информации о клиенте
        client_reliability = await self._get_client_reliability(client_id)
        
        # Создание описания нарушения
        violation = LimitViolation(
            violation_id=violation_id,
            timestamp=datetime.utcnow().isoformat(),
            client_id=client_id,
            limit_type=limit_type,
            severity=severity,
            current_usage=current_usage,
            limit_value=limit_value,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None,
            endpoint=str(request.url.path),
            method=request.method,
            request_id=request.headers.get("x-request-id") or str(uuid.uuid4()),
            trace_id=request.headers.get("x-trace-id"),
            business_context=business_context
        )
        
        # Расчет времени ожидания
        retry_after_seconds = self.retry_calculator.calculate_delay(
            violation, 
            previous_attempts=await self._get_client_attempts(client_id, limit_type),
            client_reliability=client_reliability
        )
        
        violation.retry_after_seconds = retry_after_seconds
        violation.estimated_recovery_time = retry_after_seconds
        
        # Логирование нарушения
        self.violation_logger.log_violation(violation)
        
        # Отправка в систему мониторинга
        await self._notify_monitoring(violation)
        
        # Проверка circuit breaker
        try:
            await self.circuit_breakers[limit_type].call(self._create_graceful_response, violation, request)
        except CircuitBreakerOpenException:
            return await self._create_extreme_response(violation, request)
        
        return await self._create_response(violation, request)
    
    def _extract_client_id(self, request: Request) -> str:
        """Извлечение идентификатора клиента"""
        # Приоритеты: API Key, User ID, IP Address
        api_key = request.headers.get("x-api-key")
        if api_key:
            return f"api_key:{hash(api_key) % 1000000}"  # Хеширование для безопасности
        
        user_id = request.headers.get("x-user-id")
        if user_id:
            return f"user:{user_id}"
        
        ip_address = request.client.host if request.client else "unknown"
        return f"ip:{ip_address}"
    
    def _determine_severity(self, 
                          limit_type: LimitType, 
                          current_usage: int, 
                          limit_value: int) -> LimitSeverity:
        """Определение серьезности нарушения лимита"""
        ratio = current_usage / limit_value
        
        if ratio >= 5.0:
            return LimitSeverity.CRITICAL
        elif ratio >= 2.0:
            return LimitSeverity.HIGH
        elif ratio >= 1.5:
            return LimitSeverity.MEDIUM
        else:
            return LimitSeverity.LOW
    
    async def _get_client_reliability(self, client_id: str) -> float:
        """Оценка надежности клиента на основе истории"""
        # Получение из кеша или базы данных
        # Здесь может быть сложная логика на основе истории нарушений
        
        # Простая реализация: начинаем с базовой надежности
        return 1.0
    
    async def _get_client_attempts(self, client_id: str, limit_type: LimitType) -> int:
        """Получение количества попыток клиента"""
        # Получение из кеша или базы данных
        return 0
    
    async def _notify_monitoring(self, violation: LimitViolation):
        """Уведомление системы мониторинга"""
        for callback in self.monitoring_callbacks:
            try:
                await callback(violation)
            except Exception as e:
                logger.error(f"Error in monitoring callback: {e}")
    
    async def _create_response(self, violation: LimitViolation, request: Request) -> Response:
        """Создание стандартного ответа"""
        client_type = self._determine_client_type(request)
        language = self._determine_language(request)
        
        response_data = self.adaptive_response.create_response(
            violation, client_type, language
        )
        
        return JSONResponse(
            status_code=response_data["status_code"],
            content=response_data["body"],
            headers=response_data["headers"]
        )
    
    async def _create_graceful_response(self, violation: LimitViolation, request: Request) -> Response:
        """Создание ответа с graceful degradation"""
        # Добавление альтернативных данных или reduced functionality
        response_data = self.adaptive_response.create_response(
            violation, self._determine_client_type(request), self._determine_language(request)
        )
        
        # Добавление информации о degraded functionality
        response_data["body"]["degraded_functionality"] = {
            "available": True,
            "reduced_capabilities": True,
            "message": "Сервис работает в режиме ограниченной функциональности"
        }
        
        return JSONResponse(
            status_code=response_data["status_code"],
            content=response_data["body"],
            headers=response_data["headers"]
        )
    
    async def _create_extreme_response(self, violation: LimitViolation, request: Request) -> Response:
        """Создание ответа для extreme cases"""
        extreme_response = {
            "error": {
                "code": "CIRCUIT_BREAKER_OPEN",
                "message": "Сервис временно недоступен из-за высокой нагрузки. Попробуйте позже.",
                "violation_id": violation.violation_id,
                "timestamp": violation.timestamp
            },
            "status": "degraded",
            "retry_info": {
                "retry_after_seconds": 300,  # 5 минут для extreme cases
                "message": "Автоматическое восстановление через 5 минут"
            }
        }
        
        headers = {
            "Retry-After": "300",
            "X-Status": "circuit_breaker_open",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        return JSONResponse(
            status_code=HTTPStatusCode.SERVICE_UNAVAILABLE.value,
            content=extreme_response,
            headers=headers
        )
    
    def _determine_client_type(self, request: Request) -> str:
        """Определение типа клиента"""
        user_agent = request.headers.get("user-agent", "").lower()
        
        if "mobile" in user_agent or "android" in user_agent or "iphone" in user_agent:
            return "mobile"
        elif "api" in user_agent or "curl" in user_agent or "postman" in user_agent:
            return "api"
        else:
            return "web"
    
    def _determine_language(self, request: Request) -> str:
        """Определение языка пользователя"""
        accept_language = request.headers.get("accept-language", "")
        if "ru" in accept_language:
            return "ru"
        elif "en" in accept_language:
            return "en"
        else:
            return "ru"  # По умолчанию русский
    
    def add_monitoring_callback(self, callback: Callable):
        """Добавление колбэка для мониторинга"""
        self.monitoring_callbacks.append(callback)
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики работы обработчика"""
        stats = {
            "circuit_breaker_states": {
                limit_type.value: breaker.state.value
                for limit_type, breaker in self.circuit_breakers.items()
            },
            "total_callbacks": len(self.monitoring_callbacks)
        }
        return stats


# Фабричная функция для создания middleware
def create_rate_limit_middleware(handler: RateLimitHandler) -> Callable:
    """Создание FastAPI middleware для интеграции с обработчиком лимитов"""
    
    async def middleware(request: Request, call_next):
        try:
            # Извлечение информации о лимитах из контекста
            limit_info = getattr(request.state, 'limit_info', None)
            
            if limit_info and limit_info.get('violated'):
                # Обработка нарушения лимита
                response = await handler.handle_limit_violation(
                    request=request,
                    limit_type=limit_info['limit_type'],
                    current_usage=limit_info['current_usage'],
                    limit_value=limit_info['limit_value'],
                    business_context=limit_info.get('business_context')
                )
                return response
            
            # Нормальное выполнение запроса
            response = await call_next(request)
            return response
            
        except Exception as e:
            logger.error(f"Error in rate limit middleware: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": {"code": "INTERNAL_ERROR", "message": "Внутренняя ошибка сервера"}}
            )
    
    return middleware


# Пример использования
async def example_usage():
    """Пример использования обработчика лимитов"""
    
    handler = RateLimitHandler()
    
    # Создание mock request
    class MockRequest:
        def __init__(self):
            self.client = type('Client', (), {'host': '192.168.1.100'})()
            self.headers = {'user-agent': 'Mozilla/5.0', 'x-api-key': 'test-key'}
            self.method = 'POST'
            self.url = type('URL', (), {'path': '/api/data'})()
    
    request = MockRequest()
    
    # Обработка нарушения лимита
    response = await handler.handle_limit_violation(
        request=request,
        limit_type=LimitType.RATE_LIMIT,
        current_usage=150,
        limit_value=100,
        business_context={"operation": "data_export", "size": "large"}
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    
    # Получение статистики
    stats = await handler.get_statistics()
    print(f"Statistics: {stats}")


if __name__ == "__main__":
    asyncio.run(example_usage())