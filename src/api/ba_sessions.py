# [NEXUS IDENTITY] ID: 4918963077187091487 | DATE: 2025-11-19

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    Body,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.security.auth import get_auth_service
from src.services.ba_session_manager import ba_session_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ba-sessions", tags=["BA Sessions"])


@router.websocket("/ws/{session_id}")
async def ba_session_ws(
    websocket: WebSocket,
    session_id: str,
    user_id: Optional[str] = Query(default=None),
    role: Optional[str] = Query(default="analyst"),
    topic: Optional[str] = Query(default=None),
    token: Optional[str] = Query(default=None),
):
    """
    WebSocket endpoint for collaborative BA sessions.

    Query params:
    - user_id: уникальный идентификатор пользователя (если нет — берём из токена)
    - role: роль участника (analyst, lead, reviewer, observer)
    - topic: произвольный контекст сессии
    """
    if token:
        try:
            principal = get_auth_service().decode_token(token)
            user_id = user_id or principal.user_id
            if principal.roles:
                role = principal.roles[0]
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to decode token for BA session: %s", exc)
    if not user_id:
        user_id = "anonymous"
    try:
        await ba_session_manager.join_session(
            session_id,
            websocket,
            user_id=user_id,
            role=role or "analyst",
            topic=topic,
        )
        await ba_session_manager.broadcast(
            session_id,
            {
                "type": "system",
                "event": "user_joined",
                "user_id": user_id,
                "role": role,
            },
            sender="system",
        )

        while True:
            data = await websocket.receive_json()
            message_type = data.get("type") or "message"
            if message_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue
            elif message_type == "leave":
                await websocket.close()
                break
            else:
                await ba_session_manager.broadcast(
                    session_id,
                    data,
                    sender=user_id,
                )
    except WebSocketDisconnect:
        pass
    except Exception as exc:  # pragma: no cover - network errors
        logger.error("BA session websocket error: %s", exc)
    finally:
        await ba_session_manager.leave_session(session_id, user_id)
        await ba_session_manager.broadcast(
            session_id,
            {"type": "system", "event": "user_left", "user_id": user_id},
            sender="system",
        )


@router.get("")
async def list_sessions():
    """List active BA sessions."""
    return {"sessions": ba_session_manager.list_sessions()}


@router.get("/{session_id}")
async def get_session(session_id: str):
    """Get state for a BA session."""
    state = ba_session_manager.get_session_state(session_id)
    if not state:
        return JSONResponse(status_code=404, content={"detail": "Session not found"})
    return state


# === BA-05: Traceability & Compliance API ===


class TraceabilityRequest(BaseModel):
    """Request для построения traceability matrix."""

    requirement_ids: List[str] = Body(..., description="Список ID требований")
    include_code: bool = Body(default=True, description="Включать связи с кодом")
    include_tests: bool = Body(default=True, description="Включать связи с тестами")
    include_incidents: bool = Body(
        default=True, description="Включать связи с инцидентами"
    )
    use_graph: bool = Body(
        default=True, description="Использовать Unified Change Graph"
    )


@router.post("/traceability/matrix")
async def build_traceability_matrix(request: TraceabilityRequest) -> Dict[str, Any]:
    """
    Построить traceability matrix для требований.

    Использует Unified Change Graph для полного traceability:
    requirements → code → tests → incidents.
    """
    try:
        from src.ai.agents.business_analyst_agent_extended import (
            BusinessAnalystAgentExtended,
        )

        agent = BusinessAnalystAgentExtended()

        # Преобразовать requirement_ids в формат requirements/test_cases
        # (для совместимости с существующим API)
        requirements = [
            {"id": req_id, "title": req_id} for req_id in request.requirement_ids
        ]
        test_cases = []  # Тесты будут найдены через граф

        result = await agent.build_traceability_and_risks(
            requirements,
            test_cases,
            use_graph=request.use_graph,
        )

        return result

    except Exception as e:
        logger.error(
            "Failed to build traceability matrix",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to build traceability matrix: {str(e)}"
        )


@router.post("/traceability/risk-register")
async def build_risk_register(
    requirement_ids: List[str] = Body(..., description="Список ID требований"),
    include_incidents: bool = Body(default=True, description="Учитывать инциденты"),
) -> Dict[str, Any]:
    """
    Построить Risk Register на основе traceability matrix.

    Риски определяются по:
    - Отсутствие тестов для требований
    - Наличие инцидентов, связанных с требованием
    - Отсутствие кода, реализующего требование
    """
    try:
        from src.ai.code_graph import InMemoryCodeGraphBackend
        from src.ai.agents.traceability_with_graph import TraceabilityWithGraph

        backend = InMemoryCodeGraphBackend()
        traceability = TraceabilityWithGraph(backend)

        result = await traceability.build_risk_register(
            requirement_ids,
            include_incidents=include_incidents,
        )

        return result

    except Exception as e:
        logger.error(
            "Failed to build risk register",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to build risk register: {str(e)}"
        )


@router.post("/traceability/full-report")
async def build_full_traceability_report(
    requirement_ids: List[str] = Body(..., description="Список ID требований"),
) -> Dict[str, Any]:
    """
    Построить полный отчёт traceability & compliance.

    Включает:
    - Traceability matrix
    - Risk register
    - Risk heatmap
    - Compliance status
    """
    try:
        from src.ai.code_graph import InMemoryCodeGraphBackend
        from src.ai.agents.traceability_with_graph import TraceabilityWithGraph

        backend = InMemoryCodeGraphBackend()
        traceability = TraceabilityWithGraph(backend)

        result = await traceability.build_full_traceability_report(requirement_ids)

        return result

    except Exception as e:
        logger.error(
            "Failed to build full traceability report",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to build full traceability report: {str(e)}",
        )


# === BA-04: Analytics & KPI Toolkit API ===


class KPIGenerationRequest(BaseModel):
    """Request для генерации KPI."""

    initiative_name: str = Body(..., description="Название инициативы/фичи")
    feature_id: Optional[str] = Body(
        default=None, description="ID фичи/требования для поиска в графе"
    )
    include_technical: bool = Body(default=True, description="Включать технические KPI")
    include_business: bool = Body(default=True, description="Включать бизнес KPI")
    use_graph: bool = Body(
        default=True, description="Использовать Unified Change Graph"
    )


@router.post("/analytics/kpi")
async def generate_kpis(request: KPIGenerationRequest) -> Dict[str, Any]:
    """
    Сгенерировать KPI для инициативы/фичи.

    Использует Unified Change Graph для автоматического построения KPI
    на основе реальных метрик (code coverage, test coverage, incident rate, etc.).
    """
    try:
        from src.ai.agents.business_analyst_agent_extended import (
            BusinessAnalystAgentExtended,
        )

        agent = BusinessAnalystAgentExtended()

        result = await agent.design_kpi_blueprint(
            initiative_name=request.initiative_name,
            feature_id=request.feature_id,
            use_graph=request.use_graph,
        )

        return result

    except Exception as e:
        logger.error(
            "Failed to generate KPIs",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to generate KPIs: {str(e)}"
        )


# === BA-03: Process & Journey Modelling API ===


class ProcessModelRequest(BaseModel):
    """Request для генерации модели процесса."""

    description: str = Body(..., description="Текстовое описание процесса")
    requirement_id: Optional[str] = Body(
        default=None, description="ID требования для связи с графом"
    )
    format: str = Body(
        default="mermaid", description="Формат вывода (mermaid, plantuml, json)"
    )
    use_graph: bool = Body(
        default=True, description="Использовать Unified Change Graph"
    )


