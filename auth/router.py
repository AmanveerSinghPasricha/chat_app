from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from auth.schema import SignupRequest, LoginRequest, TokenResponse
from auth.service import signup_user, login_user
from core.database import SessionLocal
from core.utils import success_response
from core.response import ApiResponse
from core.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post(
    "/signup",
    response_model=ApiResponse[TokenResponse],
    status_code=201,
)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    token = signup_user(db, payload.username, payload.email, payload.password)

    return success_response(
        data=TokenResponse(access_token=token),
        message="User registered successfully",
        status_code=201,
    )

@router.post(
    "/login",
    response_model=ApiResponse[TokenResponse],
)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    token = login_user(db, payload.email, payload.password)

    return success_response(
        data=TokenResponse(access_token=token),
        message="Login successful",
    )

@router.post("/logout")
def logout(current_user=Depends(get_current_user)):
    """
    Logout endpoint.
    Client must delete JWT and close WebSocket.
    """
    return success_response(
        message="Logged out successfully"
    )

