import pytest
import time
import threading
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# IMPORTANT: import database FIRST
from core import database

# -----------------------------
# TEST DATABASE ENGINE
# -----------------------------

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

database.engine = engine
database.SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# NOW import the FastAPI app and other dependencies
from main import app
from core.database import Base, get_db
from core.security import create_access_token

from user.model import User
from friend.model import FriendRequest
from chat.model import Conversation, Message
from e2ee.service import register_device, upload_prekeys

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)

# -----------------------------
# DB FIXTURE
# -----------------------------

@pytest.fixture(scope="function")
def db():

    Base.metadata.create_all(bind=engine)

    connection = engine.connect()
    transaction = connection.begin()

    session = TestingSessionLocal(bind=connection)

    print(f"\nDEBUG TEST: Created session with ID: {id(session)}")

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db

    yield session

    print("DEBUG TEST: Cleaning up session")

    app.dependency_overrides.clear()
    session.close()
    transaction.rollback()
    connection.close()

    Base.metadata.drop_all(bind=engine)


# -----------------------------
# CLIENT
# -----------------------------

@pytest.fixture
def client():
    return TestClient(app)


# -----------------------------
# USERS
# -----------------------------

@pytest.fixture
def users(db):

    alice = User(
        id=uuid4(),
        username="alice",
        email="alice@example.com",
        hashed_password="hashed",
    )

    bob = User(
        id=uuid4(),
        username="bob",
        email="bob@example.com",
        hashed_password="hashed",
    )

    db.add_all([alice, bob])
    db.commit()

    db.refresh(alice)
    db.refresh(bob)

    print("DEBUG USERS:", alice.id, bob.id)

    return alice, bob


# -----------------------------
# CONVERSATION
# -----------------------------

@pytest.fixture
def conversation(db, users):

    alice, bob = users

    conv = Conversation(
        id=uuid4(),
        user1_id=alice.id,
        user2_id=bob.id,
    )

    db.add(conv)
    db.commit()
    db.refresh(conv)

    print("DEBUG CONVERSATION:", conv.id)

    return conv


# -----------------------------
# FRIENDSHIP
# -----------------------------

@pytest.fixture
def make_friends(db):

    def _make_friends(user_a, user_b):

        fr = FriendRequest(
            sender_id=user_a.id,
            receiver_id=user_b.id,
            status="accepted",
        )

        db.add(fr)
        db.commit()

        print("DEBUG FRIENDSHIP CREATED:", user_a.id, user_b.id)

    return _make_friends


# -----------------------------
# FULL E2EE CHAT TEST
# -----------------------------

class TestFullChatFlow:

    def test_complete_e2e_chat(
        self,
        client,
        db,
        users,
        conversation,
        make_friends,
    ):

        alice, bob = users

        make_friends(alice, bob)

        alice_device = register_device(
            db=db,
            user_id=alice.id,
            device_name="web",
            identity_key_pub="alice_identity_key",
        )

        bob_device = register_device(
            db=db,
            user_id=bob.id,
            device_name="web",
            identity_key_pub="bob_identity_key",
        )

        db.commit()

        print("DEBUG DEVICES:", alice_device.id, bob_device.id)

        class SPK:
            key_id = 1
            public_key = "signed_pub"
            signature = "signature"

        class OTPK:
            def __init__(self, i):
                self.key_id = i
                self.public_key = f"otpk_{i}"

        otpks = [OTPK(i) for i in range(5)]

        upload_prekeys(db, bob_device.id, SPK, otpks)

        db.commit()

        print("DEBUG PREKEYS UPLOADED")

        alice_token = create_access_token(data={"sub": str(alice.id)})
        bob_token = create_access_token(data={"sub": str(bob.id)})

        ws_url_alice = f"/chat/ws/{conversation.id}?token={alice_token}"
        ws_url_bob = f"/chat/ws/{conversation.id}?token={bob_token}"

        print("DEBUG WS URL ALICE:", ws_url_alice)
        print("DEBUG WS URL BOB:", ws_url_bob)

        with client.websocket_connect(ws_url_alice) as alice_ws:

            print("DEBUG ALICE CONNECTED")

            with client.websocket_connect(ws_url_bob) as bob_ws:

                print("DEBUG BOB CONNECTED")

                message_payload = {
                    "ciphertext": "encrypted_message_data",
                    "nonce": "random_nonce",
                    "sender_device_id": str(alice_device.id),
                    "receiver_device_id": str(bob_device.id),
                    "header": {
                        "ephemeral_pub": "ephemeral_key",
                        "signed_prekey_id": 1,
                        "one_time_prekey_id": 1,
                    },
                    "message_type": "text",
                    "client_msg_id": "msg_1",
                }

                alice_ws.send_json(message_payload)

                print("DEBUG MESSAGE SENT")

                received_holder = {}

                def receive_message():
                    try:
                        msg = bob_ws.receive_json()
                        received_holder["msg"] = msg
                    except Exception:
                        pass

                t = threading.Thread(target=receive_message)
                t.start()
                t.join(timeout=5)

                assert "msg" in received_holder, "Bob did not receive message"

                received = received_holder["msg"]

                print("DEBUG MESSAGE RECEIVED:", received)

                assert received["ciphertext"] == "encrypted_message_data"

        stored = (
            db.query(Message)
            .filter(Message.conversation_id == conversation.id)
            .first()
        )

        print("DEBUG STORED MESSAGE:", stored)

        assert stored is not None
        assert stored.ciphertext == "encrypted_message_data"