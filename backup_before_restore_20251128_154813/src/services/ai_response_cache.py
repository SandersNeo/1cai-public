# [NEXUS IDENTITY] ID: -1352123819246249901 | DATE: 2025-11-19

"""
AI Response Caching with Semantic Similarity
Версия: 2.0.0

Улучшения:
- Улучшена обработка ошибок
- Structured logging
- Валидация входных данных
"""

import hashlib
import json
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

# Lazy import для sentence-transformers (тяжёлая библиотека)
try:
