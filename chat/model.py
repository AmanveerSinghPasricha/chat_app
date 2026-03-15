import uuid
from sqlalchemy import (
    Column, DateTime, ForeignKey, String, 
    UniqueConstraint, Integer, Text, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from datetime import datetime, timezone
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
    __table_args__ = (UniqueConstraint("user1_id", "user2_id", name="unique_conversation"),)

class Message(Base):
    __tablename__ = "messages"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    ciphertext = Column(Text, nullable=False)
    nonce = Column(String, nullable=False)
    sender_device_id = Column(UUID(as_uuid=True), nullable=False)
    receiver_device_id = Column(UUID(as_uuid=True), nullable=False)
    ephemeral_pub = Column(Text, nullable=True)
    signed_prekey_id = Column(Integer, nullable=True)
    one_time_prekey_id = Column(Integer, nullable=True)
    message_type = Column(String, default="text")
    client_msg_id = Column(String, nullable=True)
    
    # Updated to ensure Python handles the UTC default correctly
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        # We ensure the ISO format includes the 'Z' (Zulu/UTC) suffix
        # This tells React: "This time is UTC, please convert to local"
        iso_time = None
        if self.created_at:
            iso_time = self.created_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
            
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
            "created_at": iso_time,
        }

Index("ix_messages_client_msg_id", Message.client_msg_id)