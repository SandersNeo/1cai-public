# [NEXUS IDENTITY] ID: -2873649329014550120 | DATE: 2025-11-19

"""Модель события для локального логгера."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List

ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
MAX_TEXT_LENGTH = 2048


def _validate_length(
    value: str, field_name: str, max_length: int = MAX_TEXT_LENGTH
) -> str:
    if len(value) > max_length:
        raise ValueError(
            f"{field_name} превышает допустимую длину {max_length} символов"
        )
    return value


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime(ISO_FORMAT)


@dataclass(slots=True)
class EventRecord:
    """Представление события, которое будет храниться локально и синхронизироваться."""

    event_type: str
    summary: str
    agent_id: str
    workspace_id: str
    payload: Dict[str, object] = field(default_factory=dict)
    risks: List[str] = field(default_factory=list)
    links: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_utc)
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        self.event_type = _validate_length(self.event_type, "event_type", 128)
        self.summary = _validate_length(self.summary, "summary")
        self.agent_id = _validate_length(self.agent_id, "agent_id", 128)
        self.workspace_id = _validate_length(
            self.workspace_id, "workspace_id", 128)
        self.created_at = self._normalize_timestamp(self.created_at)
        self.links = [self._normalize_link(link) for link in self.links]

    @staticmethod
    def _normalize_timestamp(value: str) -> str:
        try:
