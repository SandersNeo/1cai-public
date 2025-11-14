"""
API для управления рисками в 1C AI-экосистеме
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from src.utils.structured_logging import StructuredLogger

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, APIRouter
from pydantic import BaseModel, Field

logger = StructuredLogger(__name__).logger

# Pydantic модели
class RiskAssessmentRequest(BaseModel):
    """Запрос на оценку рисков"""
    requirements: str = Field(..., description="Требования проекта")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Контекст проекта")
    architecture: Optional[Dict[str, Any]] = Field(default=None, description="Архитектурное решение")

class RiskAssessmentResponse(BaseModel):
    """Ответ с оценкой рисков"""
    risk_level: str  # low, medium, high, critical
    risks: List[Dict[str, Any]]
    mitigation_strategies: List[str]
    confidence_score: float
    timestamp: datetime

class RiskRecord(BaseModel):
    """Запись риска"""
    id: str
    category: str  # technical, business, operational, security
    description: str
    impact: str  # low, medium, high, critical
    probability: float  # 0.0 - 1.0
    mitigation_plan: str
    owner: str
    status: str  # identified, assessing, mitigating, resolved
    created_at: datetime

# Глобальные данные (в реальности - в БД)
risk_database: Dict[str, RiskRecord] = {}

# Создание роутера
router = APIRouter()

# FastAPI приложение
app = FastAPI(
    title="Risk Management API",
    description="API для управления рисками проектов 1C",
    version="1.0.0"
)


@router.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "service": "Risk Management API",
        "version": "1.0.0",
        "status": "active",
        "description": "Управление рисками проектов 1C"
    }


@router.get("/health")
async def health_check():
    """Проверка состояния сервиса"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "service": "Risk Management API",
        "version": "1.0.0",
        "risks_tracked": len(risk_database)
    }


@router.post("/risk-assessment", response_model=RiskAssessmentResponse)
async def assess_risks(request: RiskAssessmentRequest):
    """Оценка рисков проекта"""
    try:
        logger.info(
            "Оценка рисков для проекта",
            extra={"requirements_length": len(request.requirements)}
        )
        
        # Простая логика анализа рисков (в реальности - ML модель)
        risk_factors = {
            "complexity_score": len(request.requirements.split()) / 100,  # Простая метрика
            "integration_points": len(request.context.get("integrations", [])) if request.context else 0,
            "data_migration": request.context.get("data_migration", False) if request.context else False,
            "legacy_systems": len(request.context.get("legacy_systems", [])) if request.context else 0
        }
        
        # Расчет общего уровня риска
        total_risk_score = (
            risk_factors["complexity_score"] * 0.4 +
            risk_factors["integration_points"] * 0.2 +
            (1.0 if risk_factors["data_migration"] else 0) * 0.3 +
            risk_factors["legacy_systems"] * 0.1
        )
        
        if total_risk_score < 0.3:
            risk_level = "low"
            confidence = 0.85
        elif total_risk_score < 0.6:
            risk_level = "medium"
            confidence = 0.75
        elif total_risk_score < 0.8:
            risk_level = "high"
            confidence = 0.65
        else:
            risk_level = "critical"
            confidence = 0.55
        
        # Генерация списка рисков
        risks = []
        if risk_factors["complexity_score"] > 0.5:
            risks.append({
                "category": "technical",
                "description": "Высокая сложность проекта",
                "impact": "medium",
                "probability": risk_factors["complexity_score"]
            })
        
        if risk_factors["integration_points"] > 3:
            risks.append({
                "category": "technical",
                "description": "Множественные точки интеграции",
                "impact": "high",
                "probability": min(risk_factors["integration_points"] * 0.2, 1.0)
            })
        
        if risk_factors["data_migration"]:
            risks.append({
                "category": "operational",
                "description": "Миграция данных",
                "impact": "high",
                "probability": 0.7
            })
        
        if risk_factors["legacy_systems"] > 2:
            risks.append({
                "category": "technical",
                "description": "Интеграция с устаревшими системами",
                "impact": "medium",
                "probability": 0.6
            })
        
        # Стратегии минимизации
        mitigation_strategies = []
        if risk_level in ["high", "critical"]:
            mitigation_strategies.extend([
                "Создать детальный план проекта с контрольными точками",
                "Провести пилотный проект для валидации подхода",
                "Увеличить время на тестирование и QA",
                "Привлечь экспертов по 1С для консультаций"
            ])
        
        if risk_factors["data_migration"]:
            mitigation_strategies.extend([
                "Создать план поэтапной миграции данных",
                "Подготовить план отката на случай критических ошибок"
            ])
        
        if risk_factors["legacy_systems"] > 2:
            mitigation_strategies.extend([
                "Провести аудит совместимости с устаревшими системами",
                "Создать план модернизации критичных компонентов"
            ])
        
        return RiskAssessmentResponse(
            risk_level=risk_level,
            risks=risks,
            mitigation_strategies=mitigation_strategies,
            confidence_score=confidence,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(
            "Ошибка при оценке рисков",
            extra={
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risks")
async def list_risks():
    """Список всех отслеживаемых рисков"""
    return {
        "risks": [
            {
                "id": risk.id,
                "category": risk.category,
                "description": risk.description,
                "impact": risk.impact,
                "probability": risk.probability,
                "status": risk.status,
                "created_at": risk.created_at.isoformat()
            }
            for risk in risk_database.values()
        ],
        "total_count": len(risk_database)
    }


@router.post("/risks")
async def create_risk(risk: RiskRecord):
    """Создание новой записи о риске"""
    try:
        risk_database[risk.id] = risk
        logger.info(
            "Создан риск",
            extra={"risk_id": risk.id}
        )
        
        return {
            "status": "success",
            "risk_id": risk.id,
            "message": "Риск успешно создан"
        }
        
    except Exception as e:
        logger.error(
            "Ошибка создания риска",
            extra={
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risks/{risk_id}")
async def get_risk(risk_id: str):
    """Получение информации о риске"""
    if risk_id not in risk_database:
        raise HTTPException(status_code=404, detail="Риск не найден")
    
    risk = risk_database[risk_id]
    return {
        "risk": {
            "id": risk.id,
            "category": risk.category,
            "description": risk.description,
            "impact": risk.impact,
            "probability": risk.probability,
            "mitigation_plan": risk.mitigation_plan,
            "owner": risk.owner,
            "status": risk.status,
            "created_at": risk.created_at.isoformat()
        }
    }


@router.put("/risks/{risk_id}/status")
async def update_risk_status(risk_id: str, status: str):
    """Обновление статуса риска"""
    if risk_id not in risk_database:
        raise HTTPException(status_code=404, detail="Риск не найден")
    
    risk_database[risk_id].status = status
    logger.info(
        "Обновлен статус риска",
        extra={
            "risk_id": risk_id,
            "status": status
        }
    )
    
    return {
        "status": "success",
        "risk_id": risk_id,
        "new_status": status
    }


@router.get("/metrics/overview")
async def risk_metrics_overview():
    """Обзор метрик рисков"""
    if not risk_database:
        return {
            "total_risks": 0,
            "by_impact": {},
            "by_status": {},
            "by_category": {}
        }
    
    # Подсчет по категориям
    by_category = {}
    for risk in risk_database.values():
        by_category[risk.category] = by_category.get(risk.category, 0) + 1
    
    # Подсчет по статусу
    by_status = {}
    for risk in risk_database.values():
        by_status[risk.status] = by_status.get(risk.status, 0) + 1
    
    # Подсчет по влиянию
    by_impact = {}
    for risk in risk_database.values():
        by_impact[risk.impact] = by_impact.get(risk.impact, 0) + 1
    
    return {
        "total_risks": len(risk_database),
        "by_impact": by_impact,
        "by_status": by_status,
        "by_category": by_category,
        "avg_probability": sum(r.probability for r in risk_database.values()) / len(risk_database)
    }


# Экспорт роутера
__all__ = ["router"]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)