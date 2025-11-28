# [NEXUS IDENTITY] ID: 3295439782080269364 | DATE: 2025-11-19

"""
BSL Dataset Builder
Расширенный builder для создания обучающего dataset из разных источников
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class BSLDatasetBuilder:
    """Расширенный builder для BSL dataset"""

    def __init__(self, output_dir: str = "datasets/bsl"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.examples = []
        self.stats = {"total_examples": 0, "sources": {}, "categories": {}}

    async def build_from_postgres(self, db_connection):
        """
        Извлечение примеров из PostgreSQL

        Queries:
        - functions с description и code_preview
        - procedures с examples
        - Common patterns
        """
        try:
