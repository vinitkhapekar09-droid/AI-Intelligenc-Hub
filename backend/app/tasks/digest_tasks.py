# tasks/digest_tasks.py
#
# WHY THIS FILE EXISTS:
# This module orchestrates the daily digest pipeline and exposes a Celery
# wrapper for the current deployment. The core pipeline is also a plain
# Python function so it can be reused by a serverless runtime without Celery.
#
# DESIGN PRINCIPLE: Each step is independent.
# If RAG ingestion fails, the email was already sent
# and subscribers are unaffected.
# If summarization fails, we abort early and log it — no partial emails sent.

from datetime import datetime, timezone

from ..core.celery_app import celery_app
from ..core.database import SessionLocal
from ..models.subscriber import Subscriber
from ..services.fetcher import fetch_all_items
from ..services.summarizer import summarize_items
from ..services.digest_store import store_daily_issue
from ..services.email_sender import send_digest_to_all
from ..services.telegram_notifier import send_telegram_message
from ..services.task_run_service import finish_task_run, start_task_run
from sqlalchemy.exc import SQLAlchemyError

# RAG pipeline imports
from ..pipeline.normalizer import normalize_all
from ..rag.chunker import chunk_all_documents
from ..rag.embedder import embed_chunks
from ..rag.vector_store import store_chunks


def run_daily_digest_pipeline(task_id=None):
    """Run the digest pipeline without requiring a Celery task context."""
    print("[task] Starting daily digest pipeline...")
    issue_date = datetime.now(timezone.utc).date()
    task_db = SessionLocal()
    task_run = start_task_run(
        task_db,
        task_name="daily_digest",
        issue_date=issue_date.isoformat(),
        task_id=task_id,
    )
    task_db.close()

    try:
        # ----------------------------------------------------------------
        # STEP 1: Fetch raw items from NewsAPI + arXiv
        # ----------------------------------------------------------------
        raw_items = fetch_all_items()
        if not raw_items:
            print("[task] No items fetched. Aborting.")
            result = {"status": "aborted", "reason": "no items fetched"}
            _record_task_finish(task_run.id, "aborted", result)
            return result

        # ----------------------------------------------------------------
        # STEP 2: Normalize into UnifiedDocument schema
        # ----------------------------------------------------------------
        documents = normalize_all(raw_items)

        # ----------------------------------------------------------------
        # STEP 3: Summarize the fetched items
        # ----------------------------------------------------------------
        summaries = summarize_items(raw_items)
        if not summaries:
            print("[task] Summarization failed. Aborting.")
            result = {"status": "aborted", "reason": "summarization failed"}
            _record_task_finish(task_run.id, "aborted", result)
            return result

        db = SessionLocal()
        try:
            persisted_issue = store_daily_issue(db, issue_date, documents, summaries)
        finally:
            db.close()

        # ----------------------------------------------------------------
        # STEP 4: Send digest emails before RAG ingestion
        # ----------------------------------------------------------------
        db = SessionLocal()
        try:
            subscribers = db.query(Subscriber).filter(Subscriber.is_active.is_(True)).all()
            emails = [s.email for s in subscribers]
        except SQLAlchemyError as e:
            print(f"[task] Subscriber lookup failed; skipping email send: {e}")
            emails = []
        finally:
            db.close()

        if not emails:
            print("[task] No active subscribers.")
            email_results = {"sent": 0}
        else:
            email_results = send_digest_to_all(
                summaries,
                emails,
                issue_date=issue_date.isoformat(),
            )
            print(f"[task] Email results: {email_results}")

        # ----------------------------------------------------------------
        # STEP 5: RAG ingestion is non-critical
        # ----------------------------------------------------------------
        rag_result = _ingest_into_rag(documents, issue_date.isoformat())

        print("[task] Pipeline complete.")
        send_telegram_message(
            f"Daily digest completed:\nDate: {issue_date.isoformat()}\nSubscribers emailed: {len(emails)}\nRAG status: {rag_result.get('status')}"
        )
        result = {
            "status": "done",
            "documents_fetched": len(raw_items),
            "issue_date": issue_date.isoformat(),
            "issue_id": persisted_issue["id"],
            "emails": email_results,
            "rag": rag_result,
        }
        _record_task_finish(task_run.id, "success", result)
        return result
    except Exception as exc:
        result = {"status": "failed", "error": str(exc), "issue_date": issue_date.isoformat()}
        send_telegram_message(
            f"Daily digest failed:\nDate: {issue_date.isoformat()}\nError: {exc}"
        )
        _record_task_finish(task_run.id, "failed", result)
        raise


@celery_app.task(name="app.tasks.digest_tasks.run_daily_digest")
def run_daily_digest():
    """Celery entry point retained for the existing EC2 deployment."""
    task_id = getattr(run_daily_digest.request, "id", None)
    return run_daily_digest_pipeline(task_id=task_id)


def _record_task_finish(task_run_id: int, status: str, detail: dict) -> None:
    db = SessionLocal()
    try:
        finish_task_run(db, task_run_id, status=status, detail=detail)
    finally:
        db.close()


def _ingest_into_rag(documents, issue_date: str) -> dict:
    """
    Chunks, embeds, and stores documents in the vector store.
    Separated into its own function for clarity and testability.
    """
    try:
        print("[task] Starting RAG ingestion...")
        chunks = chunk_all_documents(documents)
        if not chunks:
            return {"status": "skipped", "reason": "no chunks produced"}

        embedded = embed_chunks(chunks)
        for item in embedded:
            item["metadata"]["issue_date"] = issue_date

        stored_count = store_chunks(embedded)
        print(f"[task] RAG ingestion complete: {stored_count} chunks stored.")
        return {"status": "success", "chunks_stored": stored_count}

    except Exception as e:
        print(f"[task] RAG ingestion failed (non-critical): {e}")
        return {"status": "failed", "error": str(e)}
