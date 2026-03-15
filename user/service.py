from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from user.model import User
from friend.model import FriendRequest
from fastapi import HTTPException, status
from datetime import datetime
from user.schema import UpdateProfileRequest
from core.security import verify_password, hash_password

def list_users_for_connections(db: Session, current_user_id):
    # This subquery finds any existing relationship (Pending or Accepted)
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
        .filter(User.is_active == True)
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

def update_user_profile(db: Session, user: User, payload: UpdateProfileRequest) -> User:
    """
    Updates user identity safely without affecting Auth or WebSockets.
    """
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Cannot update deleted account")

    # 1. Username Update Logic
    if payload.username is not None:
        new_username = payload.username.strip()
        # Only proceed if the username actually changed
        if new_username != user.username and new_username != "":
            # Check if anyone else already has this username
            existing_user = db.query(User).filter(
                User.username == new_username, 
                User.id != user.id
            ).first()
            
            if existing_user:
                raise HTTPException(status_code=400, detail="Username already taken")
            
            user.username = new_username

    # 2. Bio Update Logic
    if payload.bio is not None:
        stripped_bio = payload.bio.strip()
        # If the user cleared the bio, store as None; otherwise, store the text
        user.bio = stripped_bio if stripped_bio != "" else None

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        # This log helps you see the error in your terminal without crashing the app
        print(f"DATABASE ERROR during Identity Update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Internal server error while saving profile"
        )

def change_username(db: Session, user: User, new_username: str):
    # Check if someone else is already using this username
    existing_user = db.query(User).filter(
        User.username == new_username,
        User.id != user.id
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    user.username = new_username
    db.commit()
    db.refresh(user)
    return user

def change_password(db: Session, user: User, current_password: str, new_password: str):
    if not verify_password(current_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    
    if len(new_password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password must be at least 8 characters")

    user.hashed_password = hash_password(new_password)
    db.commit()