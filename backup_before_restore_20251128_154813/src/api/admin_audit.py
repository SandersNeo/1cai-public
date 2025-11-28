# [NEXUS IDENTITY] ID: -7781790871916911284 | DATE: 2025-11-19

"""Admin endpoints for viewing security audit log."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from src.security import CurrentUser, require_roles

router = APIRouter(prefix="/admin/audit", tags=["admin", "audit"])


class AuditEntry(BaseModel):
    id: int
    timestamp: str
    actor: str
    action: str
    target: Optional[str]
    metadata: dict


class AuditLogResponse(BaseModel):
    items: list[AuditEntry]
    total: int
    limit: int
    offset: int


async def _fetch_audit_entries(
    limit: int,
    offset: int,
    actor: Optional[str],
    action: Optional[str],
) -> tuple[list[AuditEntry], int]:
    try:
