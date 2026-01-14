from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from user.model import User
from friend.model import FriendRequest
from fastapi import HTTPException, status
from datetime import datetime
from user.schema import UpdateProfileRequest
from core.security import verify_password, hash_password

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

def delete_user_account(db: Session, user: User):
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account already deleted",
        )

    user.is_active = False
    user.deleted_at = datetime.utcnow()
    db.commit()

def update_user_profile(
    db: Session,
    user: User,
    payload: UpdateProfileRequest,
) -> User:
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update deleted account",
        )

    if payload.username is not None:
        user.username = payload.username

    if payload.bio is not None:
        user.bio = payload.bio

    db.commit()
    db.refresh(user)
    return user

def change_username(db: Session, user: User, new_username: str):
    user.username = new_username
    db.commit()
    db.refresh(user)
    return user

def change_password(
    db: Session,
    user: User,
    current_password: str,
    new_password: str,
):
    if not verify_password(current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    user.hashed_password = hash_password(new_password)
    db.commit()