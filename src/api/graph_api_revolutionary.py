"""
Graph API with Revolutionary Components Integration
==================================================

Добавление endpoints для революционных компонентов:
- Event-Driven Architecture
- Self-Evolving AI
- Self-Healing Code
- Distributed Network
- Monitoring & Analytics
"""

from fastapi import APIRouter, HTTPException, Body, Query
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
import logging

from src.api.graph_api import app
from src.ai.orchestrator_revolutionary import RevolutionaryAIOrchestrator
from src.monitoring.revolutionary_metrics import RevolutionaryMetricsCollector
from src.analytics.revolutionary_analytics import RevolutionaryAnalytics
from src.config.revolutionary_config import RevolutionaryConfigManager

logger = logging.getLogger(__name__)

# Router для революционных endpoints
revolutionary_router = APIRouter(prefix="/api/revolutionary", tags=["revolutionary"])

# Глобальные экземпляры
orchestrator: Optional[RevolutionaryAIOrchestrator] = None
metrics_collector: Optional[RevolutionaryMetricsCollector] = None
analytics: Optional[RevolutionaryAnalytics] = None
config_manager: Optional[RevolutionaryConfigManager] = None


def init_revolutionary_components():
    """Инициализация революционных компонентов"""
    global orchestrator, metrics_collector, analytics, config_manager
    
    try:
        orchestrator = RevolutionaryAIOrchestrator()
        metrics_collector = RevolutionaryMetricsCollector()
        analytics = RevolutionaryAnalytics()
        config_manager = RevolutionaryConfigManager()
        
        logger.info("Revolutionary components initialized")
    except Exception as e:
        logger.error(f"Failed to initialize revolutionary components: {e}")
        raise


# Models
class EvolutionRequest(BaseModel):
    """Запрос на эволюцию AI"""
    force: bool = Field(default=False, description="Принудительная эволюция")


class HealingRequest(BaseModel):
    """Запрос на самоисправление"""
    error_message: str = Field(..., description="Сообщение об ошибке")
    context: Dict[str, Any] = Field(default_factory=dict, description="Контекст ошибки")


class NetworkTaskRequest(BaseModel):
    """Запрос на задачу в сети агентов"""
    description: str = Field(..., description="Описание задачи")
    agent_roles: List[str] = Field(default_factory=list, description="Роли агентов")


# Endpoints

@revolutionary_router.post("/evolve")
async def evolve_ai(request: EvolutionRequest = Body(...)) -> Dict[str, Any]:
    """
    Запуск эволюции AI системы
    
    Self-Evolving AI автоматически улучшает систему на основе метрик
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        result = await orchestrator.evolve()
        return {
            "status": "success",
            "evolution": result
        }
    except Exception as e:
        logger.error(f"Evolution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@revolutionary_router.post("/heal")
async def heal_error(request: HealingRequest = Body(...)) -> Dict[str, Any]:
    """
    Автоматическое исправление ошибки
    
    Self-Healing Code пытается автоматически исправить ошибку
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        error = Exception(request.error_message)
        fix = await orchestrator.healing_code.handle_error(
            error,
            context=request.context
        )
        
        if fix:
            return {
                "status": "success",
                "fix": {
                    "id": fix.id,
                    "description": fix.description,
                    "confidence": fix.confidence
                }
            }
        else:
            return {
                "status": "no_fix",
                "message": "No automatic fix available"
            }
    except Exception as e:
        logger.error(f"Healing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@revolutionary_router.post("/network/task")
async def submit_network_task(request: NetworkTaskRequest = Body(...)) -> Dict[str, Any]:
    """
    Отправка задачи в Distributed Agent Network
    
    Координация агентов для решения задачи
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        result = await orchestrator.coordinate_agents(
            request.description,
            request.agent_roles
        )
        return {
            "status": "success",
            "task": result
        }
    except Exception as e:
        logger.error(f"Network task failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@revolutionary_router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """
    Получение метрик всех революционных компонентов
    
    Возвращает метрики:
    - Event-Driven Architecture
    - Self-Evolving AI
    - Self-Healing Code
    - Distributed Network
    """
    if not metrics_collector:
        raise HTTPException(status_code=503, detail="Metrics collector not initialized")
    
    try:
        all_metrics = metrics_collector.get_all_metrics()
        summary = metrics_collector.get_summary()
        
        return {
            "status": "success",
            "metrics": {
                name: metrics.to_dict()
                for name, metrics in all_metrics.items()
            },
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@revolutionary_router.get("/analytics/report")
async def get_analytics_report(
    period_days: int = Query(default=7, ge=1, le=90),
    components: Optional[List[str]] = Query(default=None)
) -> Dict[str, Any]:
    """
    Получение аналитического отчета
    
    Анализ производительности и ROI компонентов
    """
    if not analytics:
        raise HTTPException(status_code=503, detail="Analytics not initialized")
    
    try:
        report = analytics.generate_report(
            title="Revolutionary Components Report",
            period_days=period_days,
            components=components
        )
        
        return {
            "status": "success",
            "report": report.to_dict()
        }
    except Exception as e:
        logger.error(f"Failed to generate report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@revolutionary_router.get("/config")
async def get_config(component: Optional[str] = Query(default=None)) -> Dict[str, Any]:
    """
    Получение конфигурации компонентов
    """
    if not config_manager:
        raise HTTPException(status_code=503, detail="Config manager not initialized")
    
    try:
        if component:
            config = config_manager.get_component_config(component)
            if not config:
                raise HTTPException(status_code=404, detail=f"Component not found: {component}")
            return {
                "status": "success",
                "component": component,
                "config": {
                    "enabled": config.enabled,
                    "settings": config.settings
                }
            }
        else:
            # Все компоненты
            all_configs = {}
            for comp_name in ["event_driven", "self_evolving", "self_healing", "distributed_network"]:
                comp_config = config_manager.get_component_config(comp_name)
                if comp_config:
                    all_configs[comp_name] = {
                        "enabled": comp_config.enabled,
                        "settings": comp_config.settings
                    }
            
            return {
                "status": "success",
                "configs": all_configs
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@revolutionary_router.put("/config")
async def update_config(
    component: str = Query(..., description="Имя компонента"),
    settings: Dict[str, Any] = Body(..., description="Новые настройки")
) -> Dict[str, Any]:
    """
    Обновление конфигурации компонента
    """
    if not config_manager:
        raise HTTPException(status_code=503, detail="Config manager not initialized")
    
    try:
        config_manager.update_config(component, settings)
        return {
            "status": "success",
            "message": f"Config updated for {component}"
        }
    except Exception as e:
        logger.error(f"Failed to update config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Startup event
@app.on_event("startup")
async def startup_revolutionary():
    """Инициализация при старте приложения"""
    try:
        init_revolutionary_components()
        if orchestrator:
            await orchestrator.start()
    except Exception as e:
        logger.error(f"Failed to start revolutionary components: {e}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_revolutionary():
    """Остановка при завершении приложения"""
    try:
        if orchestrator:
            await orchestrator.stop()
    except Exception as e:
        logger.error(f"Failed to stop revolutionary components: {e}")


# Подключение router к основному app
app.include_router(revolutionary_router)

