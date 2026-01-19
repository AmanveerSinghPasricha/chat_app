from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class ConversationResponse(BaseModel):
    id: UUID
    user1_id: UUID
    user2_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    sender_id: UUID
    content: str
    message_type: str
    created_at: datetime

    class Config:
        from_attributes = True

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class E2EEHeader(BaseModel):
    ephemeral_pub: Optional[str] = None
    signed_prekey_id: Optional[int] = None
    one_time_prekey_id: Optional[int] = None

class EncryptedMessageIn(BaseModel):
    ciphertext: str
    nonce: str
    sender_device_id: UUID
    receiver_device_id: UUID
    header: Optional[E2EEHeader] = None
    message_type: str = "text"

class EncryptedMessageOut(BaseModel):
    id: UUID
    conversation_id: UUID
    sender_id: UUID

    ciphertext: str
    nonce: str
    sender_device_id: UUID
    receiver_device_id: UUID

    ephemeral_pub: Optional[str] = None
    signed_prekey_id: Optional[int] = None
    one_time_prekey_id: Optional[int] = None

    message_type: str
    created_at: datetime

    class Config:
        from_attributes = True