class JourneyMapRequest(BaseModel):
    """Request для генерации Customer Journey Map."""

    journey_description: str = Body(
        ..., description="Текстовое описание customer journey"
    )
    stages: Optional[List[str]] = Body(
        default=None, description="Список стадий (опционально)"
    )
    format: str = Body(
        default="mermaid", description="Формат вывода (mermaid, plantuml, json)"
    )
    use_graph: bool = Body(
        default=True, description="Использовать Unified Change Graph"
    )


@router.post("/process/model")
async def generate_process_model(request: ProcessModelRequest) -> Dict[str, Any]:
    """
    Сгенерировать BPMN модель процесса.

    Использует Unified Change Graph для связи процесса с кодом, требованиями и тестами.
    """
    try:
        from src.ai.agents.business_analyst_agent_extended import (
            BusinessAnalystAgentExtended,
        )

        agent = BusinessAnalystAgentExtended()

        result = await agent.generate_process_model(
            description=request.description,
            requirement_id=request.requirement_id,
            format=request.format,
            use_graph=request.use_graph,
        )

        return result

    except Exception as e:
        logger.error(
            "Failed to generate process model",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to generate process model: {str(e)}"
        )


@router.post("/process/journey-map")
async def generate_journey_map(request: JourneyMapRequest) -> Dict[str, Any]:
    """
    Сгенерировать Customer Journey Map.

    Использует Unified Change Graph для поиска touchpoints (API endpoints, модули).
    """
    try:
        from src.ai.agents.business_analyst_agent_extended import (
            BusinessAnalystAgentExtended,
        )

        agent = BusinessAnalystAgentExtended()

        result = await agent.generate_journey_map(
            journey_description=request.journey_description,
            stages=request.stages,
            format=request.format,
            use_graph=request.use_graph,
        )

        return result

    except Exception as e:
        logger.error(
            "Failed to generate journey map",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to generate journey map: {str(e)}"
        )


@router.post("/process/validate")
async def validate_process(
    process_model: Dict[str, Any] = Body(
        ..., description="Модель процесса для валидации"
    ),
) -> Dict[str, Any]:
    """
    Валидировать модель процесса.

    Проверяет наличие владельцев, входов/выходов, измеримых результатов
    и связей с кодом/тестами через граф.
    """
    try:
        from src.ai.agents.business_analyst_agent_extended import (
            BusinessAnalystAgentExtended,
        )

        agent = BusinessAnalystAgentExtended()

        result = await agent.validate_process_model(process_model)

        return result

    except Exception as e:
        logger.error(
            "Failed to validate process",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to validate process: {str(e)}"
        )


# === BA-06: Integrations & Collaboration API ===


class SyncRequirementsRequest(BaseModel):
    """Request для синхронизации требований в Jira."""

    requirement_ids: List[str] = Body(..., description="Список ID требований")
    project_key: Optional[str] = Body(default=None, description="Ключ проекта Jira")
    issue_type: str = Body(
        default="Story", description="Тип задачи (Story, Task, Epic)"
    )
    use_graph: bool = Body(
        default=True, description="Использовать Unified Change Graph"
    )


class SyncBPMNRequest(BaseModel):
    """Request для синхронизации BPMN в Confluence."""

    process_model: Dict[str, Any] = Body(..., description="Модель процесса")
    space_key: Optional[str] = Body(
        default=None, description="Ключ пространства Confluence"
    )
    parent_page_id: Optional[str] = Body(
        default=None, description="ID родительской страницы"
    )
    use_graph: bool = Body(
        default=True, description="Использовать Unified Change Graph"
    )


@router.post("/integrations/sync-requirements-jira")
async def sync_requirements_to_jira(request: SyncRequirementsRequest) -> Dict[str, Any]:
    """
    Синхронизировать требования из графа в Jira.

    Создаёт задачи в Jira на основе требований, автоматически добавляя
    ссылки на код и тесты из Unified Change Graph.
    """
    try:
        from src.ai.agents.business_analyst_agent_extended import (
            BusinessAnalystAgentExtended,
        )

        agent = BusinessAnalystAgentExtended()

        result = await agent.sync_requirements_to_jira(
            requirement_ids=request.requirement_ids,
            project_key=request.project_key,
            issue_type=request.issue_type,
            use_graph=request.use_graph,
        )

        return result

    except Exception as e:
        logger.error(
            "Failed to sync requirements to Jira",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to sync requirements to Jira: {str(e)}"
        )


