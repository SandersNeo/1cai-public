# [NEXUS IDENTITY] ID: -5481155745247461037 | DATE: 2025-11-19

"""
Metrics Collection Middleware
Версия: 2.0.0

Улучшения:
- Улучшенная нормализация endpoints
- Обработка ошибок при сбое метрик
- Структурированное логирование
- Поддержка различных типов ID в путях
"""

import re
import time
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

# Try to import prometheus metrics (graceful fallback if not available)
try:
