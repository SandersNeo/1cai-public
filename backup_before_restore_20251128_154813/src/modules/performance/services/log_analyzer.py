"""Tech Log Analyzer Service."""

import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from ..domain.logs import (EventType, LogAnalysisResult, LogEntry,
                           PerformanceIssue)


class LogAnalyzerService:
    """Service for analyzing 1C tech logs."""

    def __init__(self):
        """Initialize log analyzer."""
        self.slow_query_threshold_ms = 1000
        self.memory_threshold_mb = 500.0

    def parse_log(self, file_path: str) -> List[LogEntry]:
        """
        Parse tech log file.

        Args:
            file_path: Path to tech log file

        Returns:
            List of log entries

        Raises:
            FileNotFoundError: If log file doesn't exist
            ValueError: If log format is invalid
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Log file not found: {file_path}")

        entries = []
        current_entry = {}
        line_number = 0

        with open(path, 'r', encoding='utf-8-sig') as f:
            for line in f:
                line_number += 1
                line = line.strip()

                if not line:
                    if current_entry:
                        entry = self._parse_entry(current_entry, line_number)
                        if entry:
                            entries.append(entry)
                        current_entry = {}
                    continue

                # Parse key-value pairs
                if '=' in line:
                    key, value = line.split('=', 1)
                    current_entry[key.strip()] = value.strip()

        # Don't forget last entry
        if current_entry:
            entry = self._parse_entry(current_entry, line_number)
            if entry:
                entries.append(entry)

        return entries

    def _parse_entry(self, data: dict, line_number: int) -> Optional[LogEntry]:
        """Parse single log entry from dict."""
        try:
