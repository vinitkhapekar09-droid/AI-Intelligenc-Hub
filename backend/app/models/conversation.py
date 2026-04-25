from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from ..core.database import Base


class Conversation(Base):
    """Stores chat conversations per user for persistent memory."""

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Message content
    role = Column(String, nullable=False)  # "user" or "assistant"
    message = Column(Text, nullable=False)

    # Metadata for retrieval
    doc_type = Column(String, nullable=True)  # "news", "research", or None
    sources_used = Column(Text, nullable=True)  # JSON string of sources

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # For grouping related messages into conversation threads
    thread_id = Column(String, nullable=True, index=True)  # Optional: group messages
    is_pinned = Column(Boolean, default=False)  # Allow users to pin important conversations
