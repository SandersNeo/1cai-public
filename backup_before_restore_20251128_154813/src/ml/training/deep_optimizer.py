"""
Deep Optimizer

Advanced optimizer with Nested Learning principles.
Implements L2-regression loss and nested momentum.
"""

import time
from typing import Any, Callable, Dict, List, Optional

import numpy as np
import torch
import torch.nn as nn

from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class DeepOptimizer:
    """
    Deep optimizer with Nested Learning principles

    Features:
    - L2-regression loss (better than dot-product)
    - Nested momentum (multi-scale updates)
    - Retry logic for robustness
    - Adaptive learning rates

    Based on Nested Learning paper recommendations.

    Example:
        >>> model = MyModel()
        >>> optimizer = DeepOptimizer(
        ...     model=model,
        ...     loss_fn="l2_regression",
        ...     momentum_type="nested"
        ... )
        >>> for batch in dataloader:
        ...     loss = optimizer.step(batch['data'], batch['labels'])
        ...     print(f"Loss: {loss:.4f}")
    """

    def __init__(
        self,
        model: nn.Module,
        loss_fn: str = "l2_regression",
        momentum_type: str = "nested",
        learning_rate: float = 0.001,
        max_retries: int = 3,
        weight_decay: float = 0.0001,
    ):
        """
        Initialize deep optimizer

        Args:
            model: PyTorch model
            loss_fn: Loss function type ("l2_regression" | "mse" | "cross_entropy")
            momentum_type: "standard" | "nested"
            learning_rate: Base learning rate
            max_retries: Max retry attempts on failure
            weight_decay: L2 regularization
        """
        self.model = model
        self.loss_fn_type = loss_fn
        self.momentum_type = momentum_type
        self.learning_rate = learning_rate
        self.max_retries = max_retries

        # Optimizer
        self.optimizer = torch.optim.Adam(
            model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay)

        # Nested momentum buffers
        if momentum_type == "nested":
            self.momentum_buffers = {
                "fast": [],  # Update every step
                "medium": [],  # Update every 10 steps
                "slow": [],  # Update every 100 steps
            }
            self.step_count = 0

        # Learning rate scheduler
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode="min", factor=0.5, patience=10, verbose=True
        )

        # Statistics
        self.stats = {
            "total_steps": 0,
            "total_retries": 0,
            "avg_loss": 0.0,
            "best_loss": float("inf"),
            "convergence_steps": 0,
        }

        logger.info(
            f"Created DeepOptimizer with {loss_fn} loss and {momentum_type} momentum")

    def l2_regression_loss(
            self,
            predictions: torch.Tensor,
            targets: torch.Tensor) -> torch.Tensor:
        """
        L2-regression loss (recommended by Nested Learning)

        Better than dot-product for continual learning.
        Prevents catastrophic forgetting.

        Args:
            predictions: Model predictions
            targets: Target values

        Returns:
            L2 loss
        """
        return torch.mean((predictions - targets) ** 2)

    def step(
            self,
            batch_data: torch.Tensor,
            batch_labels: torch.Tensor,
            return_predictions: bool = False) -> float:
        """
        Perform optimization step with retry logic

        Args:
            batch_data: Input batch
            batch_labels: Target labels
            return_predictions: Whether to return predictions

        Returns:
            Loss value (or tuple of loss and predictions)
        """
        for attempt in range(self.max_retries):
            try:
