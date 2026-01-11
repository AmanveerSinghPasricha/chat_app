from fastapi import APIRouter, Depends
from core.deps import get_current_user,get_db
from core.utils import success_response
from user.model import User
from sqlalchemy.orm import Session
from core.response import ApiResponse
from user.schema import UserListResponse
from user.service import list_users_for_connections

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return success_response(
        data={
            "id": str(current_user.id),
            "username": current_user.username,
            "email": current_user.email,
        },
        message="User fetched successfully",
    )

@router.get(
    "",
    response_model=ApiResponse[list[UserListResponse]],
)
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    users = list_users_for_connections(db, current_user.id)

    return success_response(
        data=users,
        message="Users available for connection",
    )