"""
Enhanced WebSocket API
Real-time updates for dashboards and notifications
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.services.real_time_service import real_time_manager
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

router = APIRouter()


@router.websocket("/ws/{topic}")
async def websocket_endpoint(websocket: WebSocket, topic: str):
    """
    WebSocket endpoint for real-time updates
    
    Topics:
    - dashboard_owner: Owner dashboard updates
    - dashboard_executive: Executive dashboard updates
    - dashboard_pm: PM dashboard updates
    - dashboard_developer: Developer dashboard updates  
    - dashboard_team_lead: Team Lead dashboard updates
    - dashboard_ba: BA dashboard updates
    - system: System-wide alerts
    - user_{id}: User-specific notifications
    
    Usage:
        const ws = new WebSocket('ws://localhost:8000/ws/dashboard_owner');
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            // Update dashboard with data
        };
    """
    
    await real_time_manager.connect(websocket, topic)
    
    try:
        while True:
            # Receive messages from client (ping/pong, subscriptions, etc.)
            data = await websocket.receive_json()
            
            # Handle client messages
            message_type = data.get('type')
            
            if message_type == 'ping':
                await real_time_manager.send_to_client(websocket, {
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                })
            
            elif message_type == 'subscribe':
                # Change topic subscription
                new_topic = data.get('topic')
                if new_topic:
                    await real_time_manager.disconnect(websocket)
                    await real_time_manager.connect(websocket, new_topic)
            
            # Add more message types as needed
            
    except WebSocketDisconnect:
        await real_time_manager.disconnect(websocket)
    except Exception as e:
        logger.error(
            "WebSocket error",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "topic": topic if 'topic' in locals() else None
            },
            exc_info=True
        )
        await real_time_manager.disconnect(websocket)


@router.get("/ws/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics"""
    return real_time_manager.get_stats()


