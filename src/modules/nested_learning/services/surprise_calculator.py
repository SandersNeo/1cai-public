"""
Surprise Calculator

Computes surprise scores for Nested Learning updates.
Surprise determines which memory levels should be updated.

Based on prediction error and context.
"""

from typing import Any, Dict, Optional

import numpy as np

from src.utils.structured_logging import StructuredLogger

from src.modules.nested_learning.domain.types import SurpriseScore

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
        logger.info("Created SurpriseCalculator with method=%s", method)

    def compute(self, actual: Any, predicted: Any, context: Optional[Dict] = None) -> SurpriseScore:
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
            # Convert to numpy arrays
            if isinstance(actual, (int, float)):
                actual = np.array([actual])
                predicted = np.array([predicted])
            else:
                actual = np.array(actual)
                predicted = np.array(predicted)

            # Compute MSE
            mse = np.mean((actual - predicted) ** 2)

            # Normalize to [0, 1] using sigmoid
            surprise = 1.0 / (1.0 + np.exp(-mse))

            return float(surprise)

        except Exception as e:
            logger.warning("Error computing MSE surprise: %s", e)
            return 0.5  # Default medium surprise

    def _compute_cosine(self, actual: Any, predicted: Any) -> SurpriseScore:
        """Compute surprise using cosine distance"""
        try:
            actual = np.array(actual)
            predicted = np.array(predicted)

            # Compute cosine similarity
            dot = np.dot(actual, predicted)
            norm_a = np.linalg.norm(actual)
            norm_p = np.linalg.norm(predicted)

            if norm_a == 0 or norm_p == 0:
                return 1.0  # Maximum surprise

            similarity = dot / (norm_a * norm_p)

            # Convert to distance (surprise)
            surprise = (1.0 - similarity) / 2.0  # Map [-1, 1] to [0, 1]

            return float(np.clip(surprise, 0.0, 1.0))

        except Exception as e:
            logger.warning("Error computing cosine surprise: %s", e)
            return 0.5

    def _compute_kl(self, actual: Any, predicted: Any) -> SurpriseScore:
        """Compute surprise using KL divergence"""
        try:
            # Ensure probability distributions
            actual = np.array(actual)
            predicted = np.array(predicted)

            # Normalize
            actual = actual / np.sum(actual)
            predicted = predicted / np.sum(predicted)

            # Add small epsilon to avoid log(0)
            eps = 1e-10
            actual = np.clip(actual, eps, 1.0)
            predicted = np.clip(predicted, eps, 1.0)

            # Compute KL divergence
            kl = np.sum(actual * np.log(actual / predicted))

            # Normalize to [0, 1]
            surprise = 1.0 - np.exp(-kl)

            return float(np.clip(surprise, 0.0, 1.0))

        except Exception as e:
            logger.warning("Error computing KL surprise: %s", e)
            return 0.5

    def compute_embedding_surprise(self, actual_emb: np.ndarray, predicted_emb: np.ndarray) -> SurpriseScore:
        """
        Compute surprise for embeddings

        Uses cosine distance by default

        Args:
            actual_emb: Actual embedding
            predicted_emb: Predicted embedding

        Returns:
            Surprise score
        """
        return self._compute_cosine(actual_emb, predicted_emb)

    def compute_code_surprise(
        self, code: str, expected_pattern: str, similarity_threshold: float = 0.7
    ) -> SurpriseScore:
        """
        Compute surprise for code patterns

        Args:
            code: Actual code
            expected_pattern: Expected pattern
            similarity_threshold: Threshold for low surprise

        Returns:
            Surprise score
        """
        # Simple string similarity
        code_lower = code.lower()
        pattern_lower = expected_pattern.lower()

        # Jaccard similarity
        code_tokens = set(code_lower.split())
        pattern_tokens = set(pattern_lower.split())

        if not code_tokens or not pattern_tokens:
            return 0.5

        intersection = code_tokens & pattern_tokens
        union = code_tokens | pattern_tokens

        similarity = len(intersection) / len(union)

        # Convert to surprise
        if similarity >= similarity_threshold:
            surprise = 0.0  # Low surprise
        else:
            surprise = 1.0 - similarity

        return float(np.clip(surprise, 0.0, 1.0))
