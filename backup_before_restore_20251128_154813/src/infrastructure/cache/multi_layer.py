# [NEXUS IDENTITY] ID: 951165206130129020 | DATE: 2025-11-19

"""
Multi-Layer Caching with Best Practices
Production-ready caching strategy used by top companies

Features:
- LRU eviction for in-memory cache
- Circuit breaker for Redis
- Prometheus metrics
- Cache warming
- Stale-while-revalidate pattern
"""

import asyncio
import hashlib
import json
from collections import OrderedDict
from contextlib import nullcontext
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.infrastructure.logging.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

# Try to import Prometheus client (optional)
try:
