# [NEXUS IDENTITY] ID: -695444790217978972 | DATE: 2025-11-19

"""
OpenTelemetry Setup for Distributed Tracing
Версия: 2.1.0

Улучшения:
- Structured logging
- Улучшена обработка ошибок

Best Practices from top companies (Google, Microsoft, AWS, etc.)

Features:
- Automatic instrumentation for FastAPI, asyncpg, httpx, redis
- Export to Prometheus, Jaeger, OTLP
- Custom spans for business logic
- Correlation IDs for request tracking
"""

import os
from typing import Optional

from src.infrastructure.logging.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

# Try to import OpenTelemetry (optional dependency)
try:
