from fastapi import WebSocketException, status
from core.security import decode_access_token

def authenticate_ws(token: str):
    if not token:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    try:
        return decode_access_token(token)
    except Exception:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)