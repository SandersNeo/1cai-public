# [NEXUS IDENTITY] ID: 969984806280980791 | DATE: 2025-11-19

"""
LoRA Fine-Tuning Pipeline
Обучение Qwen3-Coder на BSL с использованием LoRA
"""

from pathlib import Path

from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class LoRAFineTuner:
    """
    LoRA Fine-Tuning для BSL

    Обучает Qwen3-Coder понимать BSL лучше
    Используя LoRA (Low-Rank Adaptation) - эффективный метод
    """

    def __init__(
        self,
        base_model: str = "Qwen/Qwen2.5-Coder-7B-Instruct",
        output_dir: str = "models/qwen-bsl-lora",
    ):
        self.base_model = base_model
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Check dependencies
        self._check_dependencies()

    def _check_dependencies(self):
        """Проверка необходимых библиотек"""

        required = ["transformers", "peft", "torch", "datasets"]
        missing = []

        for lib in required:
            try:
