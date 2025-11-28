from typing import Any, Dict

from src.ai.clients.kimi_client import KimiClient, KimiConfig
from src.ai.strategies.base import AIStrategy
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class KimiStrategy(AIStrategy):
    """Strategy for Kimi-K2-Thinking"""

    def __init__(self):
        try:
