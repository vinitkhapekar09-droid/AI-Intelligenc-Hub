from ..core.celery_app import celery_app
from ..core.database import SessionLocal
from ..models.subscriber import Subscriber
from ..services.fetcher import fetch_all_items
from ..services.summarizer import summarize_items
from ..services.email_sender import send_digest_to_all


@celery_app.task(name="app.tasks.digest_task.run_daily_digest")
def run_daily_digest():
    print("[task] Starting daily digest pipeline...")

    # Step 1: Fetch news
    items = fetch_all_items()
    if not items:
        print("[task] No items fetched. Aborting.")
        return {"status": "aborted", "reason": "no items fetched"}

    # Step 2: Summarize with Gemini
    summaries = summarize_items(items)
    if not summaries:
        print("[task] Summarization failed. Aborting.")
        return {"status": "aborted", "reason": "summarization failed"}

    # Step 3: Get all active subscribers from DB
    db = SessionLocal()
    try:
        subscribers = db.query(Subscriber).filter(Subscriber.is_active.is_(True)).all()
        emails = [s.email for s in subscribers]
    finally:
        db.close()

    if not emails:
        print("[task] No active subscribers.")
        return {"status": "done", "sent": 0}

    # Step 4: Send emails
    results = send_digest_to_all(summaries, emails)

    print(f"[task] Digest complete: {results}")
    return {"status": "done", **results}
