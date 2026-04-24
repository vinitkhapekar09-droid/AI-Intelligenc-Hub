# tasks/digest_tasks.py
#
# WHY THIS FILE EXISTS:
# This is the Celery task that orchestrates the entire daily pipeline.
# It runs on a schedule (7AM IST via Celery Beat) and ties together
# all services: fetching, normalizing, summarizing, emailing,
# and RAG ingestion.
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
from ..services.task_run_service import finish_task_run, start_task_run
from sqlalchemy.exc import SQLAlchemyError

# RAG pipeline imports
from ..pipeline.normalizer import normalize_all
from ..rag.chunker import chunk_all_documents
from ..rag.embedder import embed_chunks
from ..rag.vector_store import store_chunks


@celery_app.task(name="app.tasks.digest_tasks.run_daily_digest")
def run_daily_digest():
    print("[task] Starting daily digest pipeline...")
    issue_date = datetime.now(timezone.utc).date()
    task_db = SessionLocal()
    task_run = start_task_run(
        task_db,
        task_name="daily_digest",
        issue_date=issue_date.isoformat(),
        task_id=getattr(run_daily_digest.request, "id", None),
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
        # WHY here? Summarizer and RAG pipeline both need clean, typed data.
        # We normalize once and reuse the result for both.
        # ----------------------------------------------------------------
        documents = normalize_all(raw_items)

        # ----------------------------------------------------------------
        # STEP 3: Summarize with Gemini (existing behavior, unchanged)
        # summarize_items() still expects raw dicts, so we pass raw_items.
        # WHY not pass documents? To avoid breaking the existing summarizer.
        # We'll refactor summarizer in Phase 2.
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
        # STEP 4: Send digest emails to all active subscribers
        # This is the critical path — must happen before RAG ingestion.
        # ----------------------------------------------------------------
        db = SessionLocal()
        try:
            subscribers = db.query(Subscriber).filter(Subscriber.is_active.is_(True)).all()
            emails = [s.email for s in subscribers]
        except SQLAlchemyError as e:
            # Local/manual runs may not have Postgres running;
            # don't fail the whole digest.
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
        # STEP 5: RAG ingestion — runs AFTER email so failures don't
        # affect subscribers. Wrapped in try/except so a RAG failure
        # never causes the task to report as failed.
        # ----------------------------------------------------------------
        rag_result = _ingest_into_rag(documents, issue_date.isoformat())

        print("[task] Pipeline complete.")
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
        _record_task_finish(task_run.id, "failed", result)
        raise


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

    WHY a private function (underscore prefix)?
    It's an implementation detail of the task — not meant to be
    called directly from outside this module.
    """
    try:
        print("[task] Starting RAG ingestion...")

        # Chunk all documents
        chunks = chunk_all_documents(documents)
        if not chunks:
            return {"status": "skipped", "reason": "no chunks produced"}

        # Generate embeddings
        embedded = embed_chunks(chunks)
        for item in embedded:
            item["metadata"]["issue_date"] = issue_date

        # Store in SQL-backed RAG chunk store
        stored_count = store_chunks(embedded)

        print(f"[task] RAG ingestion complete: {stored_count} chunks stored.")
        return {
            "status": "success",
            "chunks_stored": stored_count,
        }

    except Exception as e:
        # Never let RAG failure crash the task
        print(f"[task] RAG ingestion failed (non-critical): {e}")
        return {"status": "failed", "error": str(e)}
