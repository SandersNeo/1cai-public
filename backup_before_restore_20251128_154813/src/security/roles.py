# [NEXUS IDENTITY] ID: -8251860666297395792 | DATE: 2025-11-19

"""Helpers for managing user roles & permissions from the database."""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Optional

if TYPE_CHECKING:  # pragma: no cover
    from src.security.auth import CurrentUser


async def enrich_user_from_db(user: "CurrentUser") -> "CurrentUser":
    try:
