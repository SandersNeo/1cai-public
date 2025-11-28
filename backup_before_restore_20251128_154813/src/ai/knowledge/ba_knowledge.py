# [NEXUS IDENTITY] ID: -7959207762534172851 | DATE: 2025-11-19

from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path
from typing import Dict, List, Sequence


class BAKnowledgeBase:
    """Lightweight reader for BA pipeline snapshots."""

    def __init__(self, base_dir: str | Path | None = None) -> None:
        self.base_dir = Path(
            base_dir or os.getenv("BA_PIPELINE_OUTPUT_DIR", "data/ba_intel")
        )

    def _latest_records(self, collector: str) -> List[Dict]:
        collector_dir = self.base_dir / collector
        if not collector_dir.exists():
            return []
        dated_dirs = sorted(
            [p for p in collector_dir.iterdir() if p.is_dir()], reverse=True
        )
        records: List[Dict] = []
        for dated in dated_dirs:
            for json_file in sorted(dated.glob("*.json"), reverse=True):
                try:
