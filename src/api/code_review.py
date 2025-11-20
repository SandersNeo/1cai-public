# [NEXUS IDENTITY] ID: 6818786406341445285 | DATE: 2025-11-19

"""
API endpoints для Code Review в реальном времени
Версия: 1.0.0
"""

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
import asyncio
from src.services.caching_service import get_cache_service
from src.middleware.rate_limiter import limiter, PUBLIC_RATE_LIMIT
from src.services.openai_code_analyzer import get_openai_analyzer
from src.api.code_analyzers import (
    analyze_typescript_code,
    analyze_python_code,
    analyze_javascript_code,
)
from src.utils.structured_logging import StructuredLogger

router = APIRouter(prefix="/api/code-review")
logger = StructuredLogger(__name__).logger


# ==================== МОДЕЛИ ДАННЫХ ====================


class CodeContextRequest(BaseModel):
    """Запрос на анализ кода"""

    content: str = Field(..., max_length=100000, description="Исходный код для анализа")
    language: Literal["bsl", "typescript", "javascript", "python", "java", "csharp"] = (
        Field(default="bsl", description="Язык программирования")
    )
    fileName: Optional[str] = Field(None, max_length=500, description="Имя файла")
    projectContext: Optional[dict] = Field(None, description="Контекст проекта")
    cursorPosition: Optional[dict] = Field(None, description="Позиция курсора")
    recentChanges: Optional[List[str]] = Field(None, description="Последние изменения")


class CodeSuggestion(BaseModel):
    """Предложение по улучшению кода"""

    id: str
    type: Literal["error", "warning", "info", "hint"]
    severity: Literal["critical", "high", "medium", "low"]
    message: str
    description: str
    suggestion: Optional[str] = None
    code: Optional[str] = None
    position: dict
    category: Literal[
        "performance", "security", "best-practice", "style", "bug", "optimization"
    ]
    autoFixable: bool
    confidence: float = Field(..., ge=0, le=1)


class CodeMetrics(BaseModel):
    """Метрики качества кода"""

    complexity: int = Field(..., ge=0, le=100)
    maintainability: int = Field(..., ge=0, le=100)
    securityScore: int = Field(..., ge=0, le=100)
    performanceScore: int = Field(..., ge=0, le=100)
    codeQuality: int = Field(..., ge=0, le=100)


class CodeStatistics(BaseModel):
    """Статистика кода"""

    totalLines: int
    functions: int
    variables: int
    comments: int
    potentialIssues: int


class CodeAnalysisResponse(BaseModel):
    """Ответ анализа кода"""

    suggestions: List[CodeSuggestion]
    metrics: CodeMetrics
    statistics: CodeStatistics
    recommendations: List[str]
    timestamp: datetime = Field(default_factory=datetime.now)
    analysisId: str


class AutoFixRequest(BaseModel):
    """Запрос на автоматическое исправление"""

    suggestionId: str = Field(..., max_length=100)
    code: str = Field(..., max_length=100000)


class AutoFixResponse(BaseModel):
    """Результат автозамены"""

    fixedCode: str
    changes: List[dict]
    success: bool
    message: str


# ==================== БАЗОВЫЙ АНАЛИЗАТОР (для Python) ====================


