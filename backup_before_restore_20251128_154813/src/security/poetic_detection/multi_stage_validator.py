"""
Multi-Stage Validator

Combines poetic detection and intent extraction for comprehensive validation.
"""

from dataclasses import dataclass
from typing import Dict, Optional

from loguru import logger

from .intent_extractor import IntentResult, SemanticIntentExtractor
from .poetic_detector import PoeticAnalysis, PoeticFormDetector


@dataclass
class ValidationResult:
    """Result of multi-stage validation"""

    allowed: bool
    reason: str
    poetic_analysis: Optional[PoeticAnalysis] = None
    intent_result: Optional[IntentResult] = None
    stage_completed: str = ""  # Which stage completed


class MultiStageValidator:
    """
    Multi-stage validation pipeline.

    Stage 1: Poetic form detection
    Stage 2: Intent extraction (if poetic)
    Stage 3: Standard safety check
    """

    def __init__(self, orchestrator=None):
        """
        Initialize validator.

        Args:
            orchestrator: AI orchestrator for LLM access
        """
        self.poetic_detector = PoeticFormDetector(threshold=0.6)
        self.intent_extractor = SemanticIntentExtractor(orchestrator)

    async def validate(
            self,
            query: str,
            context: Optional[Dict] = None) -> ValidationResult:
        """
        Validate query through multi-stage pipeline.

        Args:
            query: User query
            context: Optional context

        Returns:
            ValidationResult
        """
        try:
