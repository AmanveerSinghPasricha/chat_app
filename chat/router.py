from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, Query
from sqlalchemy.orm import Session
from uuid import UUID
from core.deps import get_db, get_current_user
from core.security import decode_access_token
from core.utils import success_response
from core.response import ApiResponse
from user.model import User
from chat.websocket import chat_websocket
from chat.service import get_or_create_conversation, list_conversations, get_messages
from chat.schema import ConversationResponse, EncryptedMessageOut
from friend.service import are_friends

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/conversations/{friend_id}")
def start_conversation(
    friend_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if str(friend_id) == str(current_user.id):
        raise HTTPException(status_code=400, detail="Cannot chat with yourself")

    if not are_friends(db, current_user.id, friend_id):
        raise HTTPException(status_code=403, detail="Not friends with this user")

    conversation = get_or_create_conversation(db, current_user.id, friend_id)
    return success_response(data={"conversation_id": str(conversation.id)}, message="Ready")

@router.websocket("/ws/{conversation_id}")
async def chat_ws_endpoint(
    websocket: WebSocket,
    conversation_id: UUID,
    token: str = Query(None), 
    db: Session = Depends(get_db),
):
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    try:
        from core.security import decode_access_token
        user_id_str = decode_access_token(token)
        user = db.query(User).filter(User.id == UUID(user_id_str), User.is_active == True).first()
        
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # We pass the user.id we found to the websocket handler
        await chat_websocket(websocket, conversation_id, db, user_id=user.id)
    except Exception as e:
        print(f"WS Auth Error: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)

@router.get("/conversations", response_model=ApiResponse[list[ConversationResponse]])
def get_conversations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(data=list_conversations(db, current_user.id), message="Fetched")

@router.get("/messages/{conversation_id}", response_model=ApiResponse[list[EncryptedMessageOut]])
def fetch_messages(conversation_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    messages = get_messages(db, conversation_id)
    return success_response(data=messages, message="History fetched")