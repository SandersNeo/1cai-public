"""
Code Approval API - для human-in-the-loop approval process
Версия: 2.1.0

Улучшения:
- Structured logging
- Улучшена обработка ошибок
- Input validation
- Timeout handling
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import List, Optional
from slowapi import Limiter
from slowapi.util import get_remote_address
from datetime import timedelta
import asyncio

from src.ai.agents.developer_agent_secure import DeveloperAISecure
from src.database import get_pool
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


router = APIRouter(prefix="/api/code-approval", tags=["Code Approval"])
limiter = Limiter(key_func=get_remote_address)


class CodeGenerationRequest(BaseModel):
    prompt: str = Field(..., max_length=5000)
    context: Optional[dict] = None
    user_id: str = Field(..., max_length=100)


class CodeApprovalRequest(BaseModel):
    token: str = Field(..., max_length=200)
    approved_by_user: str = Field(..., max_length=100)
    changes_made: Optional[str] = Field(None, max_length=2000)


class BulkApprovalRequest(BaseModel):
    tokens: List[str] = Field(..., max_items=100)
    approved_by_user: str = Field(..., max_length=100)


# Singleton agent instance
_developer_ai = None

def get_developer_ai() -> DeveloperAISecure:
    global _developer_ai
    if _developer_ai is None:
        _developer_ai = DeveloperAISecure()
    return _developer_ai


@router.post(
    "/generate",
    summary="Generate code with AI",
    description="Generate code with AI and return suggestion with approval token",
    responses={
        200: {"description": "Code generated successfully"},
        400: {"description": "Invalid input"},
        403: {"description": "Request blocked by security"},
        429: {"description": "Rate limit exceeded"}
    }
)
@limiter.limit("10/minute")  # Rate limit: 10 requests per minute
async def generate_code(
    api_request: Request,
    request: CodeGenerationRequest,
    agent: DeveloperAISecure = Depends(get_developer_ai)
):
    """
    Генерирует код с AI с валидацией входных данных
    
    Best practices:
    - Валидация длины prompt
    - Sanitization входных данных
    - Улучшенная обработка ошибок
    """
    try:
        # Input validation and sanitization (best practice)
        prompt = request.prompt.strip()
        if not prompt:
            raise HTTPException(
                status_code=400,
                detail="Prompt cannot be empty"
            )
        
        # Limit prompt length (prevent DoS)
        max_prompt_length = 5000
        if len(prompt) > max_prompt_length:
            raise HTTPException(
                status_code=400,
                detail=f"Prompt too long. Maximum length: {max_prompt_length} characters"
            )
        
        # Sanitize user_id
        user_id = request.user_id.strip()[:100]  # Limit length
        if not user_id:
            raise HTTPException(
                status_code=400,
                detail="User ID cannot be empty"
            )
        
        result = agent.generate_code(
            prompt=prompt,
            context={'user_id': user_id, **(request.context or {})}
        )
        
        if result.get('blocked'):
            raise HTTPException(
                status_code=403,
                detail=result.get('error', 'Request blocked by security')
            )
        
        return {
            'success': True,
            'suggestion': result['suggestion'],
            'token': result['token'],
            'safety': result['safety'],
            'requires_approval': result['requires_approval'],
            'can_auto_apply': result['can_auto_apply'],
            'preview_url': result['preview_url'],
            'redacted': result.get('redacted', False)
        }
    
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(
            "Unexpected error generating code",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "user_id": request.user_id if hasattr(request, 'user_id') else None,
                "prompt_length": len(request.prompt) if hasattr(request, 'prompt') else 0
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="An error occurred while generating code"
        )


@router.get("/preview/{token}")
async def get_preview(
    token: str,
    agent: DeveloperAISecure = Depends(get_developer_ai)
):
    """
    Получить preview suggestion для review с input validation
    """
    # Input validation
    if not isinstance(token, str) or not token.strip():
        logger.warning(
            "Invalid token in get_preview",
            extra={"token_type": type(token).__name__ if token else None}
        )
        raise HTTPException(status_code=400, detail="Token cannot be empty")
    
    # Limit token length (prevent DoS)
    max_token_length = 200
    if len(token) > max_token_length:
        logger.warning(
            "Token too long in get_preview",
            extra={"token_length": len(token), "max_length": max_token_length}
        )
        raise HTTPException(status_code=400, detail="Token too long")
    
    try:
        if token not in agent._pending_suggestions:
            logger.warning(
                "Token not found in get_preview",
                extra={"token": token[:50] if token else None}
            )
            raise HTTPException(status_code=404, detail="Token not found or expired")
        
        suggestion_data = agent._pending_suggestions[token]
        
        return {
            'suggestion': suggestion_data['suggestion'],
            'prompt': suggestion_data['prompt'],
            'safety': suggestion_data['safety'],
            'created_at': suggestion_data['created_at'].isoformat(),
            'expires_at': (suggestion_data['created_at'] + timedelta(minutes=30)).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error in get_preview",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "token": token[:50] if token else None
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="An error occurred while retrieving preview")


@router.post("/approve")
@limiter.limit("30/minute")  # Rate limit: 30 approvals per minute
async def approve_suggestion(
    api_request: Request,
    request: CodeApprovalRequest,
    agent: DeveloperAISecure = Depends(get_developer_ai)
):
    """
    Одобрить и применить suggestion с input validation и timeout handling
    
    КРИТИЧНО: Требует human approval!
    """
    # Input validation
    if not isinstance(request.token, str) or not request.token.strip():
        logger.warning(
            "Invalid token in approve_suggestion",
            extra={"token_type": type(request.token).__name__ if request.token else None}
        )
        raise HTTPException(status_code=400, detail="Token cannot be empty")
    
    # Limit token length
    max_token_length = 200
    if len(request.token) > max_token_length:
        logger.warning(
            "Token too long in approve_suggestion",
            extra={"token_length": len(request.token), "max_length": max_token_length}
        )
        raise HTTPException(status_code=400, detail="Token too long")
    
    if not isinstance(request.approved_by_user, str) or not request.approved_by_user.strip():
        logger.warning(
            "Invalid approved_by_user in approve_suggestion",
            extra={"user_type": type(request.approved_by_user).__name__ if request.approved_by_user else None}
        )
        raise HTTPException(status_code=400, detail="Approved by user cannot be empty")
    
    # Limit user length
    max_user_length = 100
    if len(request.approved_by_user) > max_user_length:
        request.approved_by_user = request.approved_by_user[:max_user_length]
    
    try:
        # Timeout для операции применения (30 секунд)
        result = await asyncio.wait_for(
            asyncio.to_thread(
                agent.apply_suggestion,
                token=request.token,
                approved_by_user=request.approved_by_user,
                changes_made=request.changes_made
            ),
            timeout=30.0
        )
        
        if result.get('blocked'):
            logger.warning(
                "Suggestion blocked in approve_suggestion",
                extra={
                    "token": request.token[:50],
                    "approved_by_user": request.approved_by_user,
                    "error": result.get('error')
                }
            )
            raise HTTPException(
                status_code=403,
                detail=result.get('error', 'Application blocked')
            )
        
        logger.info(
            "Suggestion approved successfully",
            extra={
                "token": request.token[:50],
                "approved_by_user": request.approved_by_user,
                "commit_sha": result.get('commit_sha')
            }
        )
        
        return {
            'success': True,
            'applied': True,
            'commit_sha': result.get('commit_sha'),
            'message': 'Code suggestion applied successfully'
        }
    except asyncio.TimeoutError:
        logger.error(
            "Timeout in approve_suggestion",
            extra={
                "token": request.token[:50],
                "approved_by_user": request.approved_by_user
            }
        )
        raise HTTPException(status_code=504, detail="Operation timed out")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error in approve_suggestion",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "token": request.token[:50],
                "approved_by_user": request.approved_by_user
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="An error occurred while approving suggestion")


@router.post("/approve-all")
@limiter.limit("10/minute")  # Rate limit: 10 bulk approvals per minute
async def bulk_approve(
    api_request: Request,
    request: BulkApprovalRequest,
    agent: DeveloperAISecure = Depends(get_developer_ai)
):
    """
    Bulk approval для множества suggestions с input validation и timeout handling
    
    Применяется только к безопасным (score > 0.95)
    """
    # Input validation
    if not isinstance(request.tokens, list):
        logger.warning(
            "Invalid tokens type in bulk_approve",
            extra={"tokens_type": type(request.tokens).__name__}
        )
        raise HTTPException(status_code=400, detail="Tokens must be a list")
    
    if len(request.tokens) == 0:
        logger.warning("Empty tokens list in bulk_approve")
        raise HTTPException(status_code=400, detail="Tokens list cannot be empty")
    
    # Limit number of tokens (prevent DoS)
    max_tokens = 100
    if len(request.tokens) > max_tokens:
        logger.warning(
            "Too many tokens in bulk_approve",
            extra={"tokens_count": len(request.tokens), "max_tokens": max_tokens}
        )
        request.tokens = request.tokens[:max_tokens]
    
    # Validate each token
    validated_tokens = []
    for token in request.tokens:
        if isinstance(token, str) and token.strip() and len(token) <= 200:
            validated_tokens.append(token.strip())
    
    if len(validated_tokens) == 0:
        raise HTTPException(status_code=400, detail="No valid tokens provided")
    
    if not isinstance(request.approved_by_user, str) or not request.approved_by_user.strip():
        logger.warning(
            "Invalid approved_by_user in bulk_approve",
            extra={"user_type": type(request.approved_by_user).__name__ if request.approved_by_user else None}
        )
        raise HTTPException(status_code=400, detail="Approved by user cannot be empty")
    
    # Limit user length
    max_user_length = 100
    if len(request.approved_by_user) > max_user_length:
        request.approved_by_user = request.approved_by_user[:max_user_length]
    
    try:
        # Timeout для bulk операции (60 секунд)
        result = await asyncio.wait_for(
            asyncio.to_thread(
                agent.bulk_approve_safe_suggestions,
                tokens=validated_tokens,
                approved_by_user=request.approved_by_user
            ),
            timeout=60.0
        )
        
        logger.info(
            "Bulk approval completed",
            extra={
                "approved": len(result.get('approved', [])),
                "rejected": len(result.get('rejected', [])),
                "errors": len(result.get('errors', [])),
                "approved_by_user": request.approved_by_user
            }
        )
        
        return {
            'success': True,
            'approved': len(result['approved']),
            'rejected': len(result['rejected']),
            'errors': len(result['errors']),
            'details': result
        }
    except asyncio.TimeoutError:
        logger.error(
            "Timeout in bulk_approve",
            extra={
                "tokens_count": len(validated_tokens),
                "approved_by_user": request.approved_by_user
            }
        )
        raise HTTPException(status_code=504, detail="Bulk operation timed out")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error in bulk_approve",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "tokens_count": len(validated_tokens),
                "approved_by_user": request.approved_by_user
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="An error occurred while processing bulk approval")


@router.delete("/reject/{token}")
async def reject_suggestion(
    token: str,
    agent: DeveloperAISecure = Depends(get_developer_ai)
):
    """
    Отклонить suggestion с input validation
    """
    # Input validation
    if not isinstance(token, str) or not token.strip():
        logger.warning(
            "Invalid token in reject_suggestion",
            extra={"token_type": type(token).__name__ if token else None}
        )
        raise HTTPException(status_code=400, detail="Token cannot be empty")
    
    # Limit token length (prevent DoS)
    max_token_length = 200
    if len(token) > max_token_length:
        logger.warning(
            "Token too long in reject_suggestion",
            extra={"token_length": len(token), "max_length": max_token_length}
        )
        raise HTTPException(status_code=400, detail="Token too long")
    
    try:
        if token not in agent._pending_suggestions:
            logger.warning(
                "Token not found in reject_suggestion",
                extra={"token": token[:50] if token else None}
            )
            raise HTTPException(status_code=404, detail="Token not found")
        
        # Удаляем из pending
        del agent._pending_suggestions[token]
        
        logger.info(
            "Suggestion rejected",
            extra={"token": token[:50]}
        )
        
        return {
            'success': True,
            'message': 'Suggestion rejected'
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error in reject_suggestion",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "token": token[:50] if token else None
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="An error occurred while rejecting suggestion")


@router.get("/pending")
async def get_pending_suggestions(
    user_id: str,
    agent: DeveloperAISecure = Depends(get_developer_ai)
):
    """
    Получить все pending suggestions для пользователя с input validation
    """
    # Input validation
    if not isinstance(user_id, str) or not user_id.strip():
        logger.warning(
            "Invalid user_id in get_pending_suggestions",
            extra={"user_id_type": type(user_id).__name__ if user_id else None}
        )
        raise HTTPException(status_code=400, detail="User ID cannot be empty")
    
    # Limit user_id length (prevent DoS)
    max_user_id_length = 100
    if len(user_id) > max_user_id_length:
        logger.warning(
            "User ID too long in get_pending_suggestions",
            extra={"user_id_length": len(user_id), "max_length": max_user_id_length}
        )
        user_id = user_id[:max_user_id_length]
    
    try:
        user_suggestions = []
        
        for token, data in agent._pending_suggestions.items():
            if data.get('context', {}).get('user_id') == user_id:
                user_suggestions.append({
                    'token': token,
                    'prompt': data.get('prompt', ''),
                    'created_at': data.get('created_at').isoformat() if data.get('created_at') else None,
                    'safety_score': data.get('safety', {}).get('score', 0.0),
                    'can_auto_apply': data.get('safety', {}).get('score', 0.0) > 0.95
                })
        
        logger.debug(
            "Retrieved pending suggestions",
            extra={
                "user_id": user_id,
                "suggestions_count": len(user_suggestions)
            }
        )
        
        return {
            'pending': len(user_suggestions),
            'suggestions': user_suggestions
        }
    except Exception as e:
        logger.error(
            "Error in get_pending_suggestions",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "user_id": user_id
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="An error occurred while retrieving pending suggestions")


