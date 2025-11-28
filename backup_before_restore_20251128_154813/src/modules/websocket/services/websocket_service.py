import asyncio
import re
from datetime import datetime
from typing import Dict

from fastapi import WebSocket

from src.services.websocket_manager import manager
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class WebSocketService:
    """Service for WebSocket operations."""

    async def handle_connection(self, websocket: WebSocket, user_id: str):
        """Handle WebSocket connection lifecycle."""
        # Input validation
        if not user_id or len(user_id) > 200:
            logger.warning(
                f"Invalid user_id for WebSocket connection: {user_id}",
                extra={"user_id": user_id},
            )
            await websocket.close(code=1008, reason="Invalid user_id")
            return

        # Sanitize user_id
        if not re.match(r"^[a-zA-Z0-9_.-]+$", user_id):
            logger.warning(
                f"Invalid characters in user_id: {user_id}", extra={
                    "user_id": user_id})
            await websocket.close(code=1008, reason="Invalid user_id format")
            return

        try:
