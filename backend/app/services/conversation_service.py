"""Service for managing conversation history and memory."""

import json
from datetime import datetime
from sqlalchemy.orm import Session
from ..models.conversation import Conversation
from ..models.user import User


def save_message(
    db: Session,
    user_id: int,
    role: str,
    message: str,
    doc_type: str | None = None,
    sources: list | None = None,
) -> Conversation:
    """
    Save a message to the conversation history.
    
    Args:
        db: Database session
        user_id: User ID
        role: "user" or "assistant"
        message: The message content
        doc_type: Optional document type filter used
        sources: Optional list of sources used in response
    
    Returns:
        Saved Conversation object
    """
    sources_json = json.dumps(sources) if sources else None
    
    conversation = Conversation(
        user_id=user_id,
        role=role,
        message=message,
        doc_type=doc_type,
        sources_used=sources_json,
    )
    
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    return conversation


def get_conversation_history(
    db: Session,
    user_id: int,
    limit: int = 20,
) -> list[dict]:
    """
    Get the most recent conversation history for a user.
    
    Args:
        db: Database session
        user_id: User ID
        limit: Maximum number of messages to return
    
    Returns:
        List of conversation messages in chronological order
    """
    messages = db.query(Conversation).filter(
        Conversation.user_id == user_id
    ).order_by(
        Conversation.created_at.desc()
    ).limit(limit).all()
    
    # Reverse to get chronological order (oldest first)
    messages.reverse()
    
    return [
        {
            "role": msg.role,
            "text": msg.message,
            "timestamp": msg.created_at.isoformat(),
            "doc_type": msg.doc_type,
            "sources": json.loads(msg.sources_used) if msg.sources_used else [],
        }
        for msg in messages
    ]


def clear_conversation_history(db: Session, user_id: int) -> int:
    """
    Clear all conversation history for a user.
    
    Args:
        db: Database session
        user_id: User ID
    
    Returns:
        Number of messages deleted
    """
    count = db.query(Conversation).filter(
        Conversation.user_id == user_id
    ).delete()
    
    db.commit()
    return count


def get_conversation_summary(
    db: Session,
    user_id: int,
) -> dict:
    """
    Get statistics about a user's conversation history.
    """
    total_messages = db.query(Conversation).filter(
        Conversation.user_id == user_id
    ).count()
    
    user_messages = db.query(Conversation).filter(
        Conversation.user_id == user_id,
        Conversation.role == "user",
    ).count()
    
    assistant_messages = total_messages - user_messages
    
    # Get most common doc types
    doc_types = db.query(Conversation.doc_type).filter(
        Conversation.user_id == user_id,
        Conversation.role == "user",
    ).all()
    
    doc_type_counts = {}
    for (dt,) in doc_types:
        if dt:
            doc_type_counts[dt] = doc_type_counts.get(dt, 0) + 1
    
    return {
        "total_messages": total_messages,
        "user_messages": user_messages,
        "assistant_messages": assistant_messages,
        "doc_type_preferences": doc_type_counts,
    }
