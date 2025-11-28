import re
import time
from typing import Any, Dict

from src.ai.strategies.base import AIStrategy
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class CodeGenerationStrategy(AIStrategy):
    def __init__(self, kimi_client=None, qwen_client=None):
        self.kimi_client = kimi_client
        self.qwen_client = qwen_client

    async def execute(self,
                      query: str,
                      context: Dict[str,
                                    Any]) -> Dict[str,
                                                  Any]:
        """Handle code generation requests - prioritizes Kimi-K2-Thinking for complex reasoning"""

        # Try Kimi-K2-Thinking first (better for complex code generation)
        if self.kimi_client and self.kimi_client.is_configured:
            try:
