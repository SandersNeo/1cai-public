"""
Security Monitoring API - endpoints для security dashboard
Версия: 2.1.0

Улучшения:
- Input validation
- Structured logging
- Улучшена обработка ошибок
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

router = APIRouter(prefix="/api/security", tags=["Security Monitoring"])


@router.get("/metrics")
async def get_security_metrics():
    """
    Получить security метрики
    
    Returns:
        - blocked_inputs_24h: Количество заблокированных входов
        - leakage_attempts: Попытки утечки данных
        - human_approvals_24h: Количество human approvals
        - ml_rejections: AI-based отклонения
        - trends: Тренды
    """
    # В продакшене: реальные данные из БД
    return {
        'blocked_inputs_24h': 12,
        'blocked_trend': '-15% vs yesterday',
        'leakage_attempts': 0,
        'leakage_trend': '0% (excellent!)',
        'human_approvals_24h': 45,
        'approval_trend': '+5% vs yesterday',
        'ml_rejections': 8,
        'ml_trend': '-20% (fewer attacks)',
        'overall_security_score': 9.8
    }


@router.get("/alerts")
async def get_security_alerts(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of alerts")
):
    """
    Получить recent security alerts
    
    Security: Input validation для limit
    """
    try:
        # В продакшене: из БД
        alerts = [
        {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'input_blocked',
            'agent_id': 'developer_ai_secure',
            'reason': 'Prompt injection detected',
            'severity': 'HIGH',
            'confidence': 0.92
        },
        {
            'timestamp': (datetime.now() - timedelta(hours=2)).isoformat(),
            'event_type': 'rate_limit_exceeded',
            'agent_id': 'copilot',
            'reason': 'User exceeded 100 req/min',
            'severity': 'MEDIUM',
            'confidence': 1.0
        }
        ]
        
        # Limit results
        limited_alerts = alerts[:limit]
        
        logger.info(
            "Security alerts retrieved",
            extra={
                "limit": limit,
                "alerts_count": len(limited_alerts)
            }
        )
        
        return limited_alerts
    except Exception as e:
        logger.error(
            f"Error getting security alerts: {e}",
            extra={
                "limit": limit,
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Failed to retrieve alerts: {str(e)}")


@router.get("/agent-compliance")
async def get_agent_compliance():
    """
    Проверка соответствия всех агентов Rule of Two
    """
    agents = [
        {
            'name': 'Developer AI',
            'id': 'developer_ai_secure',
            'config': '[AB]',
            'compliant': True,
            'properties': {
                'untrusted_input': True,
                'sensitive_access': True,
                'state_change': False
            }
        },
        {
            'name': 'Code Review AI',
            'id': 'code_review_ai_secure',
            'config': '[BC]',
            'compliant': True,
            'properties': {
                'untrusted_input': False,
                'sensitive_access': True,
                'state_change': True
            }
        },
        {
            'name': 'SQL Optimizer',
            'id': 'sql_optimizer_secure',
            'config': '[AB]',
            'compliant': True,
            'properties': {
                'untrusted_input': True,
                'sensitive_access': True,
                'state_change': False
            }
        },
        {
            'name': 'DevOps AI',
            'id': 'devops_ai_secure',
            'config': '[BC]',
            'compliant': True,
            'properties': {
                'untrusted_input': False,
                'sensitive_access': True,
                'state_change': True
            }
        },
        # Остальные 6 агентов...
    ]
    
    total_agents = len(agents)
    compliant_agents = sum(1 for a in agents if a['compliant'])
    
    return {
        'total_agents': total_agents,
        'compliant_agents': compliant_agents,
        'compliance_rate': (compliant_agents / total_agents) * 100,
        'agents': agents
    }


@router.get("/audit-log")
async def get_audit_log(
    agent_id: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 100
):
    """
    Получить audit log записи
    """
    # В продакшене: запрос к БД с фильтрами
    return {
        'total': 1234,
        'entries': [
            {
                'timestamp': datetime.now().isoformat(),
                'event_type': 'ai_request',
                'agent_id': 'developer_ai_secure',
                'user_id': 'user_123',
                'rule_config': '[AB]',
                'human_approved': True,
                'input_hash': 'abc123...'
            }
        ]
    }


