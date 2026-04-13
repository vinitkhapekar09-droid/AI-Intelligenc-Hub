from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from ..core.database import get_db
from ..models.subscriber import Subscriber
from ..rag.vector_store import get_collection_stats


router = APIRouter()


class SubscribeRequest(BaseModel):
    email: EmailStr


@router.get("/health")
def health_check():
    return {"status": "healthy"}


@router.post("/subscribe")
def subscribe(request: SubscribeRequest, db: Session = Depends(get_db)):
    existing = db.query(Subscriber).filter(Subscriber.email == request.email).first()
    if existing:
        if existing.is_active:
            raise HTTPException(status_code=400, detail="Email already subscribed")
        else:
            existing.is_active = True
            db.commit()
            return {"message": "Welcome back! Subscription reactivated."}
    subscriber = Subscriber(email=request.email)
    db.add(subscriber)
    db.commit()
    return {"message": "Successfully subscribed to Daily AI Digest!"}


@router.delete("/unsubscribe")
def unsubscribe(email: EmailStr, db: Session = Depends(get_db)):
    subscriber = db.query(Subscriber).filter(Subscriber.email == email).first()
    if not subscriber or not subscriber.is_active:
        raise HTTPException(status_code=404, detail="Email not found")
    subscriber.is_active = False
    db.commit()
    return {"message": "You have been unsubscribed from Daily AI Digest."}


@router.post("/trigger-digest")
def trigger_digest():
    from ..tasks.digest_tasks import run_daily_digest

    task = run_daily_digest.delay()
    return {"message": "Daily digest task triggered", "task_id": task.id}


# --- NEW: Chat and Digest endpoints ---


class ChatRequest(BaseModel):
    question: str
    doc_type: str = None  # Optional: "news", "research", or None for both
    n_results: int = 5  # How many chunks to retrieve


@router.post("/chat")
def chat(request: ChatRequest):
    """
    RAG-based chat endpoint.
    User asks a question, gets an answer grounded in ingested AI/ML content.

    WHY lazy import for chat_agent?
    chat_agent loads the sentence-transformers model at import time (~2s).
    Lazy importing means this only happens when /chat is first called,
    not at app startup — keeping startup time fast.
    """
    from ..agents.chat_agent import ask

    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    result = ask(
        question=request.question,
        n_results=request.n_results,
        doc_type=request.doc_type,
    )
    return result


@router.get("/daily-digest")
def get_daily_digest():
    """
    Returns the latest summarized digest items and vector store stats.
    WHY this endpoint? Useful for a frontend dashboard or status check
    without triggering a full pipeline run.
    """
    stats = get_collection_stats()
    return {
        "status": "ok",
        "vector_store": stats,
        "message": "Use POST /trigger-digest to run the full pipeline",
    }
