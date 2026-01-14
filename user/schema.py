from pydantic import BaseModel
from uuid import UUID
from typing import Optional

class UserListResponse(BaseModel):
    id: UUID
    username: str
    email: str
    bio: Optional[str] = None

    class Config:
        from_attributes = True

class UpdateProfileRequest(BaseModel):
    username: Optional[str] = None
    bio: Optional[str] = None

class UserProfileResponse(BaseModel):
    id: UUID
    username: str
    email: str
    bio: Optional[str]

    class Config:
        from_attributes = True

class ChangeUsernameRequest(BaseModel):
    username: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str