def analyze_bsl_code(code: str) -> dict:
    """Базовый анализ BSL кода"""
    if not code.strip():
        return {
            "suggestions": [],
            "metrics": {
                "complexity": 0,
                "maintainability": 100,
                "securityScore": 100,
                "performanceScore": 100,
                "codeQuality": 100,
            },
            "statistics": {
                "totalLines": 0,
                "functions": 0,
                "variables": 0,
                "comments": 0,
                "potentialIssues": 0,
            },
            "recommendations": [],
        }

    suggestions = []
    lines = code.split("\n")

    # Простые правила анализа
    for i, line in enumerate(lines, 1):
        # Проверка циклов с запросами
        if "Для" in line and "По" in line:
            # Проверяем следующие строки на наличие запросов
            next_lines = "\n".join(lines[i - 1 : min(i + 5, len(lines))])
            if "Запрос" in next_lines or "Справочники" in next_lines:
                suggestions.append(
                    {
                        "id": f"perf-{i}",
                        "type": "warning",
                        "severity": "high",
                        "message": "Возможна проблема производительности: запрос к БД в цикле",
                        "description": "Запросы к базе данных внутри цикла могут значительно замедлить выполнение",
                        "suggestion": "Рассмотрите вариант выполнения запроса вне цикла или использования группировок",
                        "position": {"line": i, "column": 1},
                        "category": "performance",
                        "autoFixable": False,
                        "confidence": 0.8,
                    }
                )

        # Проверка безопасности (SQL инъекции)
        if "Запрос" in line and "+" in line and "Запрос" in line:
            suggestions.append(
                {
                    "id": f"sec-{i}",
                    "type": "error",
                    "severity": "critical",
                    "message": "Потенциальная SQL инъекция",
                    "description": "Конкатенация строк в запросе может быть небезопасной",
                    "suggestion": "Используйте параметры запроса вместо конкатенации строк",
                    "position": {"line": i, "column": 1},
                    "category": "security",
                    "autoFixable": False,
                    "confidence": 0.9,
                }
            )

        # Проверка хардкода паролей
        if ("Пароль" in line or "password" in line.lower()) and (
            "=" in line or ":=" in line
        ):
            if '"' in line or "'" in line:
                suggestions.append(
                    {
                        "id": f"sec-pass-{i}",
                        "type": "error",
                        "severity": "critical",
                        "message": "Обнаружен хардкод пароля",
                        "description": "Пароли не должны храниться в коде",
                        "suggestion": "Используйте переменные окружения или хранилище секретов",
                        "position": {"line": i, "column": 1},
                        "category": "security",
                        "autoFixable": False,
                        "confidence": 1.0,
                    }
                )

        # Best practice: ПроверитьТип вместо Тип
        if "Если" in line and "Тип(" in line and "ПроверитьТип" not in line:
            suggestions.append(
                {
                    "id": f"bsl-type-{i}",
                    "type": "hint",
                    "severity": "low",
                    "message": "Рекомендуется использовать ПроверитьТип() вместо Тип()",
                    "description": "ПроверитьТип() более эффективен и безопасен",
                    "suggestion": "Замените Тип() на ПроверитьТип()",
                    "position": {"line": i, "column": 1},
                    "category": "best-practice",
                    "autoFixable": True,
                    "confidence": 0.7,
                }
            )

    # Вычисление метрик
    total_lines = len(lines)
    functions = len([l for l in lines if "Процедура" in l or "Функция" in l])
    variables = len([l for l in lines if "=" in l])
    comments = len(
        [
            l
            for l in lines
            if "//" in l
            or "#" in l
            or (l.strip().startswith("'") and len(l.strip()) > 1)
        ]
    )

    critical_issues = len([s for s in suggestions if s["severity"] == "critical"])
    high_issues = len([s for s in suggestions if s["severity"] == "high"])

    complexity = min(100, int((total_lines / 100) * 50 + (len(suggestions) / 10) * 50))
    maintainability = max(0, 100 - (critical_issues * 20 + high_issues * 10))

    security_issues = len([s for s in suggestions if s["category"] == "security"])
    security_score = max(0, 100 - security_issues * 25)

    performance_issues = len([s for s in suggestions if s["category"] == "performance"])
    performance_score = max(0, 100 - performance_issues * 15)

    code_quality = (maintainability + security_score + performance_score) / 3

    recommendations = []
    if security_score < 70:
        recommendations.append("Рекомендуется усилить проверки безопасности в коде")
    if performance_score < 70:
        recommendations.append(
            "Обнаружены проблемы производительности. Рассмотрите оптимизацию запросов и алгоритмов"
        )
    if maintainability < 70:
        recommendations.append("Код требует улучшения для лучшей поддерживаемости")
    if critical_issues > 0:
        recommendations.append(
            f"Обнаружено {critical_issues} критических проблем. Требуется немедленное исправление"
        )

    return {
        "suggestions": suggestions,
        "metrics": {
            "complexity": complexity,
            "maintainability": maintainability,
            "securityScore": security_score,
            "performanceScore": performance_score,
            "codeQuality": int(code_quality),
        },
        "statistics": {
            "totalLines": total_lines,
            "functions": functions,
            "variables": variables,
            "comments": comments,
            "potentialIssues": len(suggestions),
        },
        "recommendations": recommendations,
    }


