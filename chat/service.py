from sqlalchemy.orm import Session
from uuid import UUID
from sqlalchemy import or_

from chat.model import Conversation, Message


def get_or_create_conversation(db: Session, user_a: UUID, user_b: UUID):
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


def get_messages(db: Session, conversation_id: UUID):
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )
