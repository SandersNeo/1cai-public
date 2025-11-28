"""
BPMN Generator Service

Сервис для генерации BPMN 2.0 диаграмм из текстового описания процессов.
"""

import html
import re
from datetime import datetime
from typing import Any, Dict, List

from src.modules.business_analyst.domain.exceptions import BPMNGenerationError
from src.modules.business_analyst.domain.models import (BPMNDiagram,
                                                        DecisionPoint)
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class BPMNGenerator:
    """
    Сервис генерации BPMN диаграмм

    Features:
    - BPMN 2.0 XML generation
    - Mermaid diagram generation
    - Actor/activity extraction
    - Decision points extraction
    """

    def __init__(self):
        """Initialize BPMN generator"""
        self.default_lane = "System"
        self._max_label_length = 120
        self._mermaid_translation = str.maketrans({
            "[": "(",
            "]": ")",
            "{": "(",
            "}": ")",
            "<": " ",
            ">": " ",
            "`": " ",
            '"': " ",
            "'": " ",
        })

    async def generate_bpmn(
        self,
        process_description: str
    ) -> BPMNDiagram:
        """
        Генерация BPMN диаграммы из описания процесса

        Args:
            process_description: Текстовое описание процесса

        Returns:
            BPMNDiagram с XML, Mermaid и метаданными
        """
        try:
