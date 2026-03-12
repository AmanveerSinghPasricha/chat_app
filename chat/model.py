import uuid
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    Integer,
    Text,
    Index,
)
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

    # used to prevent duplicate messages in UI
    client_msg_id = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "sender_id": str(self.sender_id),
            "ciphertext": self.ciphertext,
            "nonce": self.nonce,
            "sender_device_id": str(self.sender_device_id) if self.sender_device_id else None,
            "receiver_device_id": str(self.receiver_device_id) if self.receiver_device_id else None,
            "ephemeral_pub": self.ephemeral_pub,
            "signed_prekey_id": self.signed_prekey_id,
            "one_time_prekey_id": self.one_time_prekey_id,
            "message_type": self.message_type,
            "client_msg_id": self.client_msg_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

# optional index for faster dedupe
Index("ix_messages_client_msg_id", Message.client_msg_id)
