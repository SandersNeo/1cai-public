"""
Base Agent Abstract Class

Унифицированный базовый класс для всех AI агентов в системе.
Обеспечивает единый интерфейс, мониторинг, и интеграцию с Revolutionary Components.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from prometheus_client import Counter, Gauge, Histogram

# Import Adaptive LLM Selector
try:
