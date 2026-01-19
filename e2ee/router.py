from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from core.deps import get_db, get_current_user
from core.utils import success_response
from core.response import ApiResponse
from user.model import User

from e2ee.schema import (
    DeviceRegisterRequest,
    DeviceResponse,
    UploadPreKeysRequest,
    PreKeyBundleResponse,
)
from e2ee.service import register_device, upload_prekeys, get_prekey_bundle

router = APIRouter(prefix="/e2ee", tags=["E2EE"])

@router.post("/devices/register", response_model=ApiResponse[DeviceResponse])
def register_device_api(
    payload: DeviceRegisterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    device = register_device(
        db=db,
        user_id=current_user.id,
        device_name=payload.device_name,
        identity_key_pub=payload.identity_key_pub,
    )
    return success_response(data=device, message="Device registered")


@router.post("/prekeys/upload")
def upload_prekeys_api(
    payload: UploadPreKeysRequest,
    device_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # You can enforce: device must belong to current_user
    upload_prekeys(db, device_id, payload.signed_prekey, payload.one_time_prekeys)
    return success_response(message="Prekeys uploaded")


@router.get("/prekeys/bundle/{user_id}", response_model=ApiResponse[PreKeyBundleResponse])
def get_bundle_api(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    device, signed, one_time = get_prekey_bundle(db, user_id)

    data = {
        "device_id": device.id,
        "identity_key_pub": device.identity_key_pub,
        "signed_prekey": {
            "key_id": signed.key_id,
            "public_key": signed.public_key,
            "signature": signed.signature,
        },
        "one_time_prekey": None if not one_time else {
            "key_id": one_time.key_id,
            "public_key": one_time.public_key,
        },
    }

    return success_response(data=data, message="Prekey bundle fetched")
