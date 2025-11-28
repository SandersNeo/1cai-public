"""
Generation Service
"""
import re

from src.infrastructure.logging.structured_logging import StructuredLogger
from src.modules.copilot.services.model_service import ModelService

logger = StructuredLogger(__name__).logger


class GenerationService:
    """Service for code generation"""

    def __init__(self, model_service: ModelService):
        self.model_service = model_service

    async def generate_code(
            self,
            prompt: str,
            code_type: str = "function") -> str:
        """
        Generate code from description
        Uses model if available, otherwise templates
        """
        if self.model_service.is_loaded():
            return await self._generate_with_model(prompt, code_type)
        else:
            return self._generate_with_template(prompt, code_type)

    async def _generate_with_model(self, prompt: str, code_type: str) -> str:
        """Model-based code generation"""
        import torch

        model = self.model_service.get_model()
        tokenizer = self.model_service.get_tokenizer()
        device = self.model_service.get_device()

        try:
