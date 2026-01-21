from sqlalchemy.orm import Session
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import or_

from e2ee.model import Device, SignedPreKey, OneTimePreKey
from friend.model import FriendRequest


# -----------------------------
# FRIEND CHECK
# -----------------------------
def are_friends(db: Session, user_a: UUID, user_b: UUID) -> bool:
    return (
        db.query(FriendRequest)
        .filter(
            or_(
                (FriendRequest.sender_id == user_a)
                & (FriendRequest.receiver_id == user_b),
                (FriendRequest.sender_id == user_b)
                & (FriendRequest.receiver_id == user_a),
            ),
            FriendRequest.status == "accepted",
        )
        .first()
        is not None
    )


# -----------------------------
# DEVICE REGISTER (FIXED: UPSERT)
# 1 user + 1 device_name = 1 device
# -----------------------------
def register_device(
    db: Session,
    user_id: UUID,
    device_name: str | None,
    identity_key_pub: str,
) -> Device:
    device_name = device_name or "web"

    existing = (
        db.query(Device)
        .filter(Device.user_id == user_id, Device.device_name == device_name)
        .first()
    )

    # If device already exists -> UPDATE instead of creating new row
    if existing:
        # update identity pub key (in case user cleared local storage and generated new keys)
        existing.identity_key_pub = identity_key_pub
        db.commit()
        db.refresh(existing)
        return existing

    # else create new device
    device = Device(
        user_id=user_id,
        device_name=device_name,
        identity_key_pub=identity_key_pub,
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


# -----------------------------
# UPLOAD PREKEYS
# -----------------------------
def upload_prekeys(
    db: Session,
    device_id: UUID,
    signed_prekey,
    one_time_prekeys,
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    # Deactivate old signed prekeys
    db.query(SignedPreKey).filter(SignedPreKey.device_id == device_id).update(
        {"is_active": False}
    )

    # Insert new signed prekey
    spk = SignedPreKey(
        device_id=device_id,
        key_id=signed_prekey.key_id,
        public_key=signed_prekey.public_key,
        signature=signed_prekey.signature,
        is_active=True,
    )
    db.add(spk)

    # OPTIONAL BUT RECOMMENDED:
    # clear unused old one-time prekeys to prevent DB growing forever
    db.query(OneTimePreKey).filter(
        OneTimePreKey.device_id == device_id,
        OneTimePreKey.is_used == False,
    ).delete(synchronize_session=False)

    # Insert one-time prekeys
    for pk in one_time_prekeys:
        db.add(
            OneTimePreKey(
                device_id=device_id,
                key_id=pk.key_id,
                public_key=pk.public_key,
                is_used=False,
            )
        )

    db.commit()


# -----------------------------
# GET PREKEY BUNDLE (NO FRIEND CHECK)
# Use this internally if needed
# -----------------------------
def get_prekey_bundle(db: Session, user_id: UUID):
    device = (
        db.query(Device)
        .filter(Device.user_id == user_id)
        .order_by(Device.created_at.desc())
        .first()
    )
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No device registered for user",
        )

    signed = (
        db.query(SignedPreKey)
        .filter(
            SignedPreKey.device_id == device.id,
            SignedPreKey.is_active == True,
        )
        .order_by(SignedPreKey.created_at.desc())
        .first()
    )
    if not signed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No signed prekey found",
        )

    one_time = (
        db.query(OneTimePreKey)
        .filter(
            OneTimePreKey.device_id == device.id,
            OneTimePreKey.is_used == False,
        )
        .order_by(OneTimePreKey.created_at.asc())
        .first()
    )

    # consume one-time prekey
    if one_time:
        one_time.is_used = True
        db.commit()
        db.refresh(one_time)

    return device, signed, one_time


# -----------------------------
# FETCH PREKEY BUNDLE (WITH FRIEND CHECK)
# This is what you need
# -----------------------------
def fetch_prekeys_for_user(
    db: Session,
    current_user_id: UUID,
    receiver_user_id: UUID,
):
    # FRIEND CONSTRAINT CHECK
    if not are_friends(db, current_user_id, receiver_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not friends with this user",
        )

    device = (
        db.query(Device)
        .filter(Device.user_id == receiver_user_id)
        .order_by(Device.created_at.desc())
        .first()
    )
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receiver device not found",
        )

    signed = (
        db.query(SignedPreKey)
        .filter(
            SignedPreKey.device_id == device.id,
            SignedPreKey.is_active == True,
        )
        .order_by(SignedPreKey.created_at.desc())
        .first()
    )
    if not signed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receiver signed prekey not found",
        )

    one_time = (
        db.query(OneTimePreKey)
        .filter(
            OneTimePreKey.device_id == device.id,
            OneTimePreKey.is_used == False,
        )
        .order_by(OneTimePreKey.created_at.asc())
        .first()
    )

    # consume one-time prekey
    if one_time:
        one_time.is_used = True
        db.commit()
        db.refresh(one_time)

    return {
        "device_id": str(device.id),
        "identity_key_pub": device.identity_key_pub,
        "signed_prekey": {
            "key_id": signed.key_id,
            "public_key": signed.public_key,
            "signature": signed.signature,
        },
        "one_time_prekey": None
        if not one_time
        else {
            "key_id": one_time.key_id,
            "public_key": one_time.public_key,
        },
    }
