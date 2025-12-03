import json
import os
import sys
import logging
from datetime import datetime
from typing import List

# Add project root to path
sys.path.append(os.getcwd())

from src.ai.rltf.schemas import Trajectory

logger = logging.getLogger(__name__)


class MockTrainer:
    """
    Simulates the RLTF Training Loop (Policy Gradient).

    In a real implementation, this would:
    1. Load a Pre-trained LLM (e.g., Llama-3).
    2. Convert Trajectories to Tensor Batches.
    3. Compute Policy Gradient Loss: -sum(log_prob(action) * reward).
    4. Backpropagate and Update Weights.

    Here, we simulate the mechanics to prove the architecture.
    """

    def __init__(self, data_path: str = "data/rltf/trajectories.jsonl", model_path: str = "models/v1"):
        self.data_path = data_path
        self.model_path = model_path
        self._ensure_paths()

    def _ensure_paths(self):
        os.makedirs(self.model_path, exist_ok=True)

    def load_data(self) -> List[Trajectory]:
        """Loads trajectories from disk."""
        trajectories = []
        if not os.path.exists(self.data_path):
            logger.warning(f"No training data found at {self.data_path}")
            return []

        with open(self.data_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    trajectories.append(Trajectory(**data))
                except Exception as e:
                    logger.error(f"Failed to parse trajectory: {e}")

        logger.info(f"Loaded {len(trajectories)} trajectories.")
        return trajectories

    def train_epoch(self):
        """Runs one epoch of 'training'."""
        trajectories = self.load_data()
        if not trajectories:
            return

        total_reward = 0.0
        loss = 0.0

        for t in trajectories:
            r = t.reward.value
            total_reward += r
            # Mock Loss Calculation:
            # If reward is high, loss should be low.
            # Loss = 1 / (Reward + epsilon) (Simplified)
            loss += 1.0 / (r + 101.0)  # Shift to avoid div by zero if reward is -100

        avg_reward = total_reward / len(trajectories)
        avg_loss = loss / len(trajectories)

        logger.info(f"Epoch Complete. Avg Reward: {avg_reward:.2f}, Mock Loss: {avg_loss:.4f}")

        self._save_checkpoint(avg_reward)

    def _save_checkpoint(self, metric: float):
        """Saves a mock model checkpoint."""
        version_file = os.path.join(self.model_path, "version.json")
        current_version = 0

        if os.path.exists(version_file):
            with open(version_file, "r") as f:
                data = json.load(f)
                current_version = data.get("version", 0)

        new_version = current_version + 1

        checkpoint = {
            "version": new_version,
            "timestamp": datetime.now().isoformat(),
            "metric": metric,
            "status": "trained",
        }

        with open(version_file, "w") as f:
            json.dump(checkpoint, f, indent=2)

        logger.info(f"Model upgraded to v{new_version}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    trainer = MockTrainer()
    trainer.train_epoch()
