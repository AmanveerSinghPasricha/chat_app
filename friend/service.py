from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_, and_
from uuid import UUID
from friend.model import FriendRequest
from user.model import User

def are_friends(db: Session, user_a: UUID, user_b: UUID) -> bool:
    fr = (
        db.query(FriendRequest)
        .filter(
            FriendRequest.status == "accepted",
            or_(
                and_(
                    FriendRequest.sender_id == user_a,
                    FriendRequest.receiver_id == user_b,
                ),
                and_(
                    FriendRequest.sender_id == user_b,
                    FriendRequest.receiver_id == user_a,
                ),
            ),
        )
        .first()
    )
    return fr is not None


def send_friend_request(db: Session, sender_id, receiver_id):
    if sender_id == receiver_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send friend request to yourself",
        )

    existing_request = (
        db.query(FriendRequest)
        .filter(
            FriendRequest.sender_id == sender_id,
            FriendRequest.receiver_id == receiver_id,
            FriendRequest.status == "pending",
        )
        .first()
    )

    if existing_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Friend request already sent",
        )

    try:
        friend_request = FriendRequest(
            sender_id=sender_id,
            receiver_id=receiver_id,
        )
        db.add(friend_request)
        db.commit()
        db.refresh(friend_request)
        return friend_request

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid receiver",
        )


def respond_to_request(db: Session, request_id, user_id, action: str):
    friend_request = (
        db.query(FriendRequest)
        .filter(FriendRequest.id == request_id)
        .first()
    )

    if not friend_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Friend request not found",
        )

    if friend_request.receiver_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to respond to this request",
        )

    if friend_request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Friend request already handled",
        )

    if action not in {"accepted", "rejected"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action",
        )

    friend_request.status = action
    db.commit()
    db.refresh(friend_request)
    return friend_request


def get_friends(db: Session, user_id):
    friends = (
        db.query(User)
        .join(
            FriendRequest,
            or_(
                and_(
                    FriendRequest.sender_id == user_id,
                    FriendRequest.receiver_id == User.id,
                ),
                and_(
                    FriendRequest.receiver_id == user_id,
                    FriendRequest.sender_id == User.id,
                ),
            ),
        )
        .filter(
            FriendRequest.status == "accepted",
            User.id != user_id,
        )
        .all()
    )

    return friends


def get_pending_requests_for_receiver(db: Session, receiver_id):
    return (
        db.query(FriendRequest)
        .options(joinedload(FriendRequest.sender))
        .filter(
            FriendRequest.receiver_id == receiver_id,
            FriendRequest.status == "pending",
        )
        .all()
    )
