"""
Единый API Gateway для 1C AI-экосистемы
Версия: 2.1.0

Улучшения:
- Structured logging
- Улучшена обработка ошибок

Объединяет все микросервисы в единую точку входа
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json
import httpx
from contextlib import asynccontextmanager

from fastapi import (
    FastAPI, APIRouter, Request, Response, HTTPException, Depends, 
    BackgroundTasks, status
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.datastructures import Headers
import time
import jwt
from jwt import PyJWTError
import redis
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

# Конфигурация сервисов
SERVICES_CONFIG = {
    "assistants": {
        "url": "http://localhost:8002",
        "health_endpoint": "/api/assistants/health",
        "name": "AI Assistants Service",
        "timeout": 30.0
    },
    "ml": {
        "url": "http://localhost:8001", 
        "health_endpoint": "/health",
        "name": "ML System Service",
        "timeout": 30.0
    },
    "risk": {
        "url": "http://localhost:8003",
        "health_endpoint": "/health", 
        "name": "Risk Management Service",
        "timeout": 30.0
    },
    "metrics": {
        "url": "http://localhost:8004",
        "health_endpoint": "/health",
        "name": "Metrics Service", 
        "timeout": 30.0
    }
}

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Pydantic модели для Gateway API
class GatewayHealthResponse(BaseModel):
    """Ответ о состоянии Gateway"""
    gateway_status: str
    timestamp: datetime
    version: str
    services: Dict[str, Dict[str, Any]]

class ServiceHealthResponse(BaseModel):
    """Состояние конкретного сервиса"""
    service_name: str
    status: str  # healthy, unhealthy, unknown
    response_time_ms: Optional[float] = None
    last_check: datetime
    error: Optional[str] = None

class GatewayMetrics(BaseModel):
    """Метрики Gateway"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time_ms: float
    requests_per_minute: Dict[str, int]
    service_call_counts: Dict[str, int]

class APIKeyRequest(BaseModel):
    """Запрос на проверку API ключа"""
    api_key: str = Field(..., description="API ключ для доступа")

class ServiceRequest(BaseModel):
    """Базовый запрос к сервису через Gateway"""
    service: str = Field(..., description="Название сервиса")
    endpoint: str = Field(..., description="Endpoint сервиса")
    method: str = Field(default="GET", description="HTTP метод")
    headers: Optional[Dict[str, str]] = None
    data: Optional[Dict[str, Any]] = None
    params: Optional[Dict[str, Any]] = None


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware для аутентификации"""
    
    def __init__(self, app, allowed_paths: List[str] = None):
        super().__init__(app)
        self.allowed_paths = allowed_paths or [
            "/health",
            "/metrics", 
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/gateway/health"
        ]
        # Использовать переменные окружения для API ключей
        import os
        api_keys_env = os.getenv("GATEWAY_API_KEYS", "")
        if api_keys_env:
            self.valid_api_keys = [key.strip() for key in api_keys_env.split(",") if key.strip()]
        else:
            # Fallback для development (в production должно быть через env)
            self.valid_api_keys = [
                "demo-key-12345",
                "admin-key-67890"
            ]
            logger.warning("Using default API keys. Set GATEWAY_API_KEYS environment variable for production!")
    
    async def dispatch(self, request: Request, call_next):
        """Middleware для аутентификации с input validation"""
        try:
            # Проверка разрешенных путей
            if request.url.path in self.allowed_paths:
                return await call_next(request)
            
            # Проверка API ключа
            api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization")
            
            # Если Authorization header содержит "Bearer ", извлекаем токен
            if api_key and api_key.startswith("Bearer "):
                api_key = api_key[7:].strip()
            
            if not api_key:
                logger.warning(
                    "API key not provided",
                    extra={
                        "path": request.url.path,
                        "method": request.method
                    }
                )
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "API ключ не предоставлен"}
                )
            
            # Validate API key length (prevent DoS)
            max_key_length = 500
            if len(api_key) > max_key_length:
                logger.warning(
                    "API key too long",
                    extra={
                        "path": request.url.path,
                        "method": request.method,
                        "key_length": len(api_key)
                    }
                )
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Недействительный API ключ"}
                )
            
            # Простая проверка API ключа (в продакшене использовать JWT или OAuth)
            if api_key not in self.valid_api_keys:
                logger.warning(
                    "Invalid API key",
                    extra={
                        "path": request.url.path,
                        "method": request.method,
                        "key_preview": api_key[:10] + "..." if len(api_key) > 10 else api_key
                    }
                )
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Недействительный API ключ"}
                )
            
            return await call_next(request)
        except Exception as e:
            logger.error(
                f"Error in AuthenticationMiddleware: {e}",
                extra={
                    "path": request.url.path if 'request' in locals() else None,
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware для логирования запросов"""
    
    def __init__(self, app):
        super().__init__(app)
        self.request_stats = {
            "total_requests": 0,
            "successful_requests": 0, 
            "failed_requests": 0,
            "response_times": [],
            "service_calls": {}
        }
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Логирование входящего запроса
        logger.info(
            f"Входящий запрос: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.url.query) if request.url.query else None
            }
        )
        
        self.request_stats["total_requests"] += 1
        
        try:
            response = await call_next(request)
            
            # Подсчет времени ответа
            response_time = (time.time() - start_time) * 1000
            self.request_stats["response_times"].append(response_time)
            
            # Статистика ответов
            if response.status_code < 400:
                self.request_stats["successful_requests"] += 1
            else:
                self.request_stats["failed_requests"] += 1
            
            # Логирование ответа
            logger.info(
                f"Ответ: {response.status_code}, время: {response_time:.2f}ms",
                extra={
                    "status_code": response.status_code,
                    "response_time_ms": response_time,
                    "method": request.method,
                    "path": request.url.path
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(
                "Ошибка обработки запроса",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "endpoint": endpoint if 'endpoint' in locals() else None,
                    "method": request.method if 'request' in locals() else None
                },
                exc_info=True
            )
            self.request_stats["failed_requests"] += 1
            raise


class ServiceHealthChecker:
    """Класс для проверки здоровья сервисов"""
    
    def __init__(self):
        self.services_status = {}
        self.last_check_times = {}
        
    async def check_service_health(self, service_name: str, config: Dict[str, Any]) -> ServiceHealthResponse:
        """Проверка здоровья конкретного сервиса с input validation"""
        # Input validation
        if not service_name or not isinstance(service_name, str):
            logger.warning(
                "Invalid service_name in check_service_health",
                extra={"service_name_type": type(service_name).__name__ if service_name else None}
            )
            return ServiceHealthResponse(
                service_name=service_name or "unknown",
                status="unknown",
                response_time_ms=0,
                last_check=datetime.now(),
                error="Invalid service name"
            )
        
        if not config or not isinstance(config, dict):
            logger.warning(
                "Invalid config in check_service_health",
                extra={"config_type": type(config).__name__ if config else None}
            )
            return ServiceHealthResponse(
                service_name=service_name,
                status="unknown",
                response_time_ms=0,
                last_check=datetime.now(),
                error="Invalid config"
            )
        
        # Validate required config fields
        if "url" not in config or "health_endpoint" not in config:
            logger.warning(
                "Missing required config fields in check_service_health",
                extra={"service_name": service_name, "config_keys": list(config.keys())}
            )
            return ServiceHealthResponse(
                service_name=service_name,
                status="unknown",
                response_time_ms=0,
                last_check=datetime.now(),
                error="Missing required config fields"
            )
        
        start_time = time.time()
        
        try:
            timeout = config.get("timeout", 30.0)
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                timeout = 30.0  # Default timeout
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                health_url = f"{config['url']}{config['health_endpoint']}"
                logger.debug(
                    "Checking health for service",
                    extra={"service_name": service_name, "health_url": health_url}
                )
                
                response = await client.get(health_url)
                
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    status = "healthy"
                    error = None
                else:
                    status = "unhealthy"
                    error = f"HTTP {response.status_code}"
                
        except httpx.TimeoutException as e:
            logger.warning(
                "Timeout checking health for service",
                extra={
                    "service_name": service_name,
                    "timeout": timeout,
                    "error_type": "TimeoutException"
                }
            )
            status = "unhealthy"
            error = "Timeout"
            response_time = timeout * 1000
            
        except httpx.ConnectError as e:
            logger.warning(
                "Connection error checking health for service",
                extra={
                    "service_name": service_name,
                    "url": config.get("url"),
                    "error_type": "ConnectError"
                }
            )
            status = "unhealthy"
            error = "Connection failed"
            response_time = (time.time() - start_time) * 1000
            
        except Exception as e:
            logger.error(
                "Unexpected error checking health for service",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "service_name": service_name
                },
                exc_info=True
            )
            status = "unhealthy"
            error = str(e)
            response_time = (time.time() - start_time) * 1000
        
        service_status = ServiceHealthResponse(
            service_name=service_name,
            status=status,
            response_time_ms=response_time,
            last_check=datetime.now(),
            error=error
        )
        
        self.services_status[service_name] = service_status
        self.last_check_times[service_name] = datetime.now()
        
        return service_status
    
    async def check_all_services(self) -> Dict[str, ServiceHealthResponse]:
        """Проверка здоровья всех сервисов"""
        tasks = []
        for service_name, config in SERVICES_CONFIG.items():
            task = self.check_service_health(service_name, config)
            tasks.append(task)
        
        # Optimized: Use asyncio.gather with timeout (best practice)
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=30.0  # Timeout для всех health checks
            )
        except asyncio.TimeoutError:
            logger.error(
                "Timeout при проверке health всех сервисов",
                extra={
                    "services_count": len(tasks),
                    "timeout": 30.0
                }
            )
            # Возвращаем частичные результаты
            results = [{"error": "timeout"} for _ in tasks]
        
        health_status = {}
        for i, (service_name, _) in enumerate(SERVICES_CONFIG.items()):
            if isinstance(results[i], Exception):
                health_status[service_name] = ServiceHealthResponse(
                    service_name=service_name,
                    status="unknown",
                    last_check=datetime.now(),
                    error=str(results[i])
                )
            else:
                health_status[service_name] = results[i]
        
        return health_status


