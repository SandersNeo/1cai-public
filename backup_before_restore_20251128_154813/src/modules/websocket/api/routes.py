from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.modules.websocket.services.websocket_service import WebSocketService

router = APIRouter()


@router.websocket("/ws/notifications/{user_id}")
async def websocket_notifications(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time notifications."""
    service = WebSocketService()
    try:
        logger = logging.getLogger(__name__)
        logger.error("Error in try block", exc_info=True)


# Helper function for external use
async def notify_user(user_id: str, notification_type: str, data: dict):
    """Send notification to user via WebSocket."""
    service = WebSocketService()
    await service.notify_user(user_id, notification_type, data)
