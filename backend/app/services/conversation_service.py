"""Service for managing conversation history and memory."""

import json
from collections import OrderedDict
from sqlalchemy.orm import Session
from ..models.conversation import Conversation


def save_message(
    db: Session,
    user_id: int,
    role: str,
    message: str,
    doc_type: str | None = None,
    sources: list | None = None,
    thread_id: str | None = None,
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
        thread_id=thread_id,
    )
    
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    return conversation


def get_conversation_history(
    db: Session,
    user_id: int,
    limit: int = 20,
    thread_id: str | None = None,
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
    query = db.query(Conversation).filter(Conversation.user_id == user_id)

    if thread_id:
        query = query.filter(Conversation.thread_id == thread_id)

    messages = query.order_by(
        Conversation.created_at.desc()
    ).limit(limit).all()
    
    # Reverse to get chronological order (oldest first)
    messages.reverse()
    
    return [
        {
            "id": msg.id,
            "role": msg.role,
            "text": msg.message,
            "timestamp": msg.created_at.isoformat(),
            "doc_type": msg.doc_type,
            "sources": json.loads(msg.sources_used) if msg.sources_used else [],
            "thread_id": msg.thread_id,
        }
        for msg in messages
    ]


def clear_conversation_history(
    db: Session,
    user_id: int,
    thread_id: str | None = None,
) -> int:
    """
    Clear all conversation history for a user.
    
    Args:
        db: Database session
        user_id: User ID
    
    Returns:
        Number of messages deleted
    """
    query = db.query(Conversation).filter(Conversation.user_id == user_id)
    if thread_id is not None:
        query = query.filter(Conversation.thread_id == thread_id)

    count = query.delete()
    
    db.commit()
    return count


def list_conversation_threads(
    db: Session,
    user_id: int,
    limit: int = 30,
) -> list[dict]:
    """
    Return recent conversation threads for sidebar-style navigation.

    We build summaries in Python so the logic stays database-portable
    across SQLite and Postgres without maintaining separate SQL.
    """
    messages = (
        db.query(Conversation)
        .filter(
            Conversation.user_id == user_id,
            Conversation.thread_id.isnot(None),
        )
        .order_by(Conversation.created_at.desc(), Conversation.id.desc())
        .all()
    )

    thread_map: OrderedDict[str, dict] = OrderedDict()
    for message in messages:
        thread_id = message.thread_id
        if not thread_id:
            continue

        thread = thread_map.get(thread_id)
        if thread is None:
            thread = {
                "thread_id": thread_id,
                "title": "New chat",
                "last_message": message.message[:140],
                "updated_at": message.created_at.isoformat(),
                "message_count": 0,
            }
            thread_map[thread_id] = thread

        thread["message_count"] += 1

        if (
            thread["title"] == "New chat"
            and message.role == "user"
            and message.message.strip()
        ):
            thread["title"] = message.message.strip()[:60]

    return list(thread_map.values())[:limit]


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
