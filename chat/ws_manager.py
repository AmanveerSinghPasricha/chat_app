from typing import Dict, List
from fastapi import WebSocket
from uuid import UUID

class ConnectionManager:
    def __init__(self):
        # conversation_id -> list of websockets
        self.active_connections: Dict[UUID, List[WebSocket]] = {}

    async def connect(self, conversation_id: UUID, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(conversation_id, []).append(websocket)

    def disconnect(self, conversation_id: UUID, websocket: WebSocket):
        self.active_connections[conversation_id].remove(websocket)

    async def broadcast(self, conversation_id: UUID, message: dict):
        for ws in self.active_connections.get(conversation_id, []):
            await ws.send_json(message)
