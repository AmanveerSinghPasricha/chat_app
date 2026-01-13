from typing import Dict, List
from fastapi import WebSocket
from uuid import UUID

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[UUID, list[WebSocket]] = {}

    async def connect(self, conversation_id: UUID, websocket: WebSocket):
        self.active_connections.setdefault(conversation_id, []).append(websocket)

    def disconnect(self, conversation_id: UUID, websocket: WebSocket):
        self.active_connections.get(conversation_id, []).remove(websocket)

    async def broadcast(self, conversation_id: UUID, message: dict):
        for ws in self.active_connections.get(conversation_id, []):
            await ws.send_json(message)
