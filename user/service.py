from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from user.model import User
from friend.model import FriendRequest

def list_users_for_connections(db: Session, current_user_id):
    subquery = (
        db.query(FriendRequest)
        .filter(
            or_(
                and_(
                    FriendRequest.sender_id == current_user_id,
                    FriendRequest.receiver_id == User.id,
                ),
                and_(
                    FriendRequest.receiver_id == current_user_id,
                    FriendRequest.sender_id == User.id,
                ),
            )
        )
    )

    users = (
        db.query(User)
        .filter(User.id != current_user_id)
        .filter(~subquery.exists())
        .all()
    )

    return users