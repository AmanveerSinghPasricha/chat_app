from fastapi import APIRouter, Depends
from chat_app.app.core.deps import get_current_user
from chat_app.app.core.utils import success_response
from chat_app.app.user.model import User

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
