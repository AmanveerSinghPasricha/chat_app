from fastapi import WebSocketException, status
from core.security import decode_access_token
from jose import jwt, JWTError
from uuid import UUID
from core.config import SECRET_KEY, ALGORITHM

def authenticate_ws(token: str) -> UUID:
    if not token:
        raise ValueError("Missing token")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Invalid token payload")

        return UUID(user_id)   # MUST be UUID

    except (JWTError, ValueError):
        raise ValueError("Invalid token")
