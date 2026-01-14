from fastapi import APIRouter, Depends
from core.deps import get_current_user,get_db
from core.utils import success_response
from user.model import User
from sqlalchemy.orm import Session
from core.response import ApiResponse
from user.schema import UserListResponse, ChangeUsernameRequest
from user.service import list_users_for_connections
from core.utils import success_response
from core.deps import get_db, get_current_user
from core.utils import success_response
from user.schema import UpdateProfileRequest, UserProfileResponse, ChangePasswordRequest
from user.service import update_user_profile, change_username, change_password
from user.model import User

router = APIRouter(prefix="/users", tags=["Users"])

@router.get(
    "/me",
    response_model=ApiResponse[UserProfileResponse],
)
def get_me(current_user: User = Depends(get_current_user)):
    return success_response(
        data=current_user,
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

@router.delete("/me")
def delete_profile(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from user.service import delete_user_account

    delete_user_account(db, current_user)

    return success_response(
        message="User account deleted successfully"
    )

@router.put(
    "/me",
    response_model=UserProfileResponse,
)
def update_profile(
    payload: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = update_user_profile(db, current_user, payload)

    return success_response(
        data=user,
        message="Profile updated successfully",
    )

@router.put("/me/username")
def change_username_api(
    payload: ChangeUsernameRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = change_username(db, current_user, payload.username)
    return success_response(
        data=user,
        message="Username updated successfully",
    )

@router.put("/me/password")
def change_password_api(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    change_password(
        db,
        current_user,
        payload.current_password,
        payload.new_password,
    )

    return success_response(
        message="Password updated successfully. Please login again."
    )