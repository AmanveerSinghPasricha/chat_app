from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from auth.schema import SignupRequest, LoginRequest
from auth.service import signup_user, login_user

from core.deps import get_db, get_current_user
from core.utils import success_response

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup", status_code=201)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):

    user, token = signup_user(
        db,
        payload.username,
        payload.email,
        payload.password,
    )

    response = JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=success_response(
            data={
                "user_id": str(user.id),
                "access_token": token
            },
            message="User registered successfully",
            status_code=201,
        ).dict(),
    )

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60,
    )

    return response


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):

    user, token = login_user(db, payload.email, payload.password)

    response = JSONResponse(
        content=success_response(
            data={
                "user_id": str(user.id),
                "access_token": token
            },
            message="Login successful",
        ).dict()
    )

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60,
    )

    return response


@router.post("/logout")
def logout(
    response: Response,
    current_user=Depends(get_current_user),
):

    response = JSONResponse(
        content=success_response(
            message="Logged out successfully"
        ).dict()
    )

    response.delete_cookie("access_token")

    return response