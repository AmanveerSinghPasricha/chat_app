from fastapi import WebSocket, WebSocketDisconnect
from uuid import UUID
from sqlalchemy.orm import Session
from starlette import status

from chat.model import Message
from chat.ws_manager import ConnectionManager
from chat.permissions import is_conversation_member

manager = ConnectionManager()

def _clean_str(x):
    if x is None: return None
    x = str(x).strip()
    return x if x else None

def _clean_int(x):
    try: return int(x)
    except: return None

def _is_valid_uuid(x):
    try:
        UUID(str(x))
        return True
    except: return False

async def chat_websocket(
    websocket: WebSocket,
    conversation_id: UUID,
    db: Session,
    user_id: UUID,
):
    connected = False
    try:
        await websocket.accept()
        if not is_conversation_member(db, conversation_id, user_id):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await manager.connect(conversation_id, websocket)
        connected = True

        while True:
            data = await websocket.receive_json()
            # ... (keep all your cleaning and validation logic)

            msg = Message(
                conversation_id=conversation_id,
                sender_id=user_id,
                ciphertext=_clean_str(data.get("ciphertext")),
                nonce=_clean_str(data.get("nonce")),
                sender_device_id=UUID(str(data.get("sender_device_id"))),
                receiver_device_id=UUID(str(data.get("receiver_device_id"))),
                ephemeral_pub=_clean_str((data.get("header") or {}).get("ephemeral_pub")),
                signed_prekey_id=_clean_int((data.get("header") or {}).get("signed_prekey_id")),
                one_time_prekey_id=_clean_int((data.get("header") or {}).get("one_time_prekey_id")),
                message_type=_clean_str(data.get("message_type")) or "text",
                client_msg_id=_clean_str(data.get("client_msg_id")),
            )

            db.add(msg)
            db.commit()
            db.refresh(msg)

            # Broadcast uses to_dict() which now has fixed ISO formatting
            await manager.broadcast(conversation_id, msg.to_dict())

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print("WEBSOCKET ERROR:", e)
    finally:
        if connected:
            manager.disconnect(conversation_id, websocket)