"""
API для сбора и анализа метрик 1C AI-экосистемы
Версия: 2.1.0

Улучшения:
- Input validation
- Structured logging
- Улучшена обработка ошибок
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import logging

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, APIRouter, Query
from pydantic import BaseModel, Field, field_validator
import time
from src.utils.structured_logging import StructuredLogger

# Создание router для API endpoints
router = APIRouter()

# Настройка логирования
logger = StructuredLogger(__name__).logger

# Pydantic модели
class MetricRecord(BaseModel):
    """Запись метрики"""
    metric_type: str = Field(..., min_length=1, max_length=200, description="Тип метрики")
    service_name: str = Field(..., min_length=1, max_length=100, description="Название сервиса")
    value: float = Field(..., description="Значение метрики")
    timestamp: datetime = Field(default_factory=datetime.now, description="Время записи")
    labels: Optional[Dict[str, str]] = Field(default=None, description="Дополнительные метки")
    unit: Optional[str] = Field(None, max_length=20, description="Единица измерения")
    
    @field_validator('metric_type', 'service_name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Sanitize name to prevent injection"""
        import re
        # Allow alphanumeric, underscore, dash, dot
        if not re.match(r'^[a-zA-Z0-9_.-]+$', v):
            raise ValueError("Invalid characters in name")
        return v.strip()

class MetricCollectionRequest(BaseModel):
    """Запрос на сбор метрики"""
    event: str = Field(..., description="Событие или действие")
    service: str = Field(..., description="Сервис")
    metrics: Dict[str, Union[float, int, str]] = Field(..., description="Метрики")
    timestamp: Optional[datetime] = Field(default=None, description="Время события")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Контекст")

class AggregatedMetrics(BaseModel):
    """Агрегированные метрики"""
    metric_name: str
    avg_value: float
    min_value: float
    max_value: float
    count: int
    unit: Optional[str] = None
    time_range: Dict[str, datetime]

# Глобальное хранилище метрик (в реальности - БД или TSDB)
metrics_storage: List[MetricRecord] = []
performance_metrics: Dict[str, List[float]] = {}

# FastAPI приложение
app = FastAPI(
    title="Metrics API",
    description="API для сбора и анализа метрик 1C AI-экосистемы",
    version="1.0.0"
)


@router.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "service": "Metrics API",
        "version": "1.0.0",
        "status": "active",
        "description": "Сбор и анализ метрик 1C AI-экосистемы"
    }


