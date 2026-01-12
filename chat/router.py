from fastapi import APIRouter, Depends, HTTPException, status, WebSocket
from uuid import UUID
from chat.websocket import chat_websocket
from sqlalchemy.orm import Session
from core.deps import get_db, get_current_user
from core.utils import success_response
from chat.service import get_or_create_conversation, are_friends, list_conversations, get_messages
from user.model import User
from chat.schema import ConversationResponse
from core.response import ApiResponse
from chat.schema import MessageResponse
from chat.model import Conversation

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

@router.get(
    "/chat/conversations",
    response_model=ApiResponse[list[ConversationResponse]],
)
def get_conversations(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    conversations = list_conversations(db, current_user.id)

    return success_response(
        data=conversations,
        message="Conversations fetched",
    )

@router.get(
    "/messages/{conversation_id}",
    response_model=ApiResponse[list[MessageResponse]],
)
def fetch_messages(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = db.query(Conversation).get(conversation_id)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if current_user.id not in (conversation.user1_id, conversation.user2_id):
        raise HTTPException(status_code=403, detail="Not authorized")

    messages = get_messages(db, conversation_id)

    return success_response(
        data=messages,
        message="Chat history fetched",
    )