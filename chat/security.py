"""
WebSocket Security Module
=========================
Handles JWT authentication for WebSocket connections.
"""

from fastapi import WebSocket
from jose import jwt, JWTError
from uuid import UUID
from core.config import SECRET_KEY, ALGORITHM


async def authenticate_ws(websocket: WebSocket) -> UUID | None:
    """
    Authenticate WebSocket connection using JWT token.
    
    Token can be provided in:
    1. Query parameter: ?token=<jwt>
    2. Cookie: access_token
    3. Header: Authorization: Bearer <jwt>
    
    Returns:
        UUID: User ID if authenticated
        None: If authentication fails
    """
    token = None
    
    # Method 1: Try query parameters (most common for WebSocket)
    token = websocket.query_params.get("token")
    
    # Method 2: Try cookies (if using cookie-based auth)
    if not token:
        token = websocket.cookies.get("access_token")
    
    # Method 3: Try authorization header
    if not token:
        auth_header = websocket.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
    
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        return UUID(user_id)
    
    except (JWTError, ValueError):
        return None