@router.get("/health")
async def health_check():
    """Проверка состояния сервиса"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "service": "Metrics API",
        "version": "1.0.0",
        "metrics_collected": len(metrics_storage),
        "services_monitored": len(set(m.service_name for m in metrics_storage))
    }


@router.post("/collect")
async def collect_metrics(request: MetricCollectionRequest):
    """
    Сбор метрик от различных сервисов
    
    Security: Input validation и sanitization
    """
    try:
        # Input validation
        if not request.event or len(request.event) > 200:
            raise HTTPException(status_code=400, detail="Invalid event name")
        if not request.service or len(request.service) > 100:
            raise HTTPException(status_code=400, detail="Invalid service name")
        if not request.metrics or len(request.metrics) > 100:
            raise HTTPException(status_code=400, detail="Too many metrics (max 100)")
        
        timestamp = request.timestamp or datetime.now()
        
        collected_count = 0
        
        # Записываем каждую метрику
        for metric_name, value in request.metrics.items():
            # Validate metric name
            if not metric_name or len(metric_name) > 200:
                logger.warning(
                    f"Invalid metric name skipped: {metric_name}",
                    extra={"service": request.service, "event": request.event}
                )
                continue
            
            try:
                metric = MetricRecord(
                    metric_type=f"{request.event}.{metric_name}",
                    service_name=request.service,
                    value=float(value) if isinstance(value, (int, float, str)) else 0.0,
                    timestamp=timestamp,
                    labels={
                        "event": request.event,
                        "service": request.service,
                        **(request.context or {})
                    }
                )
                
                metrics_storage.append(metric)
                collected_count += 1
                
                # Сохраняем для быстрого доступа к performance метрикам
                if metric_name in ["response_time", "processing_time", "latency"]:
                    if metric_name not in performance_metrics:
                        performance_metrics[metric_name] = []
                    performance_metrics[metric_name].append(metric.value)
            except Exception as e:
                logger.warning(
                    f"Failed to collect metric {metric_name}: {e}",
                    extra={
                        "service": request.service,
                        "event": request.event,
                        "metric_name": metric_name,
                        "error_type": type(e).__name__
                    }
                )
                continue
        
        logger.info(
            f"Collected {collected_count} metrics from service {request.service}",
            extra={
                "service": request.service,
                "event": request.event,
                "collected_count": collected_count,
                "total_metrics": len(request.metrics)
            }
        )
        
        return {
            "status": "success",
            "collected_metrics": collected_count,
            "service": request.service,
            "timestamp": timestamp.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error collecting metrics: {e}",
            extra={
                "service": request.service if hasattr(request, 'service') else None,
                "event": request.event if hasattr(request, 'event') else None,
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Failed to collect metrics: {str(e)}")


@router.get("/metrics")
async def get_metrics(
    service: Optional[str] = None,
    metric_type: Optional[str] = None,
    hours_back: int = 24,
    limit: int = 1000
):
    """Получение метрик с фильтрацией"""
    try:
        # Фильтрация по времени
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        filtered_metrics = [
            m for m in metrics_storage 
            if m.timestamp >= cutoff_time
        ]
        
        # Фильтрация по сервису
        if service:
            filtered_metrics = [
                m for m in filtered_metrics 
                if m.service_name == service
            ]
        
        # Фильтрация по типу метрики
        if metric_type:
            filtered_metrics = [
                m for m in filtered_metrics 
                if metric_type in m.metric_type
            ]
        
        # Ограничение результатов
        filtered_metrics = filtered_metrics[-limit:]
        
        return {
            "metrics": [
                {
                    "metric_type": m.metric_type,
                    "service_name": m.service_name,
                    "value": m.value,
                    "timestamp": m.timestamp.isoformat(),
                    "labels": m.labels,
                    "unit": m.unit
                }
                for m in filtered_metrics
            ],
            "total_count": len(filtered_metrics),
            "filters": {
                "service": service,
                "metric_type": metric_type,
                "hours_back": hours_back,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(
            "Ошибка получения метрик",
            extra={
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/{service_name}")
async def get_performance_metrics(service_name: str, hours_back: int = 1):
    """Получение performance метрик для сервиса"""
    try:
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        service_metrics = [
            m for m in metrics_storage
            if m.service_name == service_name and m.timestamp >= cutoff_time
        ]
        
        # Группировка по типу метрики
        metrics_by_type = {}
        for metric in service_metrics:
            if metric.metric_type not in metrics_by_type:
                metrics_by_type[metric.metric_type] = []
            metrics_by_type[metric.metric_type].append(metric.value)
        
        # Подсчет статистики
        performance_summary = {}
        for metric_type, values in metrics_by_type.items():
            if values:
                performance_summary[metric_type] = {
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values),
                    "latest": values[-1] if values else None
                }
        
        return {
            "service": service_name,
            "hours_back": hours_back,
            "metrics_summary": performance_summary,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(
            "Ошибка получения performance метрик",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "service_name": service_name
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/overview")
async def get_dashboard_overview():
    """Обзорная информация для dashboard"""
    try:
        now = datetime.now()
        last_hour = now - timedelta(hours=1)
        last_day = now - timedelta(days=1)
        
        # Метрики за последний час
        recent_metrics = [m for m in metrics_storage if m.timestamp >= last_hour]
        
        # Метрики за последний день
        daily_metrics = [m for m in metrics_storage if m.timestamp >= last_day]
        
        # Активные сервисы
        active_services = set(m.service_name for m in recent_metrics)
        
        # Топ метрик по количеству
        metric_counts = {}
        for metric in daily_metrics:
            metric_counts[metric.metric_type] = metric_counts.get(metric.metric_type, 0) + 1
        
        top_metrics = sorted(metric_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Средние значения performance метрик за последний час
        perf_metrics = {}
        for metric in recent_metrics:
            if any(keyword in metric.metric_type for keyword in ["response_time", "latency", "processing_time"]):
                if metric.metric_type not in perf_metrics:
                    perf_metrics[metric.metric_type] = []
                perf_metrics[metric.metric_type].append(metric.value)
        
        avg_performance = {}
        for metric_type, values in perf_metrics.items():
            if values:
                avg_performance[metric_type] = {
                    "average": sum(values) / len(values),
                    "count": len(values)
                }
        
        return {
            "overview": {
                "total_metrics_last_hour": len(recent_metrics),
                "total_metrics_last_day": len(daily_metrics),
                "active_services": len(active_services),
                "unique_services": len(set(m.service_name for m in metrics_storage))
            },
            "top_metrics": [{"metric": metric, "count": count} for metric, count in top_metrics],
            "performance_averages": avg_performance,
            "active_services_list": list(active_services),
            "timestamp": now.isoformat()
        }
        
    except Exception as e:
        logger.error(
            "Ошибка создания dashboard overview",
            extra={
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_alerts():
    """Получение активных алертов на основе метрик"""
    try:
        alerts = []
        now = datetime.now()
        last_5_min = now - timedelta(minutes=5)
        
        # Проверяем response time алерты
        recent_perf_metrics = [
            m for m in metrics_storage
            if m.timestamp >= last_5_min and any(
                keyword in m.metric_type for keyword in ["response_time", "latency"]
            )
        ]
        
        # Группировка по сервису
        service_response_times = {}
        for metric in recent_perf_metrics:
            service = metric.service_name
            if service not in service_response_times:
                service_response_times[service] = []
            service_response_times[service].append(metric.value)
        
        # Проверка на превышение порогов
        for service, times in service_response_times.items():
            if times and sum(times) / len(times) > 5.0:  # Среднее время ответа > 5 секунд
                alerts.append({
                    "service": service,
                    "type": "high_response_time",
                    "severity": "warning",
                    "message": f"Высокое время ответа сервиса {service}: {sum(times) / len(times):.2f}s",
                    "timestamp": now.isoformat()
                })
        
        return {
            "alerts": alerts,
            "total_alerts": len(alerts),
            "timestamp": now.isoformat()
        }
        
    except Exception as e:
        logger.error(
            "Ошибка получения алертов",
            extra={
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/metrics")
async def clear_old_metrics(days_back: int = 30):
    """Очистка старых метрик"""
    try:
        cutoff_time = datetime.now() - timedelta(days=days_back)
        original_count = len(metrics_storage)
        
        # Удаляем старые метрики
        global metrics_storage
        metrics_storage = [m for m in metrics_storage if m.timestamp >= cutoff_time]
        
        removed_count = original_count - len(metrics_storage)
        
        logger.info(
            "Удалено старых метрик",
            extra={"removed_count": removed_count}
        )
        
        return {
            "status": "success",
            "removed_metrics": removed_count,
            "remaining_metrics": len(metrics_storage),
            "cutoff_date": cutoff_time.isoformat()
        }
        
    except Exception as e:
        logger.error(
            "Ошибка очистки метрик",
            extra={
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats():
    """Общая статистика по метрикам"""
    try:
        if not metrics_storage:
            return {
                "total_metrics": 0,
                "services": [],
                "metric_types": [],
                "date_range": None
            }
        
        services = list(set(m.service_name for m in metrics_storage))
        metric_types = list(set(m.metric_type for m in metrics_storage))
        
        earliest = min(m.timestamp for m in metrics_storage)
        latest = max(m.timestamp for m in metrics_storage)
        
        return {
            "total_metrics": len(metrics_storage),
            "services": services,
            "metric_types": metric_types,
            "date_range": {
                "earliest": earliest.isoformat(),
                "latest": latest.isoformat()
            },
            "storage_info": {
                "memory_usage_estimate": f"{len(metrics_storage) * 0.1:.2f} KB"
            }
        }
        
    except Exception as e:
        logger.error(
            "Ошибка получения статистики",
            extra={
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


# Экспорт router для подключения к основному приложению
__all__ = ["router"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)