# ==================== API ENDPOINTS ====================


@router.post(
    "/analyze",
    response_model=CodeAnalysisResponse,
    tags=["Code Review"],
    summary="Real-time code analysis",
    description="""
    Analyze code and provide improvement suggestions in real-time.
    
    **Supported Languages:**
    - BSL (1C:Enterprise)
    - TypeScript
    - JavaScript
    - Python
    - Java
    - C#
    
    **Analysis Features:**
    - Performance issues (N+1 queries, inefficient loops)
    - Security vulnerabilities (SQL injection, hardcoded secrets)
    - Code quality metrics (complexity, maintainability)
    - Best practices violations
    - Style suggestions
    
    **Caching:**
    - Results are cached for 1 hour
    - Cache key based on code content hash
    
    **Rate Limit:** Public rate limit (configurable)
    """,
    responses={
        200: {
            "description": "Code analysis results",
            "content": {
                "application/json": {
                    "example": {
                        "suggestions": [],
                        "metrics": {
                            "complexity": 10,
                            "maintainability": 85,
                            "securityScore": 90,
                            "performanceScore": 80,
                            "codeQuality": 85,
                        },
                        "statistics": {
                            "totalLines": 100,
                            "functions": 5,
                            "variables": 10,
                            "comments": 20,
                            "potentialIssues": 2,
                        },
                        "recommendations": ["Use parameterized queries"],
                        "analysisId": "analysis-1234567890",
                    }
                }
            },
        },
        400: {"description": "Invalid code or language"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Analysis error"},
    },
)
@limiter.limit(PUBLIC_RATE_LIMIT)
async def analyze_code(
    request: Request, request_data: CodeContextRequest, response: Response
):
    """
    Анализ кода с предложениями по улучшению

    Best practices:
    - Валидация длины кода
    - Sanitization входных данных
    - Улучшенная обработка ошибок
    """
    try:
        # Input validation and sanitization (best practice)
        code = request_data.content.strip()
        if not code:
            raise HTTPException(status_code=400, detail="Code cannot be empty")

        # Limit code length (prevent DoS)
        max_code_length = 100000  # 100KB max
        if len(code) > max_code_length:
            raise HTTPException(
                status_code=400,
                detail=f"Code too long. Maximum length: {max_code_length} characters",
            )

        # Validate language
        supported_languages = ["bsl", "typescript", "python", "javascript"]
        if request_data.language not in supported_languages:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported language: {request_data.language}. Supported: {', '.join(supported_languages)}",
            )

        # Sanitize file name if provided
        file_name = None
        if request_data.fileName:
            file_name = request_data.fileName.strip()[:200]  # Limit length
            # Prevent path traversal
            if ".." in file_name or "/" in file_name or "\\" in file_name:
                file_name = None  # Use None if invalid

        # Используем request_data как основной request
        code_request = request_data
        code_request.content = code  # Use sanitized code
        if file_name:
            code_request.fileName = file_name

        # Определяем вариант кэша в зависимости от доступности AI
        ai_variant = "local"
        openai_analyzer = None
        try:
            openai_analyzer = get_openai_analyzer()
            if getattr(openai_analyzer, "enabled", False):
                ai_variant = f"ai:{getattr(openai_analyzer, 'model', 'unknown')}"
        except Exception as analyzer_init_error:
            logger.warning(
                "Failed to initialize AI analyzer, fallback to local analysis",
                extra={
                    "error": str(analyzer_init_error),
                    "error_type": type(analyzer_init_error).__name__,
                },
            )
            openai_analyzer = None

        # Генерация ключа кэша (включая вариант AI, чтобы не кэшировать локальный анализ для AI клиентов)
        cache_service = get_cache_service()
        cache_key = cache_service.generate_key(
            "code_review",
            content=code_request.content,
            language=code_request.language,
            fileName=code_request.fileName or "",
            ai_variant=ai_variant,
        )

        logger.debug(
            "Code review cache variant selected",
            extra={
                "ai_variant": ai_variant,
                "ai_enabled": bool(
                    openai_analyzer and getattr(openai_analyzer, "enabled", False)
                ),
                "analyzer_type": (
                    type(openai_analyzer).__name__ if openai_analyzer else None
                ),
            },
        )

        # Попытка получить из кэша
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return CodeAnalysisResponse(**cached_result)

        # Локальный анализ кода (быстрый, без AI)
        if code_request.language == "bsl":
            result = analyze_bsl_code(code_request.content)
        elif code_request.language == "typescript":
            result = analyze_typescript_code(code_request.content)
        elif code_request.language == "python":
            result = analyze_python_code(code_request.content)
        elif code_request.language == "javascript":
            result = analyze_javascript_code(code_request.content)
        else:
            # Fallback для других языков - используем базовый анализатор
            logger.warning(
                "Language not fully supported, using basic analysis",
                extra={"language": code_request.language},
            )
            result = analyze_bsl_code(code_request.content)

        # AI анализ через OpenAI (асинхронно, если доступен) с timeout
        ai_suggestions = []
        if openai_analyzer and getattr(openai_analyzer, "enabled", False):
            # Timeout для AI анализа (30 секунд)
            ai_timeout = 30.0
            try:
                ai_suggestions = await asyncio.wait_for(
                    openai_analyzer.analyze_code(
                        code=code_request.content,
                        language=code_request.language,
                        context=code_request.projectContext,
                    ),
                    timeout=ai_timeout,
                )

                # Объединение с локальными предложениями
                result["suggestions"].extend(ai_suggestions)

                logger.info(
                    "AI suggestions added to analysis",
                    extra={
                        "ai_suggestions_count": len(ai_suggestions),
                        "language": code_request.language,
                    },
                )
            except asyncio.TimeoutError:
                logger.warning(
                    "AI analysis timeout",
                    extra={
                        "language": code_request.language,
                        "code_length": len(code_request.content),
                        "timeout": ai_timeout,
                    },
                )
                # Продолжаем без AI предложений
            except Exception as e:
                logger.warning(
                    "AI analysis unavailable, using local analysis only",
                    extra={
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "language": code_request.language,
                    },
                    exc_info=True,
                )
        else:
            logger.debug(
                "AI analyzer disabled or not initialized, skipping AI suggestions",
                extra={"ai_variant": ai_variant, "language": code_request.language},
            )

        analysis_id = f"analysis-{datetime.now().timestamp()}"

        response_data = CodeAnalysisResponse(
            suggestions=[CodeSuggestion(**s) for s in result["suggestions"]],
            metrics=CodeMetrics(**result["metrics"]),
            statistics=CodeStatistics(**result["statistics"]),
            recommendations=result["recommendations"],
            analysisId=analysis_id,
        )

        # Сохранение в кэш (TTL 1 час)
        await cache_service.set(cache_key, response_data.dict(), ttl=3600)

        return response_data

    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(
            "Unexpected error analyzing code",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "code_length": len(code) if "code" in locals() else 0,
                "language": (
                    request_data.language if hasattr(request_data, "language") else None
                ),
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="An error occurred while analyzing code"
        )


async def _apply_auto_fix(payload: AutoFixRequest) -> AutoFixResponse:
    """
    SMART Auto-Fix - Применение автозамены на основе типа issue

    Supports multiple fix patterns based on suggestion ID
    """

    try:
        fixed_code = payload.code
        changes = []

        # Parse suggestion ID to determine fix type
        suggestion_id = payload.suggestionId.lower()

        # Pattern 1: Type checking (Тип → ПроверитьТип)
        if "type-check" in suggestion_id or "Тип(" in fixed_code:
            original = fixed_code
            fixed_code = fixed_code.replace("Тип(", "ПроверитьТип(")

            if fixed_code != original:
                changes.append(
                    {
                        "type": "type_safety",
                        "old": "Тип(",
                        "new": "ПроверитьТип(",
                        "count": fixed_code.count("ПроверитьТип(")
                        - original.count("ПроверитьТип("),
                        "description": "Added type checking for safety",
                    }
                )

        # Pattern 2: Null checking
        if "null-check" in suggestion_id:
            import re

            # Find assignments without null checks
            pattern = r"(\w+)\s*=\s*(\w+\.\w+\([^)]*\));"

            def add_null_check(match):
                var_name = match.group(1)
                call = match.group(2)
                return f"{var_name} = {call};\nЕсли {var_name} = Неопределено Тогда\n    // Handle null\n    Возврат;\nКонецЕсли;"

            new_code = re.sub(pattern, add_null_check, fixed_code)
            if new_code != fixed_code:
                changes.append(
                    {
                        "type": "null_safety",
                        "description": "Added null checks",
                        "count": len(re.findall(pattern, fixed_code)),
                    }
                )
                fixed_code = new_code

        # Pattern 3: Error handling
        if "error-handling" in suggestion_id or "exception" in suggestion_id:
            if "Попытка" not in fixed_code:
                # Wrap code in try-catch
                lines = fixed_code.split("\n")
                indented = "\n".join(["    " + line for line in lines])
                fixed_code = f"Попытка\n{indented}\nИсключение\n    // Log error\n    ЗаписьЖурналаРегистрации(ОписаниеОшибки());\n    ВызватьИсключение;\nКонецПопытки;"

                changes.append(
                    {
                        "type": "error_handling",
                        "description": "Wrapped code in try-catch block",
                        "count": 1,
                    }
                )

        # Pattern 4: Performance - N+1 queries
        if "n+1" in suggestion_id or "batch" in suggestion_id:
            # Replace loop queries with batch query
            import re

            pattern = r"Для\s+Каждого\s+(\w+)\s+Из\s+(\w+)\s+Цикл\s+.*?Запрос\."

            if re.search(pattern, fixed_code, re.DOTALL):
                changes.append(
                    {
                        "type": "performance",
                        "description": "Suggested: Convert to batch query (manual intervention needed)",
                        "suggestion": "Replace loop with: Запрос.УстановитьПараметр('Список', Список);",
                    }
                )

        # Pattern 5: Magic numbers
        if "magic-number" in suggestion_id:
            import re

            # Find bare numbers (except 0, 1, -1)
            pattern = r"(?<=[^\w])(\d{2,})(?=[^\w])"

            def replace_with_constant(match):
                num = match.group(1)
                return f"КОНСТАНТА_{num}"

            new_code = re.sub(pattern, replace_with_constant, fixed_code)
            if new_code != fixed_code:
                changes.append(
                    {
                        "type": "maintainability",
                        "description": "Replaced magic numbers with constants",
                        "count": len(re.findall(pattern, fixed_code)),
                    }
                )
                fixed_code = new_code

        return AutoFixResponse(
            fixedCode=fixed_code,
            changes=changes,
            success=len(changes) > 0,
            message=(
                f"Applied {len(changes)} fix(es)"
                if changes
                else "No applicable auto-fixes for this suggestion"
            ),
        )

    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(
            "Error in auto-fix",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "suggestion_id": payload.suggestionId,
            },
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Ошибка автозамены: {str(e)}")


