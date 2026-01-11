from pydantic import BaseModel
from uuid import UUID

class UserListResponse(BaseModel):
    id: UUID
    username: str
    email: str

    class Config:
        from_attributes = True
