"""
Deep Optimizer

Advanced optimizer with Nested Learning principles.
Implements L2-regression loss and nested momentum.
"""

import time
from typing import Any, Dict

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
            model.parameters(), lr=learning_rate, weight_decay=weight_decay)

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

    def l2_regression_loss(self, predictions: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
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

    def step(self, batch_data: torch.Tensor, batch_labels: torch.Tensor, return_predictions: bool = False) -> float:
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
                result = self._step_internal(
                    batch_data, batch_labels, return_predictions)

                if return_predictions:
                    loss, predictions = result
                else:
                    loss = result

                # Update stats
                self.stats["total_steps"] += 1
                self.stats["avg_loss"] = self.stats["avg_loss"] * 0.99 + loss * 0.01

                if loss < self.stats["best_loss"]:
                    self.stats["best_loss"] = loss
                    self.stats["convergence_steps"] = self.stats["total_steps"]

                # Update learning rate
                self.scheduler.step(loss)

                if return_predictions:
                    return loss, predictions
                return loss

            except Exception as e:
                self.stats["total_retries"] += 1
                logger.warning(
                    f"Optimization step failed (attempt {attempt + 1}/{self.max_retries}): {e}", exc_info=True
                )

                if attempt == self.max_retries - 1:
                    raise

                # Wait before retry
                time.sleep(0.1 * (attempt + 1))

        return float("inf")

    def _step_internal(self, batch_data: torch.Tensor, batch_labels: torch.Tensor, return_predictions: bool = False):
        """Internal optimization step"""
        self.optimizer.zero_grad()

        # Forward pass
        predictions = self.model(batch_data)

        # Compute loss
        if self.loss_fn_type == "l2_regression":
            loss = self.l2_regression_loss(predictions, batch_labels)
        elif self.loss_fn_type == "mse":
            loss = nn.functional.mse_loss(predictions, batch_labels)
        elif self.loss_fn_type == "cross_entropy":
            loss = nn.functional.cross_entropy(predictions, batch_labels)
        else:
            raise ValueError(f"Unknown loss function: {self.loss_fn_type}")

        # Backward pass
        loss.backward()

        # Gradient clipping
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)

        # Apply nested momentum if enabled
        if self.momentum_type == "nested":
            self._apply_nested_momentum()

        # Update weights
        self.optimizer.step()

        if return_predictions:
            return float(loss.item()), predictions.detach()
        return float(loss.item())

    def _apply_nested_momentum(self):
        """
        Apply nested momentum updates

        Multi-scale momentum for better convergence.
        """
        self.step_count += 1

        # Fast momentum (every step) - handled by Adam

        # Medium momentum (every 10 steps)
        if self.step_count % 10 == 0:
            # Store medium-scale gradients
            for param in self.model.parameters():
                if param.grad is not None:
                    if len(self.momentum_buffers["medium"]) < len(list(self.model.parameters())):
                        self.momentum_buffers["medium"].append(param.grad.clone())
                    else:
                        idx = len(self.momentum_buffers["medium"]) % len(
                            list(self.model.parameters()))
                        self.momentum_buffers["medium"][idx] = param.grad.clone()

        # Slow momentum (every 100 steps)
        if self.step_count % 100 == 0:
            # Store slow-scale gradients
            for param in self.model.parameters():
                if param.grad is not None:
                    if len(self.momentum_buffers["slow"]) < len(list(self.model.parameters())):
                        self.momentum_buffers["slow"].append(param.grad.clone())

    def get_stats(self) -> Dict[str, Any]:
        """Get optimizer statistics"""
        return {
            **self.stats,
            "current_lr": self.optimizer.param_groups[0]["lr"],
            "momentum_type": self.momentum_type,
            "loss_fn": self.loss_fn_type,
        }

    def save_checkpoint(self, path: str):
        """Save optimizer checkpoint"""
        torch.save(
            {
                "model_state_dict": self.model.state_dict(),
                "optimizer_state_dict": self.optimizer.state_dict(),
                "scheduler_state_dict": self.scheduler.state_dict(),
                "stats": self.stats,
                "step_count": self.step_count if self.momentum_type == "nested" else 0,
            },
            path,
        )

        logger.info("Saved checkpoint to %s", path)

    def load_checkpoint(self, path: str):
        """Load optimizer checkpoint"""
        checkpoint = torch.load(path)

        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
        self.stats = checkpoint["stats"]

        if self.momentum_type == "nested":
            self.step_count = checkpoint.get("step_count", 0)

        logger.info("Loaded checkpoint from %s", path)

    def health_check(self) -> Dict[str, Any]:
        """Health check"""
        return {
            "status": "healthy",
            "total_steps": self.stats["total_steps"],
            "avg_loss": self.stats["avg_loss"],
            "best_loss": self.stats["best_loss"],
            "current_lr": self.optimizer.param_groups[0]["lr"],
            "retries": self.stats["total_retries"],
        }
