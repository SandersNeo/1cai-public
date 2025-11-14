"""
Monitoring API Endpoints
Версия: 2.1.0

Улучшения:
- Улучшена обработка ошибок
- Structured logging
"""

from fastapi import APIRouter, HTTPException
from src.monitoring.prometheus_metrics import metrics_endpoint
from src.services.health_checker import get_health_checker
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.get("/metrics")
async def get_prometheus_metrics():
    """
    Prometheus metrics endpoint
    
    Scrape this endpoint with Prometheus:
    
    ```yaml
    scrape_configs:
      - job_name: '1c-ai-api'
        static_configs:
          - targets: ['api:8000']
        metrics_path: '/monitoring/metrics'
    ```
    """
    try:
        metrics = await metrics_endpoint()
        logger.debug("Prometheus metrics retrieved successfully")
        return metrics
    except Exception as e:
        logger.error(
            f"Error getting Prometheus metrics: {e}",
            extra={"error_type": type(e).__name__},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metrics: {str(e)}")


@router.get("/health/detailed")
async def detailed_health_check():
    """
    Detailed health check with all services
    
    Returns status of:
    - PostgreSQL
    - Redis  
    - Neo4j
    - Qdrant
    - Elasticsearch
    - OpenAI API
    """
    try:
        health_checker = get_health_checker()
        result = await health_checker.check_all()
        
        logger.info(
            "Detailed health check completed",
            extra={
                "overall_status": result.get("status"),
                "healthy_count": result.get("healthy_count", 0),
                "total_count": result.get("total_count", 0)
            }
        )
        
        return result
    except Exception as e:
        logger.error(
            f"Error performing detailed health check: {e}",
            extra={"error_type": type(e).__name__},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


