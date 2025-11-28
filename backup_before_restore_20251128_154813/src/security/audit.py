# [NEXUS IDENTITY] ID: -8013991353093750602 | DATE: 2025-11-19

"""Security audit logging utilities."""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Optional


class AuditLogger:
    """Append-only JSONL audit logger."""

    def __init__(self, log_path: Optional[Path] = None) -> None:
        env_path = os.getenv("AUDIT_LOG_PATH", "logs/security_audit.log")
        self._path = log_path or Path(env_path)
        self._lock = Lock()

    @property
    def path(self) -> Path:
        return self._path

    def log_action(
        self,
        *,
        actor: str,
        action: str,
        target: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        timestamp = datetime.now(timezone.utc)
        entry = {
            "timestamp": timestamp.isoformat(timespec="seconds"),
            "actor": actor,
            "action": action,
            "target": target,
            "metadata": metadata or {},
        }

        self._path.parent.mkdir(parents=True, exist_ok=True)

        with self._lock:
            with self._path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

        try:
