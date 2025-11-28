# [NEXUS IDENTITY] ID: -7713792861972064162 | DATE: 2025-11-19

"""
OpenAI Code Analyzer Service
Специализированный сервис для анализа кода через OpenAI API
Версия: 1.0.0
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

# Динамический импорт settings для избежания циклических зависимостей
try:
