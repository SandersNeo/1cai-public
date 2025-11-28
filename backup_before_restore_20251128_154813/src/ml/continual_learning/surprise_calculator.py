"""
Surprise Calculator

Computes surprise scores for Nested Learning updates.
Surprise determines which memory levels should be updated.

Based on prediction error and context.
"""

from typing import Any, Dict, Optional

import numpy as np

from src.utils.structured_logging import StructuredLogger

from .types import SurpriseScore

logger = StructuredLogger(__name__).logger


class SurpriseCalculator:
    """
    Calculate surprise scores for continual learning

    Surprise is based on:
    - Prediction error (how wrong was the prediction)
    - Context novelty (how different from past examples)
    - Temporal distance (how long since similar example)

    Example:
        >>> calc = SurpriseCalculator()
        >>> surprise = calc.compute(actual=42, predicted=10)
        >>> print(f"Surprise: {surprise:.2f}")
    """

    def __init__(self, method: str = "mse"):
        """
        Initialize surprise calculator

        Args:
            method: Calculation method ("mse", "cosine", "kl")
        """
        self.method = method
        logger.info("Created SurpriseCalculator with method=%s")

    def compute(
            self,
            actual: Any,
            predicted: Any,
            context: Optional[Dict] = None) -> SurpriseScore:
        """
        Compute surprise score

        Args:
            actual: Actual outcome
            predicted: Predicted outcome
            context: Optional context for weighting

        Returns:
            Surprise score (0.0 to 1.0)
        """
        if self.method == "mse":
            return self._compute_mse(actual, predicted)
        elif self.method == "cosine":
            return self._compute_cosine(actual, predicted)
        elif self.method == "kl":
            return self._compute_kl(actual, predicted)
        else:
            raise ValueError(f"Unknown method: {self.method}")

    def _compute_mse(self, actual: Any, predicted: Any) -> SurpriseScore:
        """Compute surprise using Mean Squared Error"""
        try:
