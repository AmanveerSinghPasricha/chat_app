"""
E2EE Service Test Suite
=======================

Comprehensive tests for End-to-End Encryption functionality.
Tests cover:
- Device registration (new and update scenarios)
- Prekey upload and storage
- Prekey bundle retrieval
- Friend verification
- Security constraints
"""

import pytest
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

# Adjust imports based on your project structure
import sys
sys.path.insert(0, '/home/claude/app')

from core.database import Base
from e2ee.service import (
    register_device,
    upload_prekeys,
    get_prekey_bundle,
    fetch_prekeys_for_user,
    are_friends,
)
from e2ee.model import Device, SignedPreKey, OneTimePreKey
from friend.model import FriendRequest
from user.model import User


# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_e2ee.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def user_alice(db):
    """Create test user Alice"""
    user = User(
        id=uuid4(),
        username="alice",
        email="alice@example.com",
        hashed_password="hashed_password"    
        )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def user_bob(db):
    """Create test user Bob"""
    user = User(
        id=uuid4(),
        username="bob",
        email="bob@example.com",
        hashed_password="hashed_password",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def make_friends(db):
    """Helper to make two users friends"""
    def _make_friends(user_a, user_b):
        friend_req = FriendRequest(
            sender_id=user_a.id,
            receiver_id=user_b.id,
            status="accepted",
        )
        db.add(friend_req)
        db.commit()
    return _make_friends


class TestDeviceRegistration:
    """Test device registration functionality"""
    
    def test_register_new_device(self, db, user_alice):
        """Test registering a brand new device"""
        device = register_device(
            db=db,
            user_id=user_alice.id,
            device_name="web",
            identity_key_pub="identity_key_alice_web",
        )
        
        assert device is not None
        assert device.user_id == user_alice.id
        assert device.device_name == "web"
        assert device.identity_key_pub == "identity_key_alice_web"
        
    def test_register_device_default_name(self, db, user_alice):
        """Test device registration with default name"""
        device = register_device(
            db=db,
            user_id=user_alice.id,
            device_name=None,  # Should default to "web"
            identity_key_pub="identity_key_alice",
        )
        
        assert device.device_name == "web"
    
    def test_update_existing_device(self, db, user_alice):
        """Test updating existing device (UPSERT behavior)"""
        # Register device first time
        device1 = register_device(
            db=db,
            user_id=user_alice.id,
            device_name="web",
            identity_key_pub="old_key",
        )
        device1_id = device1.id
        
        # Register same device again (simulates key regeneration)
        device2 = register_device(
            db=db,
            user_id=user_alice.id,
            device_name="web",
            identity_key_pub="new_key",
        )
        
        # Should be same device with updated key
        assert device2.id == device1_id
        assert device2.identity_key_pub == "new_key"
        
        # Should only have one device in DB
        count = db.query(Device).filter(Device.user_id == user_alice.id).count()
        assert count == 1
    
    def test_multiple_devices_per_user(self, db, user_alice):
        """Test user can have multiple devices with different names"""
        device_web = register_device(
            db=db,
            user_id=user_alice.id,
            device_name="web",
            identity_key_pub="key_web",
        )
        
        device_mobile = register_device(
            db=db,
            user_id=user_alice.id,
            device_name="mobile",
            identity_key_pub="key_mobile",
        )
        
        assert device_web.id != device_mobile.id
        assert device_web.device_name == "web"
        assert device_mobile.device_name == "mobile"


class MockSignedPreKey:
    """Mock schema for signed prekey"""
    def __init__(self, key_id, public_key, signature):
        self.key_id = key_id
        self.public_key = public_key
        self.signature = signature


class MockOneTimePreKey:
    """Mock schema for one-time prekey"""
    def __init__(self, key_id, public_key):
        self.key_id = key_id
        self.public_key = public_key


class TestPrekeyUpload:
    """Test prekey upload functionality"""
    
    def test_upload_prekeys_success(self, db, user_alice):
        """Test successful prekey upload"""
        # Register device first
        device = register_device(
            db=db,
            user_id=user_alice.id,
            device_name="web",
            identity_key_pub="identity_key",
        )
        
        # Create mock prekeys
        signed_prekey = MockSignedPreKey(
            key_id=1,
            public_key="signed_pub_key",
            signature="signature",
        )
        
        one_time_prekeys = [
            MockOneTimePreKey(key_id=i, public_key=f"otpk_{i}")
            for i in range(10)
        ]
        
        # Upload prekeys
        upload_prekeys(db, device.id, signed_prekey, one_time_prekeys)
        
        # Verify signed prekey was stored
        spk = db.query(SignedPreKey).filter(
            SignedPreKey.device_id == device.id,
            SignedPreKey.is_active == True
        ).first()
        
        assert spk is not None
        assert spk.key_id == 1
        assert spk.public_key == "signed_pub_key"
        
        # Verify one-time prekeys were stored
        otpks = db.query(OneTimePreKey).filter(
            OneTimePreKey.device_id == device.id
        ).all()
        
        assert len(otpks) == 10
    
    def test_upload_deactivates_old_signed_prekeys(self, db, user_alice):
        """Test that uploading new signed prekey deactivates old ones"""
        device = register_device(
            db=db,
            user_id=user_alice.id,
            device_name="web",
            identity_key_pub="identity_key",
        )
        
        # Upload first signed prekey
        spk1 = MockSignedPreKey(1, "pub1", "sig1")
        upload_prekeys(db, device.id, spk1, [])
        
        # Upload second signed prekey
        spk2 = MockSignedPreKey(2, "pub2", "sig2")
        upload_prekeys(db, device.id, spk2, [])
        
        # First should be inactive
        old_spk = db.query(SignedPreKey).filter(
            SignedPreKey.device_id == device.id,
            SignedPreKey.key_id == 1
        ).first()
        assert old_spk.is_active == False
        
        # Second should be active
        new_spk = db.query(SignedPreKey).filter(
            SignedPreKey.device_id == device.id,
            SignedPreKey.key_id == 2
        ).first()
        assert new_spk.is_active == True
    
    def test_upload_clears_old_unused_otpks(self, db, user_alice):
        """Test that old unused one-time prekeys are cleared"""
        device = register_device(
            db=db,
            user_id=user_alice.id,
            device_name="web",
            identity_key_pub="identity_key",
        )
        
        # Upload first batch
        spk = MockSignedPreKey(1, "pub1", "sig1")
        otpks1 = [MockOneTimePreKey(i, f"key_{i}") for i in range(5)]
        upload_prekeys(db, device.id, spk, otpks1)
        
        # Upload second batch (should clear first batch since unused)
        otpks2 = [MockOneTimePreKey(i, f"new_key_{i}") for i in range(10, 15)]
        upload_prekeys(db, device.id, spk, otpks2)
        
        # Should only have new batch
        all_otpks = db.query(OneTimePreKey).filter(
            OneTimePreKey.device_id == device.id
        ).all()
        
        assert len(all_otpks) == 5
        assert all([otpk.key_id >= 10 for otpk in all_otpks])
    
    def test_upload_to_nonexistent_device(self, db):
        """Test upload to device that doesn't exist"""
        fake_device_id = uuid4()
        spk = MockSignedPreKey(1, "pub", "sig")
        
        with pytest.raises(HTTPException) as exc_info:
            upload_prekeys(db, fake_device_id, spk, [])
        
        assert exc_info.value.status_code == 404


class TestPrekeyBundleRetrieval:
    """Test prekey bundle retrieval"""
    
    def test_get_prekey_bundle_success(self, db, user_alice):
        """Test successful prekey bundle retrieval"""
        # Setup: register device and upload keys
        device = register_device(
            db=db,
            user_id=user_alice.id,
            device_name="web",
            identity_key_pub="identity_key",
        )
        
        spk = MockSignedPreKey(1, "signed_pub", "signature")
        otpks = [MockOneTimePreKey(i, f"otpk_{i}") for i in range(5)]
        upload_prekeys(db, device.id, spk, otpks)
        
        # Fetch bundle
        dev, signed, one_time = get_prekey_bundle(db, user_alice.id)
        
        assert dev.id == device.id
        assert signed.key_id == 1
        assert one_time is not None
        assert one_time.is_used == True  # Should be marked as used
    
    def test_get_prekey_bundle_no_device(self, db, user_alice):
        """Test fetching bundle when user has no device"""
        with pytest.raises(HTTPException) as exc_info:
            get_prekey_bundle(db, user_alice.id)
        
        assert exc_info.value.status_code == 404
        assert "No device registered" in exc_info.value.detail
    
    def test_get_prekey_bundle_no_signed_prekey(self, db, user_alice):
        """Test fetching bundle when device has no signed prekey"""
        device = register_device(
            db=db,
            user_id=user_alice.id,
            device_name="web",
            identity_key_pub="identity_key",
        )
        
        with pytest.raises(HTTPException) as exc_info:
            get_prekey_bundle(db, user_alice.id)
        
        assert exc_info.value.status_code == 404
        assert "No signed prekey" in exc_info.value.detail
    
    def test_get_prekey_bundle_exhausted_otpks(self, db, user_alice):
        """Test fetching bundle when one-time prekeys are exhausted"""
        device = register_device(
            db=db,
            user_id=user_alice.id,
            device_name="web",
            identity_key_pub="identity_key",
        )
        
        spk = MockSignedPreKey(1, "signed_pub", "signature")
        upload_prekeys(db, device.id, spk, [])  # No one-time prekeys
        
        dev, signed, one_time = get_prekey_bundle(db, user_alice.id)
        
        assert dev is not None
        assert signed is not None
        assert one_time is None  # No one-time prekey available
    
    def test_otpk_consumption_fifo(self, db, user_alice):
        """Test that one-time prekeys are consumed in FIFO order"""
        device = register_device(
            db=db,
            user_id=user_alice.id,
            device_name="web",
            identity_key_pub="identity_key",
        )
        
        spk = MockSignedPreKey(1, "signed_pub", "signature")
        otpks = [MockOneTimePreKey(i, f"otpk_{i}") for i in range(5)]
        upload_prekeys(db, device.id, spk, otpks)
        
        # Fetch bundle 3 times
        used_keys = []
        for _ in range(3):
            _, _, one_time = get_prekey_bundle(db, user_alice.id)
            used_keys.append(one_time.key_id)
        
        # Should consume in order: 0, 1, 2 (FIFO)
        assert used_keys == [0, 1, 2]


class TestFriendCheckedBundleRetrieval:
    """Test prekey bundle retrieval with friend verification"""
    
    def test_fetch_prekeys_success_when_friends(
        self, db, user_alice, user_bob, make_friends
    ):
        """Test successful bundle fetch between friends"""
        # Make Alice and Bob friends
        make_friends(user_alice, user_bob)
        
        # Setup Bob's device and keys
        bob_device = register_device(
            db=db,
            user_id=user_bob.id,
            device_name="web",
            identity_key_pub="bob_identity",
        )
        
        spk = MockSignedPreKey(1, "bob_signed_pub", "signature")
        otpks = [MockOneTimePreKey(i, f"bob_otpk_{i}") for i in range(5)]
        upload_prekeys(db, bob_device.id, spk, otpks)
        
        # Alice fetches Bob's bundle
        bundle = fetch_prekeys_for_user(
            db=db,
            current_user_id=user_alice.id,
            receiver_user_id=user_bob.id,
        )
        
        assert bundle["device_id"] == str(bob_device.id)
        assert bundle["identity_key_pub"] == "bob_identity"
        assert bundle["signed_prekey"]["key_id"] == 1
        assert bundle["one_time_prekey"] is not None
    
    def test_fetch_prekeys_forbidden_when_not_friends(
        self, db, user_alice, user_bob
    ):
        """Test bundle fetch fails when users are not friends"""
        # Setup Bob's device (but don't make friends)
        bob_device = register_device(
            db=db,
            user_id=user_bob.id,
            device_name="web",
            identity_key_pub="bob_identity",
        )
        
        spk = MockSignedPreKey(1, "bob_signed_pub", "signature")
        upload_prekeys(db, bob_device.id, spk, [])
        
        # Alice tries to fetch Bob's bundle (should fail)
        with pytest.raises(HTTPException) as exc_info:
            fetch_prekeys_for_user(
                db=db,
                current_user_id=user_alice.id,
                receiver_user_id=user_bob.id,
            )
        
        assert exc_info.value.status_code == 403
        assert "not friends" in exc_info.value.detail


class TestFriendCheck:
    """Test friend relationship checking"""
    
    def test_are_friends_when_accepted(self, db, user_alice, user_bob):
        """Test friend check with accepted request"""
        friend_req = FriendRequest(
            sender_id=user_alice.id,
            receiver_id=user_bob.id,
            status="accepted",
        )
        db.add(friend_req)
        db.commit()
        
        assert are_friends(db, user_alice.id, user_bob.id) == True
        assert are_friends(db, user_bob.id, user_alice.id) == True  # Bidirectional
    
    def test_not_friends_when_pending(self, db, user_alice, user_bob):
        """Test friend check with pending request"""
        friend_req = FriendRequest(
            sender_id=user_alice.id,
            receiver_id=user_bob.id,
            status="pending",
        )
        db.add(friend_req)
        db.commit()
        
        assert are_friends(db, user_alice.id, user_bob.id) == False
    
    def test_not_friends_when_no_request(self, db, user_alice, user_bob):
        """Test friend check with no request"""
        assert are_friends(db, user_alice.id, user_bob.id) == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
