from typing import Any, Dict

from src.ai.qwen_client import QwenCoderClient
from src.ai.strategies.base import AIStrategy
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class QwenStrategy(AIStrategy):
    """Strategy for Qwen3-Coder"""

    def __init__(self):
        # Lazy initialization or DI is preferred to avoid connection errors at
        # startup
        pass

    @property
    def service_name(self) -> str:
        return "qwen_coder"

    def _get_client(self):
        try:
