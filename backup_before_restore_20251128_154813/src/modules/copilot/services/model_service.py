"""
Model Service
"""
import os
from typing import Any, Optional

from src.infrastructure.logging.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class ModelService:
    """Service for managing AI model and tokenizer"""

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.model_loaded = False
        self.device = "cpu"
        self._load_model()

    def _load_model(self):
        """Attempt to load fine-tuned model"""
        try:
