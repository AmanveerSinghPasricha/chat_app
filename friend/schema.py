from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class FriendRequestCreate(BaseModel):
    receiver_id: UUID

class FriendRequestAction(BaseModel):
    request_id: UUID

class FriendRequestResponse(BaseModel):
    id: UUID
    sender_id: UUID
    receiver_id: UUID
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class FriendResponse(BaseModel):
    id: UUID
    username: str