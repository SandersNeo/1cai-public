"""
Completion Service
"""
from typing import Any, Dict, List

from src.infrastructure.logging.structured_logging import StructuredLogger
from src.modules.copilot.services.model_service import ModelService

logger = StructuredLogger(__name__).logger


class CompletionService:
    """Service for code completion"""

    def __init__(self, model_service: ModelService):
        self.model_service = model_service

    async def get_completions(self,
                              code: str,
                              current_line: str,
                              max_suggestions: int = 3) -> List[Dict[str,
                                                                     Any]]:
        """
        Get code completion suggestions
        Uses model if available, otherwise rule-based
        """
        if self.model_service.is_loaded():
            return await self._get_model_completions(code, current_line, max_suggestions)
        else:
            return self._get_rule_based_completions(
                code, current_line, max_suggestions)

    async def _get_model_completions(
            self, code: str, current_line: str, max_suggestions: int) -> List[Dict[str, Any]]:
        """Model-based completions"""
        import torch

        suggestions = []
        model = self.model_service.get_model()
        tokenizer = self.model_service.get_tokenizer()
        device = self.model_service.get_device()

        try:
