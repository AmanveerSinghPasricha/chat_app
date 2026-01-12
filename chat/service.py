from sqlalchemy.orm import Session
from uuid import UUID
from chat.model import Conversation
from friend.model import FriendRequest
from sqlalchemy import or_
from user.model import User
from chat.model import Message

def get_messages(db: Session, conversation_id: UUID):
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )

def are_friends(db: Session, user_a: UUID, user_b: UUID) -> bool:
    return (
        db.query(FriendRequest)
        .filter(
            or_(
                (FriendRequest.sender_id == user_a) & (FriendRequest.receiver_id == user_b),
                (FriendRequest.sender_id == user_b) & (FriendRequest.receiver_id == user_a),
            ),
            FriendRequest.status == "accepted",
        )
        .first()
        is not None
    )

def get_or_create_conversation(
    db: Session,
    user_a: UUID,
    user_b: UUID,
):
    # ensure consistent ordering
    u1, u2 = sorted([user_a, user_b])

    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.user1_id == u1,
            Conversation.user2_id == u2,
        )
        .first()
    )

    if conversation:
        return conversation

    conversation = Conversation(user1_id=u1, user2_id=u2)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation

def get_friends(db: Session, user_id):
    friends = (
        db.query(User)
        .join(
            FriendRequest,
            or_(
                (FriendRequest.sender_id == User.id),
                (FriendRequest.receiver_id == User.id),
            ),
        )
        .filter(
            FriendRequest.status == "accepted",
            User.id != user_id,
            or_(
                FriendRequest.sender_id == user_id,
                FriendRequest.receiver_id == user_id,
            ),
        )
        .all()
    )

    return friends

def list_conversations(db: Session, user_id: UUID):
    return (
        db.query(Conversation)
        .filter(
            or_(
                Conversation.user1_id == user_id,
                Conversation.user2_id == user_id,
            )
        )
        .order_by(Conversation.updated_at.desc())
        .all()
    )