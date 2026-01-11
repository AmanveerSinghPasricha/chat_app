from fastapi import APIRouter, WebSocket
from uuid import UUID
from chat.websocket import chat_websocket

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.websocket("/ws/{conversation_id}")
async def chat_ws_endpoint(
    websocket: WebSocket,
    conversation_id: UUID,
):
    await chat_websocket(websocket, conversation_id)
