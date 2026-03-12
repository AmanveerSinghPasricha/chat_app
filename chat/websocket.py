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

def _clean_int(x):
    try:
        return int(x)
    except Exception:
        return None

def _is_valid_uuid(x):
    try:
        UUID(str(x))
        return True
    except Exception:
        return False

async def chat_websocket(websocket: WebSocket, conversation_id: UUID):
    db: Session = SessionLocal()

    try:
        user_id = await authenticate_ws(websocket)
        if not user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        if not is_conversation_member(db, conversation_id, user_id):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await manager.connect(conversation_id, websocket)

        while True:
            data = await websocket.receive_json()

            ciphertext = _clean_str(data.get("ciphertext"))
            nonce = _clean_str(data.get("nonce"))
            sender_device_id = data.get("sender_device_id")
            receiver_device_id = data.get("receiver_device_id")

            header = data.get("header") or {}
            client_msg_id = _clean_str(data.get("client_msg_id"))

            if not ciphertext or not nonce:
                continue

            # Never log ciphertext or plaintext
            # Enforce replay protection server-side by client_msg_id uniqueness per conversation
            if client_msg_id:
                existing = (
                    db.query(Message)
                    .filter(
                        Message.conversation_id == conversation_id,
                        Message.client_msg_id == client_msg_id,
                    )
                    .first()
                )
                if existing:
                    continue

            # Validate device IDs (must be UUID)
            if not _is_valid_uuid(sender_device_id) or not _is_valid_uuid(receiver_device_id):
                continue

            ephemeral_pub = _clean_str(header.get("ephemeral_pub"))

            msg = Message(
                conversation_id=conversation_id,
                sender_id=user_id,
                ciphertext=ciphertext,
                nonce=nonce,
                sender_device_id=UUID(str(sender_device_id)),
                receiver_device_id=UUID(str(receiver_device_id)),
                ephemeral_pub=ephemeral_pub,
                signed_prekey_id=_clean_int(header.get("signed_prekey_id")),
                one_time_prekey_id=_clean_int(header.get("one_time_prekey_id")),
                message_type=_clean_str(data.get("message_type")) or "text",
                client_msg_id=client_msg_id,
            )

            db.add(msg)
            db.commit()
            db.refresh(msg)

            await manager.broadcast(conversation_id, msg.to_dict())

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(conversation_id, websocket)
        db.close()
