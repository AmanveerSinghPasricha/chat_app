from fastapi import WebSocket, WebSocketDisconnect
from uuid import UUID
from sqlalchemy.orm import Session
from core.database import SessionLocal
from chat.model import Message
from chat.ws_manager import ConnectionManager
from chat.security import authenticate_ws
from chat.permissions import is_conversation_member

manager = ConnectionManager()

async def chat_websocket(
    websocket: WebSocket,
    conversation_id: UUID,
):
    token = websocket.query_params.get("token")

    # 1️⃣ Authenticate
    user_id = authenticate_ws(token)

    db: Session = SessionLocal()

    # 2️⃣ Authorize
    if not is_conversation_member(db, conversation_id, user_id):
        await websocket.close(code=1008)
        db.close()
        return

    # 3️⃣ Connect
    await manager.connect(conversation_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            content = data.get("content")

            if not content:
                continue

            # 4️⃣ Persist message
            message = Message(
                conversation_id=conversation_id,
                sender_id=user_id,
                content=content,
            )
            db.add(message)
            db.commit()
            db.refresh(message)

            # 5️⃣ Broadcast
            await manager.broadcast(
                conversation_id,
                {
                    "id": str(message.id),
                    "conversation_id": str(conversation_id),
                    "sender_id": str(user_id),
                    "content": message.content,
                    "created_at": message.created_at.isoformat(),
                },
            )

    except WebSocketDisconnect:
        manager.disconnect(conversation_id, websocket)
    finally:
        db.close()
