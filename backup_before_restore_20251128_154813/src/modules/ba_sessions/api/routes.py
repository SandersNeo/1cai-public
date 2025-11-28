"""
BA Sessions API Routes
"""
from typing import Any, Dict, List, Optional

from fastapi import (APIRouter, Body, HTTPException, Query, WebSocket,
                     WebSocketDisconnect)
from fastapi.responses import JSONResponse

from src.infrastructure.logging.structured_logging import StructuredLogger
from src.modules.ba_sessions.domain.models import (EnablementPlanRequest,
                                                   GuideRequest,
                                                   JourneyMapRequest,
                                                   KPIGenerationRequest,
                                                   PresentationRequest,
                                                   ProcessModelRequest,
                                                   SyncBPMNRequest,
                                                   SyncRequirementsRequest,
                                                   TraceabilityRequest)
from src.modules.ba_sessions.services.analytics_service import AnalyticsService
from src.modules.ba_sessions.services.documentation_service import \
    DocumentationService
from src.modules.ba_sessions.services.integration_service import \
    IntegrationService
from src.modules.ba_sessions.services.modeling_service import ModelingService
from src.modules.ba_sessions.services.session_service import SessionService
from src.modules.ba_sessions.services.traceability_service import \
    TraceabilityService
from src.security.auth import get_auth_service

logger = StructuredLogger(__name__).logger

router = APIRouter(tags=["BA Sessions"])

# Initialize services
session_service = SessionService()
traceability_service = TraceabilityService()
analytics_service = AnalyticsService()
modeling_service = ModelingService()
integration_service = IntegrationService()
documentation_service = DocumentationService()


# === Sessions ===


@router.websocket("/ws/{session_id}")
async def ba_session_ws(
    websocket: WebSocket,
    session_id: str,
    user_id: Optional[str] = Query(default=None),
    role: Optional[str] = Query(default="analyst"),
    topic: Optional[str] = Query(default=None),
    token: Optional[str] = Query(default=None),
):
    """WebSocket endpoint for collaborative BA sessions."""
    if token:
        try:
