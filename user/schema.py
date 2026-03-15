from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from typing import Optional

class UserListResponse(BaseModel):
    id: UUID
    username: str
    email: str
    bio: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class UpdateProfileRequest(BaseModel):
    # Optional allows partial updates (e.g., just updating bio)
    username: Optional[str] = Field(None, min_length=3, max_length=20)
    bio: Optional[str] = Field(None, max_length=255)

class UserProfileResponse(BaseModel):
    id: UUID
    username: str
    email: str
    bio: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class ChangeUsernameRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)