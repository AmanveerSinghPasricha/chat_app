from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class FriendRequestCreate(BaseModel):
    receiver_id: UUID

class FriendRequestAction(BaseModel):
    request_id: UUID

class FriendRequestSender(BaseModel):
    id: UUID
    username: str
    email: str
    bio: Optional[str] = None

class FriendRequestResponse(BaseModel):
    id: UUID
    sender_id: UUID
    receiver_id: UUID
    status: str
    created_at: datetime

    sender: FriendRequestSender

    class Config:
        from_attributes = True

class FriendResponse(BaseModel):
    id: UUID
    username: str
    email: str

    class Config:
        from_attributes = True