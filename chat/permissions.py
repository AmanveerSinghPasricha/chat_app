from sqlalchemy.orm import Session
from chat.model import Conversation
from uuid import UUID

def is_conversation_member(
    db: Session,
    conversation_id: UUID,
    user_id: UUID,
) -> bool:
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id)
        .first()
    )

    if not conversation:
        return False

    return user_id in (conversation.user1_id, conversation.user2_id)
