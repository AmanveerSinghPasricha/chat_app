from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.deps import get_db, get_current_user
from core.utils import success_response

from friend.schema import (
    FriendRequestCreate,
    FriendRequestAction,
    FriendRequestResponse,
)
from friend.service import (
    send_friend_request,
    respond_to_request,
    get_pending_requests_for_receiver,
)

router = APIRouter(prefix="/friends", tags=["Friends"])

@router.post("/request")
def send_request(
    payload: FriendRequestCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    send_friend_request(
        db=db,
        sender_id=current_user.id,
        receiver_id=payload.receiver_id,
    )

    return success_response(
        status_code=201,
        message="Friend request sent",
    )

@router.post("/accept")
def accept_request(
    payload: FriendRequestAction,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    respond_to_request(
        db=db,
        request_id=payload.request_id,
        user_id=current_user.id,
        action="accepted",
    )

    return success_response(message="Friend request accepted")

@router.post("/reject")
def reject_request(
    payload: FriendRequestAction,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    respond_to_request(
        db=db,
        request_id=payload.request_id,
        user_id=current_user.id,
        action="rejected",
    )

    return success_response(message="Friend request rejected")

@router.get("/requests", response_model=list[FriendRequestResponse])
def get_friend_requests(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    requests = get_pending_requests_for_receiver(
        db=db,
        receiver_id=current_user.id,
    )

    return success_response(
        data=requests,
        message="Pending friend requests fetched",
    )