@router.post("/integrations/sync-bpmn-confluence")
async def sync_bpmn_to_confluence(request: SyncBPMNRequest) -> Dict[str, Any]:
    """
    Синхронизировать BPMN модель процесса в Confluence.

    Создаёт страницу в Confluence с BPMN диаграммой и автоматическими
    ссылками на код/тесты из Unified Change Graph.
    """
    try:
        from src.ai.agents.business_analyst_agent_extended import (
            BusinessAnalystAgentExtended,
        )

        agent = BusinessAnalystAgentExtended()

        result = await agent.sync_bpmn_to_confluence(
            process_model=request.process_model,
            space_key=request.space_key,
            parent_page_id=request.parent_page_id,
            use_graph=request.use_graph,
        )

        return result

    except Exception as e:
        logger.error(
            "Failed to sync BPMN to Confluence",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to sync BPMN to Confluence: {str(e)}"
        )


@router.post("/integrations/sync-kpi-confluence")
async def sync_kpi_to_confluence(
    kpi_report: Dict[str, Any] = Body(..., description="Отчёт KPI"),
    space_key: Optional[str] = Body(
        default=None, description="Ключ пространства Confluence"
    ),
    parent_page_id: Optional[str] = Body(
        default=None, description="ID родительской страницы"
    ),
    use_graph: bool = Body(
        default=True, description="Использовать Unified Change Graph"
    ),
) -> Dict[str, Any]:
    """
    Синхронизировать KPI отчёт в Confluence.
    """
    try:
        from src.ai.agents.business_analyst_agent_extended import (
            BusinessAnalystAgentExtended,
        )

        agent = BusinessAnalystAgentExtended()

        result = await agent.sync_kpi_to_confluence(
            kpi_report=kpi_report,
            space_key=space_key,
            parent_page_id=parent_page_id,
            use_graph=use_graph,
        )

        return result

    except Exception as e:
        logger.error(
            "Failed to sync KPI to Confluence",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to sync KPI to Confluence: {str(e)}"
        )


@router.post("/integrations/sync-traceability-confluence")
async def sync_traceability_to_confluence(
    traceability_report: Dict[str, Any] = Body(..., description="Отчёт traceability"),
    space_key: Optional[str] = Body(
        default=None, description="Ключ пространства Confluence"
    ),
    parent_page_id: Optional[str] = Body(
        default=None, description="ID родительской страницы"
    ),
    use_graph: bool = Body(
        default=True, description="Использовать Unified Change Graph"
    ),
) -> Dict[str, Any]:
    """
    Синхронизировать Traceability matrix в Confluence.
    """
    try:
        from src.ai.agents.business_analyst_agent_extended import (
            BusinessAnalystAgentExtended,
        )

        agent = BusinessAnalystAgentExtended()

        result = await agent.sync_traceability_to_confluence(
            traceability_report=traceability_report,
            space_key=space_key,
            parent_page_id=parent_page_id,
            use_graph=use_graph,
        )

        return result

    except Exception as e:
        logger.error(
            "Failed to sync traceability to Confluence",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync traceability to Confluence: {str(e)}",
        )


# === BA-07: Documentation & Enablement API ===


class EnablementPlanRequest(BaseModel):
    """Request для генерации плана enablement-материалов."""

    feature_name: str = Body(..., description="Название фичи")
    audience: str = Body(default="BA+Dev+QA", description="Целевая аудитория")
    include_examples: bool = Body(default=True, description="Включать примеры из графа")
    use_graph: bool = Body(
        default=True, description="Использовать Unified Change Graph"
    )


class GuideRequest(BaseModel):
    """Request для генерации гайда."""

    topic: str = Body(..., description="Тема гайда")
    format: str = Body(
        default="markdown", description="Формат вывода (markdown, confluence, html)"
    )
    include_code_examples: bool = Body(
        default=True, description="Включать примеры кода из графа"
    )
    use_graph: bool = Body(
        default=True, description="Использовать Unified Change Graph"
    )


class PresentationRequest(BaseModel):
    """Request для генерации outline презентации."""

    topic: str = Body(..., description="Тема презентации")
    audience: str = Body(
        default="stakeholders",
        description="Аудитория (stakeholders, technical, executive)",
    )
    duration_minutes: int = Body(default=30, description="Длительность в минутах")
    use_graph: bool = Body(
        default=True, description="Использовать Unified Change Graph"
    )


@router.post("/enablement/plan")
async def generate_enablement_plan(request: EnablementPlanRequest) -> Dict[str, Any]:
    """
    Сгенерировать план enablement-материалов.

    Использует Unified Change Graph для автоматического поиска примеров
    и связанных артефактов.
    """
    try:
        from src.ai.agents.business_analyst_agent_extended import (
            BusinessAnalystAgentExtended,
        )

        agent = BusinessAnalystAgentExtended()

        result = await agent.build_enablement_plan(
            feature_name=request.feature_name,
            audience=request.audience,
            include_examples=request.include_examples,
            use_graph=request.use_graph,
        )

        return result

    except Exception as e:
        logger.error(
            "Failed to generate enablement plan",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to generate enablement plan: {str(e)}"
        )


@router.post("/enablement/guide")
async def generate_guide(request: GuideRequest) -> Dict[str, Any]:
    """
    Сгенерировать гайд по теме с примерами из графа.
    """
    try:
        from src.ai.agents.business_analyst_agent_extended import (
            BusinessAnalystAgentExtended,
        )

        agent = BusinessAnalystAgentExtended()

        result = await agent.generate_guide(
            topic=request.topic,
            format=request.format,
            include_code_examples=request.include_code_examples,
            use_graph=request.use_graph,
        )

        return result

    except Exception as e:
        logger.error(
            "Failed to generate guide",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to generate guide: {str(e)}"
        )


@router.post("/enablement/presentation")
async def generate_presentation(request: PresentationRequest) -> Dict[str, Any]:
    """
    Сгенерировать outline презентации.
    """
    try:
        from src.ai.agents.business_analyst_agent_extended import (
            BusinessAnalystAgentExtended,
        )

        agent = BusinessAnalystAgentExtended()

        result = await agent.generate_presentation_outline(
            topic=request.topic,
            audience=request.audience,
            duration_minutes=request.duration_minutes,
            use_graph=request.use_graph,
        )

        return result

    except Exception as e:
        logger.error(
            "Failed to generate presentation",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to generate presentation: {str(e)}"
        )


@router.post("/enablement/onboarding-checklist")
async def generate_onboarding_checklist(
    role: str = Body(default="BA", description="Роль (BA, Dev, QA, Product)"),
    include_practical_tasks: bool = Body(
        default=True, description="Включать практические задачи из графа"
    ),
    use_graph: bool = Body(
        default=True, description="Использовать Unified Change Graph"
    ),
) -> Dict[str, Any]:
    """
    Сгенерировать onboarding чек-лист для роли.
    """
    try:
        from src.ai.agents.business_analyst_agent_extended import (
            BusinessAnalystAgentExtended,
        )

        agent = BusinessAnalystAgentExtended()

        result = await agent.generate_onboarding_checklist(
            role=role,
            include_practical_tasks=include_practical_tasks,
            use_graph=use_graph,
        )

        return result

    except Exception as e:
        logger.error(
            "Failed to generate onboarding checklist",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to generate onboarding checklist: {str(e)}"
        )
