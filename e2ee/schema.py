from pydantic import BaseModel
from uuid import UUID
from typing import List, Optional

class DeviceRegisterRequest(BaseModel):
    device_name: Optional[str] = None
    identity_key_pub: str  # base64 or PEM

class DeviceResponse(BaseModel):
    id: UUID
    user_id: UUID
    device_name: Optional[str]
    identity_key_pub: str

    class Config:
        from_attributes = True

class SignedPreKeyPayload(BaseModel):
    key_id: int
    public_key: str
    signature: str

class OneTimePreKeyPayload(BaseModel):
    key_id: int
    public_key: str

class UploadPreKeysRequest(BaseModel):
    signed_prekey: SignedPreKeyPayload
    one_time_prekeys: List[OneTimePreKeyPayload]

class PreKeyBundleResponse(BaseModel):
    device_id: UUID
    identity_key_pub: str
    signed_prekey: SignedPreKeyPayload
    one_time_prekey: OneTimePreKeyPayload | None