class ProxyService:
    """Сервис для проксирования запросов к микросервисам"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0))
        
    async def proxy_request(
        self, 
        service: str, 
        endpoint: str, 
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> httpx.Response:
        """Проксирование запроса к сервису с input validation"""
        # Input validation
        if not service or not isinstance(service, str):
            logger.warning(
                "Invalid service in proxy_request",
                extra={"service_type": type(service).__name__ if service else None}
            )
            raise HTTPException(
                status_code=400,
                detail="Service name is required and must be a non-empty string"
            )
        
        if not endpoint or not isinstance(endpoint, str):
            logger.warning(
                "Invalid endpoint in proxy_request",
                extra={"endpoint_type": type(endpoint).__name__ if endpoint else None}
            )
            raise HTTPException(
                status_code=400,
                detail="Endpoint is required and must be a non-empty string"
            )
        
        # Validate endpoint length (prevent DoS)
        max_endpoint_length = 2000
        if len(endpoint) > max_endpoint_length:
            logger.warning(
                "Endpoint too long in proxy_request",
                extra={"endpoint_length": len(endpoint), "max_length": max_endpoint_length}
            )
            raise HTTPException(
                status_code=400,
                detail=f"Endpoint too long. Maximum length: {max_endpoint_length} characters"
            )
        
        # Validate method
        valid_methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]
        method_upper = method.upper() if method else "GET"
        if method_upper not in valid_methods:
            logger.warning(
                "Invalid method in proxy_request",
                extra={"method": method, "valid_methods": valid_methods}
            )
            raise HTTPException(
                status_code=400,
                detail=f"Invalid HTTP method: {method}. Valid methods: {', '.join(valid_methods)}"
            )
        
        if service not in SERVICES_CONFIG:
            logger.warning(
                f"Service not found: {service}",
                extra={"service": service, "available_services": list(SERVICES_CONFIG.keys())}
            )
            raise HTTPException(
                status_code=404, 
                detail=f"Сервис '{service}' не найден"
            )
        
        service_config = SERVICES_CONFIG[service]
        
        # Валидация входных данных (best practice: sanitize inputs)
        if endpoint and not endpoint.startswith('/'):
            endpoint = '/' + endpoint
        
        # Sanitize endpoint path (prevent path traversal)
        endpoint_original = endpoint
        endpoint = endpoint.replace('..', '').replace('//', '/')
        
        if endpoint != endpoint_original:
            logger.warning(
                "Endpoint sanitized (path traversal attempt?)",
                extra={"original": endpoint_original, "sanitized": endpoint}
            )
        
        # Подготовка URL
        url = f"{service_config['url']}{endpoint}"
        
        # Подготовка заголовков
        request_headers = headers or {}
        request_headers.update({
            "X-Gateway-Request": "true",
            "X-Forwarded-For": "1C-AI-Gateway"
        })
        
        # Проксирование запроса с улучшенной обработкой ошибок
        try:
            response = await self.client.request(
                method=method,
                url=url,
                headers=request_headers,
                json=data if method.upper() in ["POST", "PUT", "PATCH"] else None,
                params=params,
                timeout=service_config["timeout"]
            )
            
            return response
            
        except httpx.TimeoutException as e:
            logger.error(
                f"Timeout при обращении к сервису '{service}': {e}",
                extra={
                    "service": service,
                    "endpoint": endpoint,
                    "method": method,
                    "timeout": service_config.get("timeout", 30.0),
                    "error_type": "TimeoutException"
                }
            )
            raise HTTPException(
                status_code=504,
                detail=f"Таймаут при обращении к сервису '{service}'"
            )
        except httpx.ConnectError as e:
            logger.error(
                f"Connection error при обращении к сервису '{service}': {e}",
                extra={
                    "service": service,
                    "endpoint": endpoint,
                    "method": method,
                    "url": url,
                    "error_type": "ConnectError"
                }
            )
            raise HTTPException(
                status_code=503,
                detail=f"Сервис '{service}' недоступен"
            )
        except httpx.HTTPStatusError as e:
            logger.warning(
                f"HTTP error {e.response.status_code} от сервиса '{service}'",
                extra={
                    "service": service,
                    "endpoint": endpoint,
                    "method": method,
                    "status_code": e.response.status_code,
                    "response_preview": e.response.text[:200],
                    "error_type": "HTTPStatusError"
                }
            )
            # Пробрасываем статус код от upstream сервиса
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Ошибка от сервиса '{service}': {e.response.text[:200]}"
            )
        except Exception as e:
            logger.error(
                "Неожиданная ошибка проксирования к сервису",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "service": service,
                    "endpoint": endpoint,
                    "method": method,
                    "url": url
                },
                exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка проксирования к сервису '{service}'"
            )

# Глобальные экземпляры
health_checker = ServiceHealthChecker()
proxy_service = ProxyService()

# Redis для кэширования (опционально)
try:
    redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    redis_client.ping()
    redis_available = True
except (redis.RedisError, ConnectionError, Exception):
    redis_available = False
    redis_client = None

# Создание router
router = APIRouter()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager для FastAPI приложения"""
    # Startup
    logger.info(
        "🚀 Запуск API Gateway для 1C AI-экосистемы",
        extra={"services_count": len(SERVICES_CONFIG)}
    )
    
    # Проверка начального состояния сервисов
    try:
        initial_health = await health_checker.check_all_services()
        healthy_count = sum(1 for s in initial_health.values() if s.status == "healthy")
        logger.info(
            f"Начальное состояние сервисов: {healthy_count}/{len(initial_health)} healthy",
            extra={
                "healthy_count": healthy_count,
                "total_services": len(initial_health),
                "services_status": {k: v.status for k, v in initial_health.items()}
            }
        )
    except Exception as e:
        logger.error(
            f"Ошибка при начальной проверке сервисов: {e}",
            extra={"error_type": type(e).__name__},
            exc_info=True
        )
    
    yield
    
    # Shutdown
    logger.info("🛑 Остановка API Gateway")
    await proxy_service.client.aclose()


# Создание FastAPI приложения
app = FastAPI(
    title="1C AI-экосистема API Gateway",
    description="Единая точка входа для всех сервисов 1C AI-экосистемы",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Добавление middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080"
    ],  # Security: specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(AuthenticationMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Добавление rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ===== ENDPOINTS =====

@router.get("/")
async def root():
    """Корневой endpoint Gateway"""
    return {
        "service": "1C AI-экосистема API Gateway",
        "version": "1.0.0",
        "status": "running",
        "description": "Единая точка входа для всех микросервисов",
        "services": list(SERVICES_CONFIG.keys()),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/api/gateway/health", response_model=GatewayHealthResponse)
async def gateway_health():
    """Проверка состояния Gateway и всех сервисов"""
    try:
        services_health = await health_checker.check_all_services()
        
        return GatewayHealthResponse(
            gateway_status="healthy",
            timestamp=datetime.now(),
            version="1.0.0",
            services={
                name: {
                    "status": health.status,
                    "response_time_ms": health.response_time_ms,
                    "error": health.error
                }
                for name, health in services_health.items()
            }
        )
        
    except Exception as e:
        logger.error(
            "Ошибка при проверке здоровья",
            extra={
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        return GatewayHealthResponse(
            gateway_status="degraded",
            timestamp=datetime.now(),
            version="1.0.0",
            services={}
        )


@router.get("/api/gateway/services")
async def list_services():
    """Список всех доступных сервисов"""
    services_info = {}
    
    for service_name, config in SERVICES_CONFIG.items():
        services_info[service_name] = {
            "name": config["name"],
            "url": config["url"],
            "health_endpoint": config["health_endpoint"],
            "timeout": config["timeout"],
            "status": health_checker.services_status.get(service_name, {}).status or "unknown"
        }
    
    return {
        "services": services_info,
        "total_count": len(services_info),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/api/gateway/metrics")
async def gateway_metrics():
    """Метрики Gateway"""
    stats = RequestLoggingMiddleware.request_stats if hasattr(RequestLoggingMiddleware, 'request_stats') else {}
    
    # Подсчет запросов в минуту (упрощенная версия)
    rpm = {}
    for service in SERVICES_CONFIG.keys():
        rpm[service] = stats.get("service_calls", {}).get(service, 0)
    
    avg_response_time = 0
    if stats.get("response_times"):
        avg_response_time = sum(stats["response_times"]) / len(stats["response_times"])
    
    return GatewayMetrics(
        total_requests=stats.get("total_requests", 0),
        successful_requests=stats.get("successful_requests", 0),
        failed_requests=stats.get("failed_requests", 0),
        average_response_time_ms=avg_response_time,
        requests_per_minute=rpm,
        service_call_counts=stats.get("service_calls", {})
    )


@router.post("/api/gateway/proxy")
async def proxy_to_service(request: ServiceRequest):
    """Проксирование запроса к сервису"""
    try:
        response = await proxy_service.proxy_request(
            service=request.service,
            endpoint=request.endpoint,
            method=request.method,
            headers=request.headers,
            data=request.data,
            params=request.params
        )
        
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Ошибка проксирования",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "service": request.service if hasattr(request, 'service') else None
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/assistants/{path:path}")
@limiter.limit("100/minute")
async def proxy_assistants(request: Request, path: str = ""):
    """Проксирование запросов к AI Assistants API"""
    query_params = dict(request.query_params)
    
    response = await proxy_service.proxy_request(
        service="assistants",
        endpoint=f"/api/assistants/{path}",
        method=request.method,
        headers=dict(request.headers),
        data=await request.json() if request.method.upper() in ["POST", "PUT", "PATCH"] else None,
        params=query_params
    )
    
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.headers.get("content-type")
    )


@router.get("/api/ml/{path:path}")
@limiter.limit("50/minute") 
async def proxy_ml(request: Request, path: str = ""):
    """Проксирование запросов к ML System API"""
    query_params = dict(request.query_params)
    
    response = await proxy_service.proxy_request(
        service="ml",
        endpoint=f"/{path}",
        method=request.method,
        headers=dict(request.headers),
        data=await request.json() if request.method.upper() in ["POST", "PUT", "PATCH"] else None,
        params=query_params
    )
    
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.headers.get("content-type")
    )


@router.get("/api/risk/{path:path}")
@limiter.limit("30/minute")
async def proxy_risk(request: Request, path: str = ""):
    """Проксирование запросов к Risk Management API"""
    query_params = dict(request.query_params)
    
    response = await proxy_service.proxy_request(
        service="risk",
        endpoint=f"/{path}",
        method=request.method,
        headers=dict(request.headers),
        data=await request.json() if request.method.upper() in ["POST", "PUT", "PATCH"] else None,
        params=query_params
    )
    
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.headers.get("content-type")
    )


@router.get("/api/metrics/{path:path}")
@limiter.limit("200/minute")
async def proxy_metrics(request: Request, path: str = ""):
    """Проксирование запросов к Metrics API"""
    query_params = dict(request.query_params)
    
    response = await proxy_service.proxy_request(
        service="metrics",
        endpoint=f"/{path}",
        method=request.method,
        headers=dict(request.headers),
        data=await request.json() if request.method.upper() in ["POST", "PUT", "PATCH"] else None,
        params=query_params
    )
    
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.headers.get("content-type")
    )


# ===== ИНТЕГРАЦИОННЫЕ ENDPOINTS =====

@router.post("/api/gateway/comprehensive-analysis")
@limiter.limit("10/minute")
async def comprehensive_analysis(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """Комплексный анализ через все сервисы с input validation"""
    try:
        # Input validation
        if not request or not isinstance(request, dict):
            logger.warning(
                "Invalid request in comprehensive_analysis",
                extra={"request_type": type(request).__name__ if request else None}
            )
            raise HTTPException(
                status_code=400,
                detail="Request must be a valid dictionary"
            )
        
        requirements_text = request.get("requirements_text", "")
        context = request.get("context", {})
        
        # Validate requirements_text
        if not isinstance(requirements_text, str):
            logger.warning(
                "Invalid requirements_text type in comprehensive_analysis",
                extra={"requirements_text_type": type(requirements_text).__name__}
            )
            requirements_text = str(requirements_text) if requirements_text else ""
        
        # Validate requirements_text length (prevent DoS)
        max_requirements_length = 50000  # 50KB max
        if len(requirements_text) > max_requirements_length:
            logger.warning(
                "Requirements text too long in comprehensive_analysis",
                extra={"requirements_length": len(requirements_text), "max_length": max_requirements_length}
            )
            raise HTTPException(
                status_code=400,
                detail=f"Requirements text too long. Maximum length: {max_requirements_length} characters"
            )
        
        # Validate context
        if not isinstance(context, dict):
            logger.warning(
                "Invalid context type in comprehensive_analysis",
                extra={"context_type": type(context).__name__}
            )
            context = {}
        
        logger.debug(
            "Starting comprehensive analysis",
            extra={"requirements_length": len(requirements_text)}
        )
        
        results = {}
        errors = {}
        
        # Параллельные запросы к сервисам
        tasks = []
    
    # Анализ требований через AI Assistants
    tasks.append(
        proxy_service.proxy_request(
            service="assistants",
            endpoint="/api/assistants/architect/comprehensive-analysis",
            method="POST",
            data={
                "requirements_text": requirements_text,
                "context": context
            }
        )
    )
    
    # Анализ рисков через Risk Management API  
    tasks.append(
        proxy_service.proxy_request(
            service="risk",
            endpoint="/risk-assessment",
            method="POST",
            data={
                "requirements": requirements_text,
                "context": context
            }
        )
    )
    
    # Сбор метрик через Metrics API
    tasks.append(
        proxy_service.proxy_request(
            service="metrics",
            endpoint="/collect",
            method="POST",
            data={
                "event": "comprehensive_analysis",
                "requirements_length": len(requirements_text),
                "timestamp": datetime.now().isoformat()
            }
        )
    )
    
        try:
            # Optimized: Use asyncio.gather with timeout (best practice)
            responses = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=60.0  # Timeout для batch requests
            )
        except asyncio.TimeoutError:
            logger.error(
                "Timeout при batch запросах к сервисам",
                extra={
                    "tasks_count": len(tasks),
                    "timeout": 60.0
                }
            )
            # Возвращаем частичные результаты с ошибками
            responses = [{"error": "timeout", "status": 504} for _ in tasks]
        
        # Обработка ответов
        for i, response in enumerate(responses):
            try:
                if isinstance(response, Exception):
                    service_name = ["assistants", "risk", "metrics"][i]
                    errors[service_name] = str(response)
                    logger.warning(
                        f"Exception from service {service_name}",
                        extra={
                            "service_name": service_name,
                            "error_type": type(response).__name__
                        }
                    )
                elif hasattr(response, 'status_code'):
                    service_name = ["assistants", "risk", "metrics"][i]
                    if response.status_code == 200:
                        try:
                            results[service_name] = response.json()
                        except Exception as json_error:
                            logger.warning(
                                f"Failed to parse JSON from {service_name}",
                                extra={
                                    "service_name": service_name,
                                    "error_type": type(json_error).__name__
                                }
                            )
                            results[service_name] = response.text
                    else:
                        errors[service_name] = f"HTTP {response.status_code}"
                        logger.warning(
                            f"Non-200 status from {service_name}",
                            extra={
                                "service_name": service_name,
                                "status_code": response.status_code
                            }
                        )
            except Exception as process_error:
                logger.error(
                    f"Error processing response from service {i}: {process_error}",
                    extra={
                        "service_index": i,
                        "error_type": type(process_error).__name__
                    },
                    exc_info=True
                )
                errors[f"service_{i}"] = str(process_error)
    
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(
            f"Ошибка комплексного анализа: {e}",
            extra={"error_type": type(e).__name__},
            exc_info=True
        )
        errors["general"] = str(e)
    
    return {
        "status": "completed",
        "results": results,
        "errors": errors,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/api/gateway/status")
async def get_gateway_status():
    """Детальный статус всех компонентов"""
    
    health_responses = await health_checker.check_all_services()
    
    status_summary = {
        "gateway": "operational",
        "overall_health": "healthy",
        "services": {},
        "timestamp": datetime.now().isoformat()
    }
    
    healthy_services = 0
    total_services = len(SERVICES_CONFIG)
    
    for service_name, health in health_responses.items():
        status_summary["services"][service_name] = {
            "status": health.status,
            "response_time_ms": health.response_time_ms,
            "last_check": health.last_check.isoformat(),
            "error": health.error
        }
        
        if health.status == "healthy":
            healthy_services += 1
    
    # Определение общего состояния
    if healthy_services == total_services:
        status_summary["overall_health"] = "healthy"
    elif healthy_services > 0:
        status_summary["overall_health"] = "degraded"
    else:
        status_summary["overall_health"] = "down"
        status_summary["gateway"] = "degraded"
    
    return status_summary


# Подключение router к приложению
app.include_router(router, prefix="/")

# Экспорт router и приложения
__all__ = ["router", "app"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info",
        access_log=True
    )