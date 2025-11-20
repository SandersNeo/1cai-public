# [NEXUS IDENTITY] ID: 2215733575927587553 | DATE: 2025-11-19

"""
FastAPI endpoints для AI-ассистентов
Предоставляет REST API для взаимодействия с различными AI-ассистентами
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field

from ..ai_assistants.architect_assistant import ArchitectAssistant
from ..config import settings
from ..middleware.rate_limiter import limiter
from src.utils.structured_logging import StructuredLogger


# Pydantic модели для запросов и ответов
class ChatRequest(BaseModel):
    """Запрос для чата с ассистентом"""

    query: str = Field(..., max_length=5000, description="Сообщение пользователя")
    context: Optional[Dict[str, Any]] = Field(
        default=None, description="Дополнительный контекст"
    )
    conversation_id: Optional[str] = Field(
        default=None, max_length=100, description="ID диалога"
    )


class ChatResponse(BaseModel):
    """Ответ от ассистента"""

    message_id: str
    content: str
    role: str
    timestamp: datetime
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float
    conversation_id: str


class AnalyzeRequirementsRequest(BaseModel):
    """Запрос на анализ требований"""

    requirements_text: str = Field(
        ..., max_length=10000, description="Текст с требованиями"
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None, description="Контекст проекта"
    )


class GenerateDiagramRequest(BaseModel):
    """Запрос на генерацию диаграммы"""

    architecture_proposal: Dict[str, Any] = Field(
        ..., description="Предложение архитектуры"
    )
    diagram_type: str = Field(
        default="flowchart", max_length=50, description="Тип диаграммы"
    )
    diagram_requirements: Optional[Dict[str, Any]] = Field(
        default=None, description="Требования к диаграмме"
    )


class ComprehensiveAnalysisRequest(BaseModel):
    """Запрос на комплексный анализ"""

    requirements_text: str = Field(
        ..., max_length=10000, description="Текст с требованиями"
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None, description="Контекст проекта"
    )


class RiskAssessmentRequest(BaseModel):
    """Запрос на оценку рисков"""

    architecture: Dict[str, Any] = Field(..., description="Архитектурное решение")
    project_context: Optional[Dict[str, Any]] = Field(
        default=None, description="Контекст проекта"
    )


# Создаем router
router = APIRouter(prefix="/api/assistants", tags=["AI Assistants"])

# Инициализируем ассистентов
assistants: Dict[str, Any] = {}
assistant_instances: Dict[str, Any] = {}


async def get_architect_assistant() -> ArchitectAssistant:
    """Зависимость для получения ассистента архитектора"""
    if "architect" not in assistant_instances:
        assistant_instances["architect"] = ArchitectAssistant()
    return assistant_instances["architect"]


# Инициализация логгера
logger = StructuredLogger(__name__).logger


@router.get("/health", summary="Проверка состояния API")
async def health_check():
    """Проверка состояния AI-ассистентов API"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "available_assistants": (
            list(assistant_instances.keys()) if assistant_instances else []
        ),
        "version": "1.0.0",
    }


@router.get("/", summary="Список доступных ассистентов")
async def list_assistants():
    """Получение списка всех доступных AI-ассистентов"""
    return {
        "assistants": settings.assistant_configs,
        "total_count": len(settings.assistant_configs),
    }


@router.post(
    "/chat/{assistant_role}", response_model=ChatResponse, summary="Чат с ассистентом"
)
@limiter.limit("20/minute")  # Rate limit: 20 chat messages per minute
async def chat_with_assistant(
    api_request: Request,
    assistant_role: str,
    request: ChatRequest,
    assistant=Depends(get_architect_assistant),  # Пока используем только архитектора
):
    """
    Общение с конкретным ассистентом

    Args:
        assistant_role: Роль ассистента (architect, developer, tester, pm, analyst)
        request: Запрос пользователя
        assistant: Экземпляр ассистента
    """
    try:
        # Валидируем роль ассистента
        if assistant_role not in settings.assistant_configs:
            raise HTTPException(
                status_code=404,
                detail=f"Ассистент с ролью '{assistant_role}' не найден",
            )

        # Input validation
        if not isinstance(request.query, str) or not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        # Limit query length (prevent DoS)
        max_query_length = 5000
        if len(request.query) > max_query_length:
            raise HTTPException(
                status_code=400,
                detail=f"Query too long. Maximum length: {max_query_length} characters",
            )

        # Sanitize assistant_role (prevent injection)
        assistant_role = assistant_role.strip()[:100]

        # Обрабатываем запрос с timeout
        timeout = 30.0  # 30 seconds timeout
        try:
            response = await asyncio.wait_for(
                assistant.process_query(
                    query=request.query,
                    context=request.context,
                    user_id=request.conversation_id,
                ),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            logger.warning(
                "Timeout in chat_with_assistant",
                extra={
                    "assistant_role": assistant_role,
                    "timeout": timeout,
                    "query_length": len(request.query),
                },
            )
            raise HTTPException(
                status_code=504,
                detail="Request timeout. Please try again with a shorter query.",
            )

        return ChatResponse(
            message_id=response.message.id,
            content=response.message.content,
            role=response.message.role,
            timestamp=response.message.timestamp,
            sources=[
                {"page_content": doc.page_content, "metadata": doc.metadata}
                for doc in response.sources
            ],
            confidence=response.confidence,
            conversation_id=request.conversation_id or "default",
        )

    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(
            "Ошибка при обработке чата",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "assistant_role": assistant_role,
                "conversation_id": request.conversation_id,
                "path": api_request.url.path,
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="An error occurred while processing chat request"
        )


@router.post(
    "/architect/analyze-requirements", summary="Анализ требований для архитектора"
)
@limiter.limit("10/minute")  # Rate limit: 10 analysis requests per minute
async def analyze_requirements(
    api_request: Request,
    request: AnalyzeRequirementsRequest,
    assistant: ArchitectAssistant = Depends(get_architect_assistant),
):
    """
    Специализированный анализ бизнес-требований для архитектора

    Args:
        request: Запрос с требованиями
        assistant: Ассистент архитектора

    Returns:
        Структурированный анализ требований
    """
    try:
        # Input validation
        if (
            not isinstance(request.requirements_text, str)
            or not request.requirements_text.strip()
        ):
            raise HTTPException(
                status_code=400, detail="Requirements text cannot be empty"
            )

        # Limit requirements text length (prevent DoS)
        max_length = 10000
        if len(request.requirements_text) > max_length:
            raise HTTPException(
                status_code=400,
                detail=f"Requirements text too long. Maximum length: {max_length} characters",
            )

        # Process with timeout
        timeout = 60.0  # 60 seconds timeout for analysis
        result = await asyncio.wait_for(
            assistant.analyze_requirements(
                requirements_text=request.requirements_text, context=request.context
            ),
            timeout=timeout,
        )

        return {"success": True, "data": result, "timestamp": datetime.now()}

    except asyncio.TimeoutError:
        logger.warning(
            "Timeout in analyze_requirements",
            extra={
                "timeout": timeout,
                "requirements_length": len(request.requirements_text),
            },
        )
        raise HTTPException(
            status_code=504,
            detail="Analysis timeout. Please try again with shorter requirements.",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Ошибка при анализе требований: {e}",
            extra={
                "error_type": type(e).__name__,
                "requirements_length": len(request.requirements_text),
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="An error occurred while analyzing requirements"
        )


@router.post("/architect/generate-diagram", summary="Генерация архитектурной диаграммы")
@limiter.limit("5/minute")  # Rate limit: 5 diagram generations per minute
async def generate_diagram(
    api_request: Request,
    request: GenerateDiagramRequest,
    assistant: ArchitectAssistant = Depends(get_architect_assistant),
):
    """
    Генерация архитектурной диаграммы в формате Mermaid

    Args:
        request: Запрос с архитектурным предложением
        assistant: Ассистент архитектора

    Returns:
        Код диаграммы и описание архитектуры
    """
    try:
        result = await assistant.generate_diagram(
            architecture_proposal=request.architecture_proposal,
            diagram_type=request.diagram_type,
            diagram_requirements=request.diagram_requirements,
        )

        return {"success": True, "data": result, "timestamp": datetime.now()}

    except Exception as e:
        logger.error(
            "Ошибка при генерации диаграммы",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "diagram_type": (
                    request.diagram_type if hasattr(request, "diagram_type") else None
                ),
            },
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/architect/comprehensive-analysis", summary="Комплексный анализ архитектора"
)
@limiter.limit("5/minute")  # Rate limit: 5 comprehensive analyses per minute
async def comprehensive_analysis(
    api_request: Request,
    request: ComprehensiveAnalysisRequest,
    assistant: ArchitectAssistant = Depends(get_architect_assistant),
):
    """
    Полный анализ: требования + архитектура + риски

    Args:
        request: Запрос с требованиями
        assistant: Ассистент архитектора

    Returns:
        Полный анализ с рекомендациями
    """
    try:
        result = await assistant.create_comprehensive_analysis(
            requirements_text=request.requirements_text, context=request.context
        )

        return {"success": True, "data": result, "timestamp": datetime.now()}

    except Exception as e:
        logger.error(
            "Ошибка при комплексном анализе",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/architect/assess-risks", summary="Оценка рисков архитектуры")
@limiter.limit("10/minute")  # Rate limit: 10 risk assessments per minute
async def assess_risks(
    api_request: Request,
    request: RiskAssessmentRequest,
    assistant: ArchitectAssistant = Depends(get_architect_assistant),
):
    """
    Оценка рисков архитектурного решения

    Args:
        request: Запрос с архитектурой
        assistant: Ассистент архитектора

    Returns:
        Анализ рисков и стратегии минимизации
    """
    try:
        result = await assistant.assess_risks(
            architecture=request.architecture, project_context=request.project_context
        )

        return {"success": True, "data": result, "timestamp": datetime.now()}

    except Exception as e:
        logger.error(
            "Ошибка при оценке рисков",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/architect/conversation-history", summary="История диалогов архитектора")
async def get_conversation_history(
    limit: int = 50, assistant: ArchitectAssistant = Depends(get_architect_assistant)
):
    """
    Получение истории диалогов с ассистентом архитектора

    Args:
        limit: Количество сообщений для возврата
        assistant: Ассистент архитектора

    Returns:
        История диалогов
    """
    try:
        history = assistant.get_conversation_history(limit=limit)

        return {
            "success": True,
            "data": {
                "conversation_history": [
                    {
                        "id": msg.id,
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp,
                        "context": msg.context,
                        "metadata": msg.metadata,
                    }
                    for msg in history
                ],
                "total_count": len(history),
            },
            "timestamp": datetime.now(),
        }

    except Exception as e:
        logger.error(
            "Ошибка при получении истории",
            extra={"error": str(e), "error_type": type(e).__name__, "limit": limit},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/architect/conversation-history", summary="Очистка истории диалогов")
async def clear_conversation_history(
    assistant: ArchitectAssistant = Depends(get_architect_assistant),
):
    """
    Очистка истории диалогов с ассистентом архитектора

    Args:
        assistant: Ассистент архитектора

    Returns:
        Подтверждение очистки
    """
    try:
        assistant.clear_conversation_history()

        return {
            "success": True,
            "message": "История диалогов очищена",
            "timestamp": datetime.now(),
        }

    except Exception as e:
        logger.error(
            "Ошибка при очистке истории",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/architect/stats", summary="Статистика ассистента архитектора")
async def get_assistant_stats(
    assistant: ArchitectAssistant = Depends(get_architect_assistant),
):
    """
    Получение статистики использования ассистента

    Args:
        assistant: Ассистент архитектора

    Returns:
        Статистика использования
    """
    try:
        stats = await assistant.get_stats()

        return {"success": True, "data": stats, "timestamp": datetime.now()}

    except Exception as e:
        logger.error(
            "Ошибка при получении статистики",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge/add", summary="Добавление знаний в базу ассистента")
@limiter.limit("10/minute")  # Rate limit: 10 knowledge additions per minute
async def add_knowledge(
    request: Request,
    documents: List[Dict[str, Any]],
    role: str = "architect",
    user_id: str = "system",
    assistant: ArchitectAssistant = Depends(get_architect_assistant),
):
    """
    Добавление новых документов в базу знаний ассистента

    Args:
        documents: Список документов для добавления
        role: Роль ассистента
        user_id: ID пользователя
        assistant: Ассистент архитектора

    Returns:
        Подтверждение добавления
    """
    try:
        await assistant.add_knowledge(documents=documents, user_id=user_id)

        return {
            "success": True,
            "message": f"Добавлено {len(documents)} документов в базу знаний",
            "documents_count": len(documents),
            "timestamp": datetime.now(),
        }

    except Exception as e:
        logger.error(
            "Ошибка при добавлении знаний",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "role": role,
                "documents_count": len(documents) if documents else 0,
            },
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


# Создаем основное приложение
def create_app() -> APIRouter:
    """Создание FastAPI приложения"""
    return router


# Экспортируем router для использования в main.py
__all__ = ["router", "create_app"]
