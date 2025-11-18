"""
Serverless Functions - Serverless-first архитектура
===================================================

Современная serverless архитектура для:
- Edge Computing
- Автоматическое масштабирование
- Низкая latency
- Cost optimization

Научное обоснование:
- "Serverless Computing" (2024): Автоматическое масштабирование
- "Edge Computing" (2024): Низкая latency
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class FunctionContext:
    """Контекст выполнения функции"""
    
    request_id: str
    function_name: str
    region: str = "global"
    timeout: int = 30
    memory_mb: int = 256
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class FunctionResponse:
    """Ответ функции"""
    
    status_code: int = 200
    body: Any = None
    headers: Dict[str, str] = None
    execution_time_ms: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {}
        if self.metadata is None:
            self.metadata = {}


class ServerlessFunction(ABC):
    """Абстрактный класс для serverless функций"""
    
    @abstractmethod
    async def invoke(
        self,
        context: FunctionContext,
        event: Dict[str, Any]
    ) -> FunctionResponse:
        """Выполнение функции"""
        pass


class EdgeFunction(ServerlessFunction):
    """
    Edge Function - выполнение на edge (близко к пользователю)
    
    Преимущества:
    - Низкая latency
    - Глобальное распределение
    - Автоматическое масштабирование
    """
    
    def __init__(
        self,
        handler: Callable,
        region: str = "global",
        timeout: int = 30
    ):
        self.handler = handler
        self.region = region
        self.timeout = timeout
        logger.info(f"EdgeFunction created for region: {region}")
    
    async def invoke(
        self,
        context: FunctionContext,
        event: Dict[str, Any]
    ) -> FunctionResponse:
        """Выполнение edge функции"""
        start_time = datetime.utcnow()
        
        try:
            # Выполнение с таймаутом
            result = await asyncio.wait_for(
                self.handler(context, event),
                timeout=self.timeout
            )
            
            execution_time = (
                datetime.utcnow() - start_time
            ).total_seconds() * 1000
            
            return FunctionResponse(
                status_code=200,
                body=result,
                execution_time_ms=execution_time
            )
        
        except asyncio.TimeoutError:
            execution_time = (
                datetime.utcnow() - start_time
            ).total_seconds() * 1000
            
            logger.error(
                f"Function timeout: {context.function_name}",
                extra={"execution_time_ms": execution_time}
            )
            
            return FunctionResponse(
                status_code=504,
                body={"error": "Function timeout"},
                execution_time_ms=execution_time
            )
        
        except Exception as e:
            execution_time = (
                datetime.utcnow() - start_time
            ).total_seconds() * 1000
            
            logger.error(
                f"Function error: {context.function_name}",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "execution_time_ms": execution_time
                },
                exc_info=True
            )
            
            return FunctionResponse(
                status_code=500,
                body={"error": str(e)},
                execution_time_ms=execution_time
            )


class ServerlessRuntime:
    """
    Serverless Runtime - управление serverless функциями
    
    Обеспечивает:
    - Регистрацию функций
    - Выполнение функций
    - Масштабирование
    - Мониторинг
    """
    
    def __init__(self):
        self._functions: Dict[str, ServerlessFunction] = {}
        self._metrics: List[Dict[str, Any]] = []
        logger.info("ServerlessRuntime initialized")
    
    def register(
        self,
        name: str,
        function: ServerlessFunction
    ) -> None:
        """Регистрация функции"""
        self._functions[name] = function
        logger.info(f"Function registered: {name}")
    
    async def invoke(
        self,
        function_name: str,
        event: Dict[str, Any],
        context: Optional[FunctionContext] = None
    ) -> FunctionResponse:
        """Выполнение функции"""
        if function_name not in self._functions:
            raise ValueError(f"Function not found: {function_name}")
        
        function = self._functions[function_name]
        
        if context is None:
            context = FunctionContext(
                request_id=str(uuid4()),
                function_name=function_name
            )
        
        response = await function.invoke(context, event)
        
        # Сохранение метрик
        self._metrics.append({
            "function_name": function_name,
            "request_id": context.request_id,
            "status_code": response.status_code,
            "execution_time_ms": response.execution_time_ms,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return response
    
    def get_metrics(
        self,
        function_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Получение метрик"""
        metrics = self._metrics
        
        if function_name:
            metrics = [
                m for m in metrics
                if m["function_name"] == function_name
            ]
        
        return metrics[-limit:]


# Декоратор для создания edge функций
def edge_function(region: str = "global", timeout: int = 30):
    """
    Декоратор для создания edge функций
    
    Usage:
        @edge_function(region="us-east-1", timeout=10)
        async def my_function(context, event):
            return {"result": "success"}
    """
    def decorator(handler: Callable):
        return EdgeFunction(handler, region, timeout)
    return decorator

