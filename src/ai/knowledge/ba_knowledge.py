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
                    payload = json.loads(json_file.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    continue
                records.extend(payload.get("records", []))
            if records:
                break
        return records

    def get_top_market_skills(self, limit: int = 10) -> List[Dict[str, object]]:
        records = self._latest_records("job_market")
        counter: Counter[str] = Counter()
        for record in records:
            for skill in record.get("skills", []):
                counter[skill] += 1
        return [
            {"skill": skill, "mentions": count}
            for skill, count in counter.most_common(limit)
        ]

    def get_conference_topics(self, limit: int = 5) -> List[Dict[str, str]]:
        records = self._latest_records("conference_digest")
        topics: List[Dict[str, str]] = []
        for record in records[:limit]:
            topics.append(
                {
                    "event": record.get("event", "Unknown"),
                    "topic": record.get("topic", ""),
                    "link": record.get("link", ""),
                    "date": record.get("date"),
                }
            )
        return topics

    def get_usage_highlights(self, limit: int = 5) -> List[Dict[str, object]]:
        records = self._latest_records("internal_usage")
        highlights: List[Dict[str, object]] = []
        for record in records[:limit]:
            highlights.append(
                {
                    "feature": record.get("feature"),
                    "count": record.get("count"),
                    "timestamp": record.get("timestamp"),
                }
            )
        return highlights

    def get_domains(self) -> Sequence[str]:
        records = self._latest_records("job_market")
        return sorted(
            {
                record.get("platform", "general")
                for record in records
                if record.get("platform")
            }
        )
