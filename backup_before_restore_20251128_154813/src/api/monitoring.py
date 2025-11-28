# [NEXUS IDENTITY] ID: -637803051261194503 | DATE: 2025-11-19

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
