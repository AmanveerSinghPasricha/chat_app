import uuid
from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from core.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user1_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user2_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("user1_id", "user2_id", name="unique_conversation"),
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id"),
        nullable=False,
    )

    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # E2EE FIELDS
    ciphertext = Column(Text, nullable=False)
    nonce = Column(String, nullable=False)

    # metadata for receiver device routing
    sender_device_id = Column(UUID(as_uuid=True), nullable=False)
    receiver_device_id = Column(UUID(as_uuid=True), nullable=False)

    # handshake header metadata (for first message / session setup)
    ephemeral_pub = Column(Text, nullable=True)
    signed_prekey_id = Column(Integer, nullable=True)
    one_time_prekey_id = Column(Integer, nullable=True)

    message_type = Column(String, default="text")

    client_msg_id = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
