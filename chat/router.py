from fastapi import APIRouter, Depends, HTTPException, status, WebSocket
from uuid import UUID
from chat.websocket import chat_websocket
from sqlalchemy.orm import Session
from core.deps import get_db, get_current_user
from core.utils import success_response
from chat.service import get_or_create_conversation, are_friends
from user.model import User

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/conversations/{friend_id}")
def start_conversation(
    friend_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not are_friends(db, current_user.id, friend_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not friends with this user",
        )

    conversation = get_or_create_conversation(
        db=db,
        user_a=current_user.id,
        user_b=friend_id,
    )

    return success_response(
        data={"conversation_id": str(conversation.id)},
        message="Conversation ready",
    )

@router.websocket("/ws/{conversation_id}")
async def chat_ws_endpoint(
    websocket: WebSocket,
    conversation_id: UUID,
):
    await chat_websocket(websocket, conversation_id)