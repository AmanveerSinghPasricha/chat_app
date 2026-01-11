from sqlalchemy.orm import Session
from uuid import UUID
from chat.model import Conversation
from friend.model import FriendRequest
from sqlalchemy import or_

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
