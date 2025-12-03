from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List, Dict
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("collab-service")

app = FastAPI(title="1C AI Collaboration Service")

class ConnectionManager:
    """
    Manages WebSocket connections for real-time collaboration.
    Groups connections by 'room_id' (e.g., file path or session ID).
    """
    def __init__(self):
        # room_id -> List[WebSocket]
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)
        logger.info(f"Client connected to room {room_id}. Total: {len(self.active_connections[room_id])}")

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            if websocket in self.active_connections[room_id]:
                self.active_connections[room_id].remove(websocket)
                if not self.active_connections[room_id]:
                    del self.active_connections[room_id]
            logger.info(f"Client disconnected from room {room_id}")

    async def broadcast(self, message: str, room_id: str, sender: WebSocket):
        """Broadcasts message to all in room EXCEPT sender."""
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                if connection != sender:
                    try:
                        await connection.send_text(message)
                    except Exception as e:
                        logger.error(f"Failed to send message: {e}")

manager = ConnectionManager()

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await manager.connect(websocket, room_id)
    try:
        while True:
            data = await websocket.receive_text()
            # In a real Yjs implementation, we would parse and merge CRDT updates here
            # For now, we just act as a relay (broadcaster)
            await manager.broadcast(data, room_id, websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        # Optional: Broadcast "User Left" message
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, room_id)

@app.get("/health")
async def health_check():
    return {"status": "ok", "active_rooms": len(manager.active_connections)}