@router.post(
    "/auto-fix",
    response_model=AutoFixResponse,
    tags=["Code Review"],
    summary="Автоматическое исправление кода",
    description="Применяет автоматическое исправление к коду на основе предложения",
)
@limiter.limit("20/minute")  # Rate limit: 20 auto-fixes per minute
async def auto_fix_code_endpoint(
    api_request: Request, request: AutoFixRequest, response: Response
):
    return await _apply_auto_fix(request)


async def auto_fix_code(request: AutoFixRequest) -> AutoFixResponse:
    """
    Позволяет использовать auto-fix напрямую в unit-тестах, минуя FastAPI слой.
    """
    return await _apply_auto_fix(request)


@router.get(
    "/health",
    tags=["Code Review"],
    summary="Проверка состояния сервиса",
)
async def health_check():
    """Проверка доступности сервиса Code Review"""
    # Проверка доступности OpenAI
    openai_analyzer = get_openai_analyzer()
    ai_enabled = openai_analyzer.enabled

    return {
        "status": "healthy",
        "service": "code-review",
        "version": "1.0.0",
        "features": {
            "bsl": True,
            "typescript": True,  # ✅ Базовая поддержка
            "python": True,  # ✅ Базовая поддержка
            "javascript": True,  # ✅ Базовая поддержка
            "ai_analysis": ai_enabled,  # ✅ Интегрировано с OpenAI
        },
        "openai": {
            "enabled": ai_enabled,
            "model": openai_analyzer.model if ai_enabled else None,
        },
    }
