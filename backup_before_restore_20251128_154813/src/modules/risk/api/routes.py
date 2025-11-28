from datetime import datetime

from fastapi import APIRouter, HTTPException

from src.modules.risk.domain.models import (RiskAssessmentRequest,
                                            RiskAssessmentResponse, RiskRecord)
from src.modules.risk.services.risk_service import RiskService

router = APIRouter(tags=["Risk Management"])


def get_risk_service() -> RiskService:
    return RiskService()


@router.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Risk Management API",
        "version": "1.0.0",
        "status": "active",
        "description": "1C project risk management",
    }


@router.get("/health")
async def health_check():
    """Health check."""
    service = get_risk_service()
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "service": "Risk Management API",
        "version": "1.0.0",
        "risks_tracked": service.db.count(),
    }


@router.post("/risk-assessment", response_model=RiskAssessmentResponse)
async def assess_risks(request: RiskAssessmentRequest):
    """Assess project risks."""
    try:
