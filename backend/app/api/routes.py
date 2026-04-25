from datetime import date
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel, EmailStr
from typing import List, Literal, Optional
from ..core.database import get_db
from ..core.config import settings
from ..models.subscriber import Subscriber
from ..rag.vector_store import get_collection_stats
from ..models.content_item import ContentItem
from ..models.daily_issue import DailyIssue
from ..models.user import User
from ..services.digest_store import (
    get_issue_by_date,
    get_latest_issue,
    list_feed_items,
    list_recent_issues,
)
from ..services.task_run_service import get_latest_task_run
from ..core.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)
from fastapi import status


router = APIRouter()


def verify_trigger_digest_token(x_trigger_token: str | None = Header(default=None)):
    expected_token = settings.TRIGGER_DIGEST_TOKEN.strip()

    if not expected_token:
        if settings.ENVIRONMENT.lower() == "production":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Digest trigger token is not configured",
            )
        return

    if x_trigger_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid trigger token",
        )


class SubscribeRequest(BaseModel):
    email: EmailStr


class RegisterRequest(BaseModel):
    """Request body for user registration."""

    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    """Request body for user login."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str
    user_name: str


@router.get("/health")
def health_check():
    return {"status": "healthy"}


@router.get("/health/details")
def health_details(db: Session = Depends(get_db)):
    database = {"status": "unknown"}
    try:
        db.execute(text("SELECT 1"))
        database = {"status": "ok"}
    except Exception as exc:
        database = {"status": "error", "detail": str(exc)}

    latest_issue = db.query(DailyIssue).order_by(DailyIssue.issue_date.desc()).first()
    issue_count = db.query(DailyIssue).count()
    content_count = db.query(ContentItem).count()
    task_run = get_latest_task_run(db, "daily_digest")
    vector_stats = get_collection_stats(db)

    overall_status = "ok" if database["status"] == "ok" else "degraded"

    return {
        "status": overall_status,
        "database": database,
        "feed": {
            "issue_count": issue_count,
            "content_item_count": content_count,
            "latest_issue_date": latest_issue.issue_date.isoformat()
            if latest_issue
            else None,
        },
        "rag": vector_stats,
        "scheduler": {
            "last_daily_digest_run": (
                {
                    "status": task_run.status,
                    "started_at": task_run.started_at.isoformat()
                    if task_run.started_at
                    else None,
                    "finished_at": task_run.finished_at.isoformat()
                    if task_run.finished_at
                    else None,
                    "issue_date": task_run.issue_date,
                    "detail": task_run.detail,
                }
                if task_run
                else None
            )
        },
    }


@router.post("/register", response_model=TokenResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user account.

    Args:
        request: RegisterRequest with name, email, password
        db: Database session

    Returns:
        TokenResponse with JWT token, token type, and user name

    Raises:
        HTTPException 400: If email already exists
        HTTPException 503: If database is unavailable
    """
    try:
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Create new user with hashed password
        hashed_pwd = hash_password(request.password)
        new_user = User(
            name=request.name,
            email=request.email,
            hashed_password=hashed_pwd,
            is_active=True,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Generate JWT token
        access_token = create_access_token(data={"sub": new_user.email})

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_name=new_user.name,
        )
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database unavailable. Error: {e}",
        )


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Login an existing user and return JWT token.

    Args:
        request: LoginRequest with email and password
        db: Database session

    Returns:
        TokenResponse with JWT token, token type, and user name

    Raises:
        HTTPException 401: If email not found or password incorrect
        HTTPException 503: If database is unavailable
    """
    try:
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        if not verify_password(request.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive",
            )

        # Generate JWT token
        access_token = create_access_token(data={"sub": user.email})

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_name=user.name,
        )
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database unavailable. Error: {e}",
        )


@router.post("/subscribe")
def subscribe(request: SubscribeRequest, db: Session = Depends(get_db)):
    try:
        existing = (
            db.query(Subscriber).filter(Subscriber.email == request.email).first()
        )
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
        return {"message": "Successfully subscribed to AI Intelligence Hub updates!"}
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Database unavailable. Start PostgreSQL or update DATABASE_URL. Error: {e}",
        )


@router.delete("/unsubscribe")
def unsubscribe(email: EmailStr, db: Session = Depends(get_db)):
    try:
        subscriber = db.query(Subscriber).filter(Subscriber.email == email).first()
        if not subscriber or not subscriber.is_active:
            raise HTTPException(status_code=404, detail="Email not found")
        subscriber.is_active = False
        db.commit()
        return {
            "message": "You have been unsubscribed from AI Intelligence Hub updates."
        }
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Database unavailable. Start PostgreSQL or update DATABASE_URL. Error: {e}",
        )


@router.post("/trigger-digest")
def trigger_digest(_verified: None = Depends(verify_trigger_digest_token)):
    from ..tasks.digest_tasks import run_daily_digest

    try:
        # Manual trigger does not need result backend subscriptions.
        task = run_daily_digest.apply_async(ignore_result=True)
        return {"message": "Daily digest task triggered", "task_id": task.id}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=(
                "Could not enqueue digest task. Ensure Redis/Celery services are running. "
                f"Error: {e}"
            ),
        )


# --- NEW: Chat and Digest endpoints ---


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    text: str


class ChatRequest(BaseModel):
    question: str
    doc_type: Optional[str] = None  # Optional: "news", "research", or None for both
    n_results: int = 5  # How many chunks to retrieve
    thread_id: Optional[str] = None
    issue_date: Optional[str] = None
    history: List[ChatMessage] = []


def _parse_issue_date(raw_value: Optional[str]) -> date | None:
    if not raw_value:
        return None

    try:
        return date.fromisoformat(raw_value)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="issue_date must use YYYY-MM-DD format",
        ) from exc


@router.post("/chat")
def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    RAG-based chat endpoint with persistent memory.
    User asks a question, gets an answer grounded in ingested AI/ML content.
    Conversation is saved to database for future context.

    This endpoint requires valid JWT authentication.
    Include Authorization: Bearer <token> header.

    Features:
    - Persistent conversation memory (no more context loss on reload!)
    - Multi-turn conversation support
    - Answer grounded in retrieval-augmented generation
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    from ..agents.chat_agent import ask
    from ..services.conversation_service import (
        save_message,
        get_conversation_history,
    )

    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    effective_thread_id = request.thread_id or str(uuid4())

    # Load conversation history from database for context
    saved_history = get_conversation_history(
        db,
        current_user.id,
        limit=100,
        thread_id=effective_thread_id,
    )
    print(
        f"[chat] Loaded {len(saved_history)} messages from history for user {current_user.id}"
    )

    # Format history for the chat agent
    history_for_agent = saved_history if saved_history else None

    # Get the answer from the chat agent
    result = ask(
        question=request.question,
        n_results=request.n_results,
        doc_type=request.doc_type,
        history=history_for_agent,
        issue_date=request.issue_date,
    )
    print(
        f"[chat] Agent found {result['chunks_found']} chunks, used {len(result['sources'])} sources"
    )

    # Save user message to conversation history
    try:
        save_message(
            db,
            user_id=current_user.id,
            role="user",
            message=request.question,
            doc_type=request.doc_type,
            thread_id=effective_thread_id,
        )

        # Save assistant response to conversation history
        save_message(
            db,
            user_id=current_user.id,
            role="assistant",
            message=result["answer"],
            doc_type=request.doc_type,
            sources=result["sources"],
            thread_id=effective_thread_id,
        )
    except Exception as e:
        print(f"[chat] Failed to save conversation history: {e}")
        # Don't fail the response if history saving fails

    return {
        **result,
        "thread_id": effective_thread_id,
    }


@router.get("/chat/threads")
def get_chat_threads(
    limit: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    from ..services.conversation_service import list_conversation_threads

    try:
        threads = list_conversation_threads(
            db,
            current_user.id,
            limit=min(max(limit, 1), 100),
        )
        return {
            "status": "ok",
            "threads": threads,
        }
    except Exception as e:
        print(f"[chat/threads] Failed to retrieve threads: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve chat threads",
        )


@router.get("/chat/history")
def get_chat_history(
    limit: int = 20,
    thread_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get the user's conversation history for memory/context.

    Args:
        limit: Maximum number of messages to retrieve (default 20)

    Returns:
        List of conversation messages with timestamps and sources
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    from ..services.conversation_service import get_conversation_history

    try:
        history = get_conversation_history(
            db,
            current_user.id,
            limit=limit,
            thread_id=thread_id,
        )
        return {
            "status": "ok",
            "message_count": len(history),
            "messages": history,
        }
    except Exception as e:
        print(f"[chat/history] Failed to retrieve history: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve conversation history",
        )


@router.delete("/chat/history")
def clear_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Clear all conversation history for the current user.
    This allows users to start fresh if desired.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    from ..services.conversation_service import clear_conversation_history

    try:
        deleted_count = clear_conversation_history(db, current_user.id)
        return {
            "status": "ok",
            "message": f"Cleared {deleted_count} messages from conversation history",
            "deleted_count": deleted_count,
        }
    except Exception as e:
        print(f"[chat/history] Failed to clear history: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to clear conversation history",
        )


@router.delete("/chat/threads/{thread_id}")
def delete_chat_thread(
    thread_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    from ..services.conversation_service import clear_conversation_history

    try:
        deleted_count = clear_conversation_history(
            db,
            current_user.id,
            thread_id=thread_id,
        )
        if deleted_count == 0:
            raise HTTPException(status_code=404, detail="Thread not found")

        return {
            "status": "ok",
            "message": f"Deleted {deleted_count} messages from thread",
            "deleted_count": deleted_count,
            "thread_id": thread_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[chat/thread-delete] Failed to delete thread: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete chat thread",
        )


@router.get("/chat/stats")
def get_chat_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get statistics about the user's conversations.
    Shows message counts, preferences, and insights.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    from ..services.conversation_service import get_conversation_summary

    try:
        stats = get_conversation_summary(db, current_user.id)
        return {
            "status": "ok",
            "stats": stats,
        }
    except Exception as e:
        print(f"[chat/stats] Failed to retrieve stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve conversation stats",
        )


@router.get("/daily-digest")
def get_daily_digest(
    issue_date: Optional[str] = None,
    db: Session = Depends(get_db),
):
    parsed_issue_date = _parse_issue_date(issue_date)
    issue = (
        get_issue_by_date(db, parsed_issue_date)
        if parsed_issue_date
        else get_latest_issue(db)
    )

    stats = get_collection_stats(db)
    if issue is None:
        return {
            "status": "ok",
            "issue": None,
            "items": [],
            "vector_store": stats,
        }

    return {
        "status": "ok",
        "issue": issue,
        "items": issue["items"],
        "vector_store": stats,
    }


@router.get("/issues")
def get_issues(
    limit: int = 7,
    db: Session = Depends(get_db),
):
    issues = list_recent_issues(db, limit=min(max(limit, 1), 30))
    return {
        "status": "ok",
        "issues": issues,
    }


@router.get("/issues/{issue_date}")
def get_issue(
    issue_date: str,
    db: Session = Depends(get_db),
):
    parsed_issue_date = _parse_issue_date(issue_date)
    issue = get_issue_by_date(db, parsed_issue_date)
    if issue is None:
        raise HTTPException(status_code=404, detail="Issue not found")

    return {
        "status": "ok",
        "issue": issue,
    }


@router.get("/feed")
def get_feed(
    limit: int = 30,
    issue_date: Optional[str] = None,
    doc_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    parsed_issue_date = _parse_issue_date(issue_date)
    items = list_feed_items(
        db,
        limit=min(max(limit, 1), 100),
        issue_date=parsed_issue_date,
        doc_type=doc_type,
    )
    return {
        "status": "ok",
        "items": items,
    }
