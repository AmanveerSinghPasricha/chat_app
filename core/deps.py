from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from core.database import SessionLocal
from core.security import decode_access_token
from user.model import User
from uuid import UUID

# -----------------------------
# DB DEPENDENCY
# -----------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------------
# AUTH DEPENDENCY
# -----------------------------
def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate user using either:
    1) Authorization Bearer token
    2) HTTP-only cookie
    """

    token = None

    # -----------------------------
    # Check Authorization header
    # -----------------------------
    auth_header = request.headers.get("Authorization")

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

    # -----------------------------
    # Fallback to cookie
    # -----------------------------
    if not token:
        token = request.cookies.get("access_token")

    # -----------------------------
    # No token
    # -----------------------------
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    # -----------------------------
    # Decode JWT
    # -----------------------------
    try:
        user_id: UUID = decode_access_token(token)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # -----------------------------
    # Fetch user
    # -----------------------------
    user = db.query(User).filter(User.id == user_id).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account inactive or deleted",
        )

    return user