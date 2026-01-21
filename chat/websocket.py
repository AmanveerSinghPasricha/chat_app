from fastapi import WebSocket, WebSocketDisconnect
from uuid import UUID
from sqlalchemy.orm import Session
from starlette import status

from core.database import SessionLocal
from chat.model import Message
from chat.ws_manager import ConnectionManager
from chat.security import authenticate_ws
from chat.permissions import is_conversation_member

manager = ConnectionManager()

def _clean_str(x):
    if x is None:
        return None
    x = str(x).strip()
    return x if x else None

async def chat_websocket(websocket: WebSocket, conversation_id: UUID):
    token = websocket.query_params.get("token")

    # ---- AUTH (before accept) ----
    try:
        user_id = authenticate_ws(token)
    except Exception:
        return

    await websocket.accept()
    db: Session = SessionLocal()

    try:
        if not is_conversation_member(db, conversation_id, user_id):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await manager.connect(conversation_id, websocket)

        while True:
            data = await websocket.receive_json()

            ciphertext = data.get("ciphertext")
            nonce = data.get("nonce")
            sender_device_id = data.get("sender_device_id")
            receiver_device_id = data.get("receiver_device_id")
            message_type = data.get("message_type", "text")

            header = data.get("header") or {}
            client_msg_id = data.get("client_msg_id")

            if not ciphertext or not nonce or not sender_device_id or not receiver_device_id:
                continue

            # IMPORTANT: never store empty string
            ephemeral_pub = _clean_str(header.get("ephemeral_pub"))

            msg = Message(
                conversation_id=conversation_id,
                sender_id=user_id,
                ciphertext=ciphertext,
                nonce=nonce,
                sender_device_id=sender_device_id,
                receiver_device_id=receiver_device_id,
                ephemeral_pub=ephemeral_pub,
                signed_prekey_id=header.get("signed_prekey_id"),
                one_time_prekey_id=header.get("one_time_prekey_id"),
                message_type=message_type,
                client_msg_id=client_msg_id,
            )

            db.add(msg)
            db.commit()
            db.refresh(msg)

            await manager.broadcast(
                conversation_id,
                {
                    "id": str(msg.id),
                    "client_msg_id": msg.client_msg_id,
                    "conversation_id": str(conversation_id),
                    "sender_id": str(user_id),
                    "ciphertext": msg.ciphertext,
                    "nonce": msg.nonce,
                    "sender_device_id": str(msg.sender_device_id),
                    "receiver_device_id": str(msg.receiver_device_id),
                    "header": {
                        "ephemeral_pub": msg.ephemeral_pub,
                        "signed_prekey_id": msg.signed_prekey_id,
                        "one_time_prekey_id": msg.one_time_prekey_id,
                    },
                    "message_type": msg.message_type,
                    "created_at": msg.created_at.isoformat(),
                },
            )

    except WebSocketDisconnect:
        manager.disconnect(conversation_id, websocket)

    finally:
        db.close()
