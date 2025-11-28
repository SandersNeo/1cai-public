# [NEXUS IDENTITY] ID: -4145568411317632700 | DATE: 2025-11-19

"""
WebSocket API (Legacy)

DEPRECATED: This module has been refactored into Clean Architecture.
Use src.modules.websocket instead.

Backward compatibility proxy - imports are redirected to new module structure.
"""
from src.modules.websocket.api.routes import notify_user, router

__all__ = ["router", "notify_user"]
