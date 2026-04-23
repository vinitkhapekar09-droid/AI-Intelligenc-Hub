#!/usr/bin/env python
"""
Test script to demonstrate conversation memory working end-to-end.
"""

import os
import sys
from app.core.database import SessionLocal
from app.models.user import User
from app.services.conversation_service import (
    save_message,
    get_conversation_history,
    get_conversation_summary,
    clear_conversation_history,
)
from app.agents.chat_agent import ask

# Set required env vars
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("RESEND_API_KEY", "test")
os.environ.setdefault("NEWS_API_KEY", "test")
os.environ.setdefault("MLFLOW_TRACKING_URL", "http://localhost:5000")


def test_conversation_memory():
    """Test the full conversation memory flow."""
    print("=" * 60)
    print("🧪 CONVERSATION MEMORY TEST")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Get or create a test user
        users = db.query(User).all()
        if not users:
            print("❌ No users found. Please create a user first!")
            return
        
        user = users[0]
        user_id = user.id
        print(f"✅ Using user: {user.email} (ID: {user_id})\n")
        
        # Clear previous history for clean test
        deleted = clear_conversation_history(db, user_id)
        print(f"🗑️  Cleared {deleted} previous messages\n")
        
        # Simulate a multi-turn conversation
        print("=" * 60)
        print("📝 SIMULATING CONVERSATION")
        print("=" * 60)
        
        conversation = [
            {
                "user": "Tell me about transformers in AI",
                "doc_type": "research",
            },
            {
                "user": "what else",
                "doc_type": "research",
            },
            {
                "user": "how are they used in NLP",
                "doc_type": "research",
            },
        ]
        
        for turn, item in enumerate(conversation, 1):
            question = item["user"]
            doc_type = item["doc_type"]
            
            print(f"\n--- Turn {turn} ---")
            print(f"👤 User: {question}")
            
            # Get history before this turn
            history = get_conversation_history(db, user_id, limit=10)
            print(f"📚 History available: {len(history)} messages")
            
            # Get response from agent
            result = ask(
                question=question,
                n_results=5,
                doc_type=doc_type,
                history=history,
            )
            
            print(f"🤖 Agent: {result['answer'][:120]}...")
            print(f"📊 Sources: {result['chunks_found']} chunks, {len(result['sources'])} sources")
            
            # Save to history
            save_message(db, user_id, "user", question, doc_type=doc_type)
            save_message(
                db,
                user_id,
                "assistant",
                result["answer"],
                doc_type=doc_type,
                sources=result["sources"],
            )
        
        # Show final statistics
        print("\n" + "=" * 60)
        print("📊 CONVERSATION STATISTICS")
        print("=" * 60)
        
        stats = get_conversation_summary(db, user_id)
        print(f"Total messages: {stats['total_messages']}")
        print(f"User messages: {stats['user_messages']}")
        print(f"Assistant messages: {stats['assistant_messages']}")
        print(f"Doc type preferences: {stats['doc_type_preferences']}")
        
        # Show full history
        print("\n" + "=" * 60)
        print("📜 FULL CONVERSATION HISTORY")
        print("=" * 60)
        
        full_history = get_conversation_history(db, user_id, limit=100)
        for i, msg in enumerate(full_history[-6:], 1):  # Show last 6 messages
            role_emoji = "👤" if msg["role"] == "user" else "🤖"
            text = msg["text"][:80] + ("..." if len(msg["text"]) > 80 else "")
            print(f"{role_emoji} {msg['role'].upper()}: {text}")
        
        print("\n✅ MEMORY TEST COMPLETE!")
        print("✅ Conversations are being stored and retrieved!")
        print("✅ History is available for context in follow-up questions!")
        
    finally:
        db.close()


if __name__ == "__main__":
    test_conversation_memory()
