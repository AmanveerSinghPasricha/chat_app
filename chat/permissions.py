from sqlalchemy.orm import Session
from chat.model import Conversation
from uuid import UUID

def is_conversation_member(
    db: Session,
    conversation_id: UUID,
    user_id: UUID,
) -> bool:

    print(f"DEBUG PERMISSION: Checking membership")
    print(f"  Session ID: {id(db)}")
    print(f"  Conversation ID: {conversation_id}")
    print(f"  User ID: {user_id}")
    
    # First, let's see all conversations in the database
    all_convs = db.query(Conversation).all()
    print(f"  Total conversations in DB: {len(all_convs)}")
    for c in all_convs:
        print(f"    Conv {c.id}: user1={c.user1_id}, user2={c.user2_id}")
    
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id)
        .first()
    )

    print(f"  Conversation found: {conversation is not None}")
    
    if not conversation:
        print("  FAILED: Conversation not found in database")
        return False

    print(f"  Conv user1_id: {conversation.user1_id} (type: {type(conversation.user1_id)})")
    print(f"  Conv user2_id: {conversation.user2_id} (type: {type(conversation.user2_id)})")
    print(f"  Checking user_id: {user_id} (type: {type(user_id)})")
    
    # Explicit equality check (most reliable)
    is_user1 = str(conversation.user1_id) == str(user_id)
    is_user2 = str(conversation.user2_id) == str(user_id)
    
    print(f"  Is user1? {is_user1}")
    print(f"  Is user2? {is_user2}")
    
    result = is_user1 or is_user2
    print(f"  RESULT: {result}")
    
